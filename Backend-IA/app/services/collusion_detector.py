"""
Collusion Detection Service — Détection des réponses similaires entre étudiants.

Pipeline:
1. Écoute le topic 'exam.correction.requested'
2. Construit une réponse agrégée par étudiant depuis le batch
3. Calcule la similarité pairwise avec paraphrase-multilingual-MiniLM-L12-v2
4. Si similarité > 0.85 → publie sur 'proctor.collusion_suspected'
"""

import json
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from sklearn.metrics.pairwise import cosine_similarity

from app.core.config import settings
from app.core.logger import get_logger
from app.kafka.producer import publish_event

logger = get_logger(__name__)

# ─────────────────────────────
# TYPES & DATA MODELS
# ─────────────────────────────

@dataclass
class StudentAnswer:
    """Représentation d'une réponse d'étudiant."""
    student_id: str
    student_name: Optional[str]
    answer_text: str
    submission_timestamp: str
    course_id: Optional[str] = None
    full_text: Optional[str] = None  # Texte concatené des réponses


@dataclass
class CollusionPair:
    """Paire d'étudiants suspectée de collusion."""
    exam_id: str
    course_id: Optional[str]
    question_id: str
    student_a_id: str
    student_b_id: str
    student_a_name: Optional[str]
    student_b_name: Optional[str]
    similarity_score: float
    detected_at: str
    answer_a_preview: str
    answer_b_preview: str


# ─────────────────────────────
# COLLUSION DETECTION
# ─────────────────────────────

class CollusionDetector:
    """
    Détecteur de collusion via similarité d'embeddings.
    
    Utilise paraphrase-multilingual-MiniLM-L12-v2 pour calculer la similarité
    entre les réponses des étudiants.
    """
    
    # Modèle dédié aux similarités (plus performant que all-MiniLM-L6-v2)
    COLLUSION_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    SIMILARITY_THRESHOLD = 0.85
    
    def __init__(self):
        """Initialise le détecteur avec le modèle d'embedding spécialisé."""
        self._model = None
        self._load_model()
    
    def _load_model(self) -> None:
        """Charge le modèle de similarité."""
        try:
            from sentence_transformers import SentenceTransformer
            import torch
            
            device = settings.EMBEDDING_DEVICE
            if device == "cuda" and not torch.cuda.is_available():
                device = "cpu"
            
            logger.info(f"[Collusion] Chargement {self.COLLUSION_MODEL_NAME} sur {device}")
            self._model = SentenceTransformer(self.COLLUSION_MODEL_NAME, device=device)
            logger.info("[Collusion] Modèle de détection prêt")
        except Exception as e:
            logger.error(f"[Collusion] Erreur chargement modèle: {e}")
            raise
    
    def detect_collusion_pairs(
        self,
        exam_id: str,
        course_id: Optional[str],
        question_id: str,
        answers: List[StudentAnswer],
        threshold: float = SIMILARITY_THRESHOLD,
    ) -> List[CollusionPair]:
        """
        Détecte les paires d'étudiants avec similarité suspecte.
        
        Args:
            exam_id: ID de l'examen
            answers: Liste des réponses des étudiants
            threshold: Seuil de similarité (défaut: 0.85)
            
        Returns:
            Liste des paires suspectes
        """
        if len(answers) < 2:
            return []
        
        # Prépare les textes pour embedding
        texts = [ans.full_text or ans.answer_text for ans in answers]
        
        try:
            # Encode tous les textes
            embeddings = self._model.encode(texts, convert_to_numpy=True)
            
            # Calcule la matrice de similarité cosinus
            similarity_matrix = cosine_similarity(embeddings)
            
            # Extrait les paires > threshold
            suspicious_pairs = []
            n = len(answers)
            
            for i in range(n):
                for j in range(i + 1, n):
                    similarity = float(similarity_matrix[i, j])
                    
                    if similarity >= threshold:
                        pair = CollusionPair(
                            exam_id=exam_id,
                            course_id=course_id,
                            question_id=question_id,
                            student_a_id=answers[i].student_id,
                            student_b_id=answers[j].student_id,
                            student_a_name=answers[i].student_name,
                            student_b_name=answers[j].student_name,
                            similarity_score=similarity,
                            detected_at=datetime.utcnow().isoformat(),
                            answer_a_preview=texts[i][:200],
                            answer_b_preview=texts[j][:200],
                        )
                        suspicious_pairs.append(pair)
                        
                        logger.warning(
                            f"[Collusion] SUSPECTE: exam={exam_id}, "
                            f"student_a={answers[i].student_id}, "
                            f"student_b={answers[j].student_id}, "
                            f"score={similarity:.4f}"
                        )
            
            return suspicious_pairs
        
        except Exception as e:
            logger.error(f"[Collusion] Erreur calcul similarité: {e}")
            return []


# ─────────────────────────────
# KAFKA CONSUMER
# ─────────────────────────────

class CollusionConsumer:
    """
    Consommateur Kafka pour exam.submitted.
    Écoute les soumissions, détecte collusions, publie alertes.
    """
    
    def __init__(self):
        """Initialise le consommateur."""
        self._consumer: Optional[KafkaConsumer] = None
        self._detector = CollusionDetector()
        self._running = False
    
    def start(self) -> bool:
        """
        Lance le consumer en mode polling continu.
        À appeler depuis une tâche asyncio en arrière-plan.
        """
        if not settings.KAFKA_ENABLED:
            logger.info("[Collusion] Kafka désactivé, consumer non lancé")
            return False
        
        try:
            logger.info(
                f"[Collusion Consumer] Initialisation "
                f"topic={settings.KAFKA_TOPIC_EXAM_CORRECTION_REQUESTED}, "
                f"group_id={settings.KAFKA_GROUP_ID}"
            )
            
            self._consumer = KafkaConsumer(
                settings.KAFKA_TOPIC_EXAM_CORRECTION_REQUESTED,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id=f"{settings.KAFKA_GROUP_ID}-collusion",
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                max_poll_records=10,
                session_timeout_ms=30000,
            )
            logger.info("[Collusion Consumer] Prêt à écouter exam.correction.requested")
            self._running = True
            return True
        except Exception as e:
            logger.error(f"[Collusion Consumer] Erreur init: {e}")
            self._running = False
            return False
    
    def stop(self) -> None:
        """Arrête le consumer."""
        self._running = False
        if self._consumer:
            try:
                self._consumer.close()
                logger.info("[Collusion Consumer] Arrêté")
            except Exception as e:
                logger.error(f"[Collusion Consumer] Erreur arrêt: {e}")
    
    def poll_once(self) -> None:
        """
        Poll une seule fois depuis Kafka.
        À appeler dans une boucle asyncio.
        """
        if not self._running or self._consumer is None:
            return
        
        try:
            messages = self._consumer.poll(timeout_ms=1000, max_records=10)
            
            if not messages:
                return
            
            for topic_partition, records in messages.items():
                for record in records:
                    self._process_correction_request(record.value)
        
        except KafkaError as e:
            logger.error(f"[Collusion Consumer] Erreur poll: {e}")
        except Exception as e:
            logger.error(f"[Collusion Consumer] Erreur traitement: {e}")
    
    def _process_correction_request(self, event: Dict) -> None:
        """
        Traite une demande de correction d'examen.
        
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
                            "student_answer": "text",
                            "correct_answer": "text",
                            "explanation": "text",
                            "max_score": 20
                        }
                    ]
                }
            ]
        }
        """
        exam_id = event.get("exam_id")
        course_id = event.get("course_id")
        requested_at = event.get("requested_at")
        submissions = event.get("submissions", [])
        
        if not exam_id:
            logger.warning("[Collusion] Événement incomplet (exam_id requis)")
            return

        if not isinstance(submissions, list) or not submissions:
            logger.info(f"[Collusion] Aucun submissions à analyser pour exam={exam_id}")
            return

        # Regroupe les réponses par question puis par étudiant.
        per_question: Dict[str, List[StudentAnswer]] = {}
        for submission in submissions:
            if not isinstance(submission, dict):
                continue

            student_id = submission.get("student_id")
            if not student_id:
                continue

            student_name = submission.get("student_name")
            open_answers = submission.get("open_answers", [])
            ts = submission.get("submission_timestamp") or requested_at or ""

            if not isinstance(open_answers, list):
                continue

            for answer in open_answers:
                if not isinstance(answer, dict):
                    continue
                question_id = str(answer.get("question_id") or "").strip()
                text = answer.get("student_answer") or answer.get("answer_text") or ""
                if not question_id or not text:
                    continue

                per_question.setdefault(question_id, []).append(
                    StudentAnswer(
                        student_id=student_id,
                        student_name=student_name,
                        answer_text=str(text),
                        submission_timestamp=str(ts or ""),
                        course_id=course_id,
                        full_text=str(text),
                    )
                )

        logger.info(
            "[Collusion] Analyse demandee exam=%s questions=%d submissions=%d",
            exam_id,
            len(per_question),
            len(submissions),
        )
        self._analyze_exam(exam_id, course_id, per_question)
    
    def _analyze_exam(
        self,
        exam_id: str,
        course_id: Optional[str],
        per_question_answers: Dict[str, List[StudentAnswer]],
    ) -> None:
        """
        Lance la détection de collusion pour un examen complet.
        Publie les résultats sur proctor.collusion_suspected.
        """
        detected_at = datetime.utcnow().isoformat()
        suspicious_pairs: List[dict] = []

        if not per_question_answers:
            logger.debug(f"[Collusion] Examen {exam_id}: aucune réponse exploitable, skip")
            return
        
        # Détecte les paires suspectes pour chaque question.
        for question_id, answers in per_question_answers.items():
            if len(answers) < 2:
                continue

            pairs = self._detector.detect_collusion_pairs(
                exam_id=exam_id,
                course_id=course_id,
                question_id=question_id,
                answers=answers,
                threshold=CollusionDetector.SIMILARITY_THRESHOLD,
            )

            for pair in pairs:
                suspicious_pairs.append(
                    {
                        "student_a_id": pair.student_a_id,
                        "student_a_name": pair.student_a_name,
                        "student_b_id": pair.student_b_id,
                        "student_b_name": pair.student_b_name,
                        "similarity_score": pair.similarity_score,
                        "question_id": pair.question_id,
                        "answer_a_preview": pair.answer_a_preview,
                        "answer_b_preview": pair.answer_b_preview,
                    }
                )

        if not suspicious_pairs:
            logger.info("[Collusion] Aucune paire suspecte detectee pour exam=%s", exam_id)
            return

        event = {
            "exam_id": exam_id,
            "course_id": course_id,
            "detected_at": detected_at,
            "suspected_pairs": suspicious_pairs,
        }

        topic = settings.KAFKA_TOPIC_COLLUSION_SUSPECTED or settings.KAFKA_TOPIC_FRAUD_ALERTS
        success = publish_event(topic, event)
        if success:
            logger.info(
                "[Collusion] Alerte publiée exam=%s pairs=%d",
                exam_id,
                len(suspicious_pairs),
            )

        # Pas de buffer persistant en mode correction-requested batch.


# ─────────────────────────────
# SINGLETON & BACKGROUND TASK
# ─────────────────────────────

_collusion_consumer: Optional[CollusionConsumer] = None


def get_collusion_consumer() -> CollusionConsumer:
    """Retourne le singleton CollusionConsumer."""
    global _collusion_consumer
    if _collusion_consumer is None:
        _collusion_consumer = CollusionConsumer()
    return _collusion_consumer


async def run_collusion_consumer_loop() -> None:
    """
    Boucle principale du consumer (à appeler en tâche asyncio).
    Écoute exam.correction.requested et détecte collusions en continu.
    """
    consumer = get_collusion_consumer()
    
    if not consumer.start():
        logger.warning("[Collusion] Consumer non démarré")
        return
    
    try:
        logger.info("[Collusion] Consumer loop démarrée")
        while True:
            consumer.poll_once()
            await asyncio.sleep(0.5)  # Évite l'occupation CPU 100%
    except asyncio.CancelledError:
        logger.info("[Collusion] Consumer loop annulée")
        consumer.stop()
    except Exception as e:
        logger.error(f"[Collusion] Erreur consumer loop: {e}")
        consumer.stop()


def stop_collusion_consumer() -> None:
    """Arrête le consumer."""
    global _collusion_consumer
    if _collusion_consumer:
        _collusion_consumer.stop()
        _collusion_consumer = None
