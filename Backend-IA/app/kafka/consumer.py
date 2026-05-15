"""
Kafka Consumer — Indexation automatique des ressources uploadées.
Écoute le topic 'resource_uploaded' et déclenche le pipeline RAG.
"""
import json
import asyncio
from typing import Optional
from kafka import KafkaConsumer
from kafka.errors import KafkaError

from app.core.config import settings
from app.core.logger import get_logger
from app.services.rag_service import ingest_bytes
from app.schemas.common import DocumentType

logger = get_logger(__name__)

_consumer: Optional[KafkaConsumer] = None
_running = False


def get_consumer() -> Optional[KafkaConsumer]:
    """Retourne le singleton KafkaConsumer, créé lazily."""
    global _consumer
    
    if not settings.KAFKA_ENABLED:
        return None
    
    if _consumer is None:
        try:
            logger.info(
                f"[Kafka] Initialisation consumer "
                f"bootstrap_servers={settings.KAFKA_BOOTSTRAP_SERVERS} "
                f"group_id={settings.KAFKA_GROUP_ID}"
            )
            _consumer = KafkaConsumer(
                settings.KAFKA_TOPIC_RESOURCE_UPLOADED,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id=settings.KAFKA_GROUP_ID,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="earliest",
                enable_auto_commit=True,
            )
            logger.info(f"[Kafka] Consumer prêt pour '{settings.KAFKA_TOPIC_RESOURCE_UPLOADED}'")
        except Exception as e:
            logger.error(f"[Kafka] Erreur initialisation consumer: {e}")
            _consumer = None
    
    return _consumer


def _parse_resource_event(msg: dict) -> tuple[str, str, str, str, bytes]:
    """
    Parse un message resource_uploaded.
    
    Format attendu:
    {
        "resource_id": "uuid",
        "course_id": "course_123",
        "chapter_id": "chapter_456",
        "filename": "cours.pdf",
        "file_content_base64": "...",  ou "file_content": bytes
        "content_type": "application/pdf"
    }
    """
    resource_id = msg.get("resource_id", "unknown")
    course_id = msg.get("course_id", "")
    chapter_id = msg.get("chapter_id", "")
    filename = msg.get("filename", "resource")
    
    # Fichier en base64 ou bytes direct
    file_content_b64 = msg.get("file_content_base64")
    file_content_bytes = msg.get("file_content")
    
    if file_content_b64:
        import base64
        file_bytes = base64.b64decode(file_content_b64)
    elif file_content_bytes:
        if isinstance(file_content_bytes, str):
            file_bytes = file_content_bytes.encode("utf-8")
        else:
            file_bytes = file_content_bytes
    else:
        raise ValueError(f"Aucun contenu fichier dans {resource_id}")
    
    return resource_id, course_id, chapter_id, filename, file_bytes


def _get_document_type(filename: str) -> DocumentType:
    """Détermine le type de document d'après l'extension."""
    ext = filename.split(".")[-1].lower()
    if ext == "pdf":
        return DocumentType.PDF
    elif ext in ("docx", "doc"):
        return DocumentType.DOCX
    elif ext == "pptx":
        return DocumentType.PPTX
    else:
        raise ValueError(f"Type de document inconnu: {ext}")


async def consume_resources():
    """
    Boucle principale du consumer Kafka.
    Lis les messages et indexe automatiquement.
    """
    global _running
    
    consumer = get_consumer()
    if not consumer:
        logger.warning("[Kafka] KAFKA_ENABLED=False, consumer désactivé")
        return
    
    _running = True
    logger.info("[Kafka] Démarrage consumer...")
    
    try:
        for msg in consumer:
            if not _running:
                break
            
            try:
                event = msg.value
                logger.info(f"[Kafka] Message reçu: {event.get('resource_id', 'unknown')}")
                
                resource_id, course_id, chapter_id, filename, file_bytes = _parse_resource_event(event)
                
                # Validation basique
                if not course_id or not chapter_id:
                    logger.warning(
                        f"[Kafka] Métadonnées manquantes pour {resource_id}: "
                        f"course_id={course_id}, chapter_id={chapter_id}"
                    )
                    continue
                
                doc_type = _get_document_type(filename)
                
                # Indexation
                logger.info(
                    f"[Kafka] Indexation {filename} "
                    f"(course={course_id}, chapter={chapter_id}, size={len(file_bytes)} bytes)"
                )
                
                result = ingest_bytes(
                    file_bytes=file_bytes,
                    filename=filename,
                    resource_id=resource_id,
                    course_id=course_id,
                    chapter_id=chapter_id,
                    doc_type=doc_type,
                )
                
                logger.info(
                    f"[Kafka] ✓ Indexation complète → {result.chunks_indexed} chunks, "
                    f"status={result.status}"
                )
                
                # Publie le résultat sur AI_RESULTS topic
                logger.info(f"[Kafka] Ingest result object for {resource_id}: {result}")
                logger.info(f"[Kafka] Ingest result.vector_id for {resource_id}: {getattr(result, 'vector_id', None)}")
                _publish_ingest_result(resource_id, result)
                
            except Exception as e:
                logger.error(f"[Kafka] Erreur processing message: {e}")
                continue
    
    except KeyboardInterrupt:
        logger.info("[Kafka] Consumer interrompu")
    except Exception as e:
        logger.error(f"[Kafka] Erreur consumer: {e}")
    finally:
        if consumer:
            consumer.close()
        _running = False


def _publish_ingest_result(resource_id: str, result):
    """Publie le résultat d'indexation sur le topic AI_RESULTS."""
    if not settings.KAFKA_ENABLED:
        return
    
    try:
        from kafka import KafkaProducer
        producer = KafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        
        msg = {
            "resource_id": resource_id,
            "status": result.status,
            "chunks_indexed": result.chunks_indexed,
            "pages_processed": result.pages_processed,
            "vector_id": getattr(result, "vector_id", None),
        }
        
        logger.info(f"[Kafka] Publishing ai_results message: {msg}")
        producer.send(settings.KAFKA_TOPIC_AI_RESULTS, msg)
        producer.close()

        logger.info(f"[Kafka] Résultat publié pour {resource_id}")
    except Exception as e:
        logger.error(f"[Kafka] Erreur publication résultat: {e}")


def stop_consumer():
    """Arrête le consumer proprement."""
    global _running
    _running = False
    logger.info("[Kafka] Arrêt consumer demandé")

def _run_consumer_sync():
    """Version synchrone bloquante — tourne dans un thread séparé."""
    global _running

    consumer = get_consumer()
    if not consumer:
        logger.warning("[Kafka] KAFKA_ENABLED=False, consumer désactivé")
        return

    _running = True
    logger.info("[Kafka] Démarrage consumer...")

    try:
        for msg in consumer:
            if not _running:
                break
            try:
                event = msg.value
                logger.info(f"[Kafka] Message reçu: {event.get('resource_id', 'unknown')}")
                resource_id, course_id, chapter_id, filename, file_bytes = _parse_resource_event(event)

                if not course_id or not chapter_id:
                    logger.warning(f"[Kafka] Métadonnées manquantes pour {resource_id}")
                    continue

                doc_type = _get_document_type(filename)
                result = ingest_bytes(
                    file_bytes=file_bytes,
                    filename=filename,
                    resource_id=resource_id,
                    course_id=course_id,
                    chapter_id=chapter_id,
                    doc_type=doc_type,
                )
                logger.info(f"[Kafka] ✓ {result.chunks_indexed} chunks indexés")
                _publish_ingest_result(resource_id, result)

            except Exception as e:
                logger.error(f"[Kafka] Erreur processing message: {e}")
                continue
    except Exception as e:
        logger.error(f"[Kafka] Erreur consumer: {e}")
    finally:
        if consumer:
            consumer.close()
        _running = False


async def run_resource_consumer_loop() -> None:
    """
    Wrapper async NON-BLOQUANT — tourne le consumer dans un thread séparé.
    """
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(None, _run_consumer_sync)
    except asyncio.CancelledError:
        logger.info("[Kafka] Resource consumer loop annulée")
        stop_consumer()
    except Exception as e:
        logger.error(f"[Kafka] Erreur resource consumer loop: {e}")
        stop_consumer()