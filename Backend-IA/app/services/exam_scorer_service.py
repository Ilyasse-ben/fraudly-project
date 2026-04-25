"""
Exam Scorer Service - scoring des questions ouvertes via LLM.

Pipeline:
1. Ecoute le topic 'exam.correction.requested'
2. Pour chaque reponse ouverte du batch
3. LLM evalue la reponse selon la rubrique fournie
4. Publie le resultat sur 'exam.scored'
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from kafka import KafkaConsumer
from kafka.errors import KafkaError

from app.core.config import settings
from app.core.logger import get_logger
from app.kafka.producer import publish_event
from app.services.llm_router import invoke_with_fallback

logger = get_logger(__name__)


@dataclass
class ScoreResult:
    score: float
    max_score: float
    feedback: str
    rubric_justification: str
    provider: str
    fallback_used: bool


class ExamScorerConsumer:
    """Consumer Kafka pour scorer les reponses ouvertes d'examen."""

    def __init__(self):
        self._consumer: Optional[KafkaConsumer] = None
        self._running = False

    def start(self) -> bool:
        if not settings.KAFKA_ENABLED:
            logger.info("[ExamScorer] Kafka desactive, consumer non lance")
            return False

        try:
            self._consumer = KafkaConsumer(
                settings.KAFKA_TOPIC_EXAM_CORRECTION_REQUESTED,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id=f"{settings.KAFKA_GROUP_ID}-exam-scorer",
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                max_poll_records=10,
                session_timeout_ms=30000,
            )
            self._running = True
            logger.info(
                "[ExamScorer] Consumer pret topic=%s group=%s",
                settings.KAFKA_TOPIC_EXAM_CORRECTION_REQUESTED,
                f"{settings.KAFKA_GROUP_ID}-exam-scorer",
            )
            return True
        except Exception as e:
            logger.error(f"[ExamScorer] Erreur initialisation consumer: {e}")
            self._running = False
            return False

    def stop(self) -> None:
        self._running = False
        if self._consumer is not None:
            try:
                self._consumer.close()
                logger.info("[ExamScorer] Consumer arrete")
            except Exception as e:
                logger.error(f"[ExamScorer] Erreur fermeture consumer: {e}")
            finally:
                self._consumer = None

    def poll_once(self) -> None:
        if not self._running or self._consumer is None:
            return

        try:
            messages = self._consumer.poll(timeout_ms=1000, max_records=10)
            if not messages:
                return

            for _tp, records in messages.items():
                for record in records:
                    self._handle_event(record.value)
        except KafkaError as e:
            logger.error(f"[ExamScorer] Kafka poll error: {e}")
        except Exception as e:
            logger.error(f"[ExamScorer] Erreur traitement poll: {e}")

    def _handle_event(self, event: Dict[str, Any]) -> None:
        """
        Format attendu (exam.correction.requested):
        {
          "exam_id": "uuid",
          "course_id": "uuid",
          "requested_at": "iso-string",
          "submissions": [
            {
              "student_id": "uuid",
              "student_name": "string",
              "open_answers": [
                {
                  "question_id": "uuid",
                  "student_answer": "texte",
                  "correct_answer": "reponse attendue",
                  "explanation": "justification attendue",
                  "max_score": 20
                }
              ]
            }
          ]
        }
        """
        exam_id = event.get("exam_id")
        submissions = event.get("submissions", [])
        requested_at = event.get("requested_at")

        if not exam_id:
            logger.warning("[ExamScorer] Message incomplet: exam_id manquant")
            return

        if not isinstance(submissions, list) or not submissions:
            logger.info("[ExamScorer] Aucun submissions a scorer pour exam=%s", exam_id)
            return

        published = 0
        for submission in submissions:
            if not isinstance(submission, dict):
                continue

            student_id = submission.get("student_id")
            student_name = submission.get("student_name")
            open_answers = submission.get("open_answers", [])

            if not student_id:
                logger.warning(
                    "[ExamScorer] Submission ignoree exam=%s: student_id manquant",
                    exam_id,
                )
                continue

            if not isinstance(open_answers, list) or not open_answers:
                logger.info(
                    "[ExamScorer] Aucune open_answer a scorer pour exam=%s student=%s",
                    exam_id,
                    student_id,
                )
                continue

            for answer in open_answers:
                if not isinstance(answer, dict):
                    continue

                question_id = answer.get("question_id")
                student_answer = answer.get("student_answer") or answer.get("answer_text")
                correct_answer = answer.get("correct_answer")
                explanation = answer.get("explanation")
                max_score = float(answer.get("max_score", 20))

                required = {
                    "question_id": question_id,
                    "student_answer": student_answer,
                    "correct_answer": correct_answer,
                    "explanation": explanation,
                }
                missing = [k for k, v in required.items() if v in (None, "")]
                if missing:
                    logger.warning(
                        "[ExamScorer] Reponse ignoree exam=%s student=%s (champs manquants: %s)",
                        exam_id,
                        student_id,
                        missing,
                    )
                    continue

                result = self._score_open_answer(
                    student_answer=str(student_answer),
                    correct_answer=str(correct_answer),
                    explanation=str(explanation),
                    max_score=max_score,
                )

                output_event = {
                    "exam_id": exam_id,
                    "course_id": event.get("course_id"),
                    "requested_at": requested_at,
                    "student_id": student_id,
                    "student_name": student_name,
                    "question_id": question_id,
                    "score": result.score,
                    "max_score": result.max_score,
                    "feedback": result.feedback,
                    "scored_at": datetime.now(timezone.utc).isoformat(),
                    "rubric_justification": result.rubric_justification,
                    "provider": result.provider,
                    "fallback_used": result.fallback_used,
                }

                ok = publish_event(settings.KAFKA_TOPIC_EXAM_SCORED, output_event)
                if ok:
                    published += 1
                    logger.info(
                        "[ExamScorer] Score publie exam=%s question=%s student=%s score=%.2f/%.2f",
                        exam_id,
                        question_id,
                        student_id,
                        result.score,
                        result.max_score,
                    )

        logger.info(
            "[ExamScorer] Batch corrige exam=%s submissions=%d publies=%d",
            exam_id,
            len(submissions),
            published,
        )

    def _score_open_answer(
        self,
        student_answer: str,
        correct_answer: str,
        explanation: str,
        max_score: float,
    ) -> ScoreResult:
        prompt = (
            "Tu es un correcteur d'examen strict et juste.\n"
            "Evalue la reponse et retourne UNIQUEMENT un JSON valide.\n"
            "Schema JSON attendu:\n"
            "{\n"
            "  \"score\": number,\n"
            "  \"feedback\": string,\n"
            "  \"rubric_justification\": string\n"
            "}\n"
            "Contraintes:\n"
            f"- score entre 0 et {max_score}\n"
            "- feedback court, actionnable\n"
            "- justification basee explicitement sur la reponse correcte et l'explication\n\n"
            f"Reponse correcte:\n{correct_answer}\n\n"
            f"Explication attendue:\n{explanation}\n\n"
            f"Reponse etudiant:\n{student_answer}\n"
        )

        llm_result = invoke_with_fallback(prompt)

        if not llm_result.answer:
            logger.warning("[ExamScorer] LLM indisponible, score par defaut 0")
            return ScoreResult(
                score=0.0,
                max_score=max_score,
                feedback="Scoring indisponible: echec fournisseur LLM.",
                rubric_justification=llm_result.error or "Aucune reponse LLM.",
                provider=llm_result.provider,
                fallback_used=llm_result.fallback_used,
            )

        score = 0.0
        feedback = ""
        justification = ""

        try:
            raw = llm_result.answer.strip()
            if raw.startswith("```"):
                raw = raw.strip("`")
                raw = raw.replace("json", "", 1).strip()

            parsed = json.loads(raw)
            score = float(parsed.get("score", 0.0))
            feedback = str(parsed.get("feedback", "")).strip()
            justification = str(parsed.get("rubric_justification", "")).strip()
        except Exception as e:
            logger.warning(f"[ExamScorer] Reponse LLM non JSON, fallback regex: {e}")
            score = 0.0
            feedback = "Format de scoring invalide retourne par le LLM."
            justification = llm_result.answer[:1000]

        score = max(0.0, min(score, max_score))

        return ScoreResult(
            score=score,
            max_score=max_score,
            feedback=feedback or "Aucun feedback fourni.",
            rubric_justification=justification or "Aucune justification fournie.",
            provider=llm_result.provider,
            fallback_used=llm_result.fallback_used,
        )


_exam_scorer_consumer: Optional[ExamScorerConsumer] = None


def get_exam_scorer_consumer() -> ExamScorerConsumer:
    global _exam_scorer_consumer
    if _exam_scorer_consumer is None:
        _exam_scorer_consumer = ExamScorerConsumer()
    return _exam_scorer_consumer


async def run_exam_scorer_loop() -> None:
    consumer = get_exam_scorer_consumer()
    if not consumer.start():
        logger.warning("[ExamScorer] Consumer non demarre")
        return

    try:
        logger.info("[ExamScorer] Loop demarree")
        while True:
            consumer.poll_once()
            await asyncio.sleep(0.5)
    except asyncio.CancelledError:
        logger.info("[ExamScorer] Loop annulee")
        consumer.stop()
    except Exception as e:
        logger.error(f"[ExamScorer] Erreur loop: {e}")
        consumer.stop()


def stop_exam_scorer_consumer() -> None:
    global _exam_scorer_consumer
    if _exam_scorer_consumer is not None:
        _exam_scorer_consumer.stop()
        _exam_scorer_consumer = None
