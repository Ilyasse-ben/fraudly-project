"""
Smoke test Kafka pour le pipeline de correction Backend-IA, sans Spring.

Ce script:
1) Publie un message exam.correction.requested
2) Ecoute exam.scored
3) Ecoute proctor.collusion_suspected
4) Valide des contraintes minimales de contrat

Usage:
    python scripts/smoke_test_correction_pipeline.py
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from kafka import KafkaConsumer, KafkaProducer

# Allow running as: python scripts/smoke_test_correction_pipeline.py
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings


def build_input_event(exam_id: str) -> Dict[str, Any]:
    return {
        "exam_id": exam_id,
        "course_id": "course-smoke-01",
        "requested_at": datetime.now(timezone.utc).isoformat(),
        "submissions": [
            {
                "student_id": "stu-1",
                "student_name": "Alice",
                "open_answers": [
                    {
                        "question_id": "q-1",
                        "student_answer": "La complexite est O(n log n) car on divise le probleme et on fusionne.",
                        "correct_answer": "La profondeur de recursion est log n et chaque niveau coute O(n), donc O(n log n).",
                        "explanation": "Mentionner division recursive + fusion lineaire.",
                        "max_score": 5,
                    },
                    {
                        "question_id": "q-2",
                        "student_answer": "Une pile suit le principe LIFO.",
                        "correct_answer": "Une pile est LIFO (Last In First Out).",
                        "explanation": "Donner la definition LIFO clairement.",
                        "max_score": 3,
                    },
                ],
            },
            {
                "student_id": "stu-2",
                "student_name": "Yassine",
                "open_answers": [
                    {
                        "question_id": "q-1",
                        "student_answer": "La complexite de merge sort est O(n log n) car on divise puis on fusionne.",
                        "correct_answer": "La profondeur de recursion est log n et chaque niveau coute O(n), donc O(n log n).",
                        "explanation": "Mentionner division recursive + fusion lineaire.",
                        "max_score": 5,
                    },
                    {
                        "question_id": "q-2",
                        "student_answer": "Pile = LIFO.",
                        "correct_answer": "Une pile est LIFO (Last In First Out).",
                        "explanation": "Donner la definition LIFO clairement.",
                        "max_score": 3,
                    },
                ],
            },
        ],
    }


def make_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        acks="all",
    )


def make_consumer(topic: str, group_suffix: str) -> KafkaConsumer:
    return KafkaConsumer(
        topic,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=f"{settings.KAFKA_GROUP_ID}-smoke-{group_suffix}",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="latest",
        enable_auto_commit=True,
        max_poll_records=50,
        session_timeout_ms=30000,
    )


def validate_scored_event(msg: Dict[str, Any]) -> None:
    required = [
        "exam_id",
        "course_id",
        "student_id",
        "student_name",
        "question_id",
        "score",
        "max_score",
        "feedback",
        "scored_at",
        "provider",
        "fallback_used",
    ]
    missing = [k for k in required if k not in msg]
    if missing:
        raise AssertionError(f"exam.scored incomplet: {missing}")

    score = float(msg["score"])
    max_score = float(msg["max_score"])
    if score < 0 or score > max_score:
        raise AssertionError(f"score hors bornes: score={score}, max_score={max_score}")


def validate_collusion_event(msg: Dict[str, Any]) -> None:
    required = ["exam_id", "course_id", "detected_at", "suspected_pairs"]
    missing = [k for k in required if k not in msg]
    if missing:
        raise AssertionError(f"proctor.collusion_suspected incomplet: {missing}")

    if not isinstance(msg["suspected_pairs"], list):
        raise AssertionError("suspected_pairs doit etre une liste")

    for pair in msg["suspected_pairs"]:
        pair_required = [
            "student_a_id",
            "student_a_name",
            "student_b_id",
            "student_b_name",
            "similarity_score",
            "question_id",
            "answer_a_preview",
            "answer_b_preview",
        ]
        pair_missing = [k for k in pair_required if k not in pair]
        if pair_missing:
            raise AssertionError(f"paire collusion incomplete: {pair_missing}")

        if float(pair["similarity_score"]) <= 0.85:
            raise AssertionError(
                f"similarity_score invalide (<=0.85): {pair['similarity_score']}"
            )


def main() -> int:
    if not settings.KAFKA_ENABLED:
        print("[SMOKE] KAFKA_ENABLED=False. Active Kafka dans .env puis relance.")
        return 1

    exam_id = f"exam-smoke-{int(time.time())}"
    input_event = build_input_event(exam_id)

    consumer_scored = make_consumer(settings.KAFKA_TOPIC_EXAM_SCORED, "scored")
    consumer_collusion = make_consumer(settings.KAFKA_TOPIC_COLLUSION_SUSPECTED, "collusion")
    producer = make_producer()

    expected_scored = sum(
        len(sub.get("open_answers", [])) for sub in input_event.get("submissions", [])
    )

    print("[SMOKE] Publishing exam.correction.requested...")
    producer.send(settings.KAFKA_TOPIC_EXAM_CORRECTION_REQUESTED, value=input_event).get(timeout=10)
    producer.flush()

    scored_events: List[Dict[str, Any]] = []
    collusion_events: List[Dict[str, Any]] = []

    deadline = time.time() + 90
    while time.time() < deadline:
        scored_batches = consumer_scored.poll(timeout_ms=1200, max_records=50)
        for _, records in scored_batches.items():
            for r in records:
                payload = r.value
                if payload.get("exam_id") == exam_id:
                    scored_events.append(payload)

        collusion_batches = consumer_collusion.poll(timeout_ms=1200, max_records=50)
        for _, records in collusion_batches.items():
            for r in records:
                payload = r.value
                if payload.get("exam_id") == exam_id:
                    collusion_events.append(payload)

        if len(scored_events) >= expected_scored and len(collusion_events) >= 1:
            break

    print(f"[SMOKE] exam.scored received: {len(scored_events)} / {expected_scored}")
    print(f"[SMOKE] proctor.collusion_suspected received: {len(collusion_events)}")

    if len(scored_events) < expected_scored:
        raise AssertionError(
            f"Nombre insuffisant de exam.scored: {len(scored_events)} < {expected_scored}"
        )

    for evt in scored_events:
        validate_scored_event(evt)

    # Une alerte de collusion peut ne pas apparaitre selon similarite reelle des sorties modeles.
    # Si presente, elle doit respecter le contrat.
    for evt in collusion_events:
        validate_collusion_event(evt)

    print("[SMOKE] SUCCESS: contrat Backend-IA valide sans Spring.")

    consumer_scored.close()
    consumer_collusion.close()
    producer.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
