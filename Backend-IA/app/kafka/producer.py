"""
Kafka Producer — publication des événements vers les topics Fraudly.
"""
import json
from typing import Dict, Any, Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

_producer: Optional[KafkaProducer] = None


def get_producer() -> Optional[KafkaProducer]:
    """Retourne le singleton KafkaProducer, créé lazily."""
    global _producer
    
    if not settings.KAFKA_ENABLED:
        return None
    
    if _producer is None:
        try:
            logger.info(
                f"[Kafka Producer] Initialisation "
                f"bootstrap_servers={settings.KAFKA_BOOTSTRAP_SERVERS}"
            )
            _producer = KafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all",
                retries=3,
            )
            logger.info("[Kafka Producer] Prêt pour publication")
        except Exception as e:
            logger.error(f"[Kafka Producer] Erreur initialisation: {e}")
            _producer = None
    
    return _producer


def publish_event(topic: str, event: Dict[str, Any]) -> bool:
    """
    Publie un événement sur un topic Kafka.
    
    Args:
        topic: Nom du topic Kafka
        event: Dictionnaire à sérialiser en JSON
        
    Returns:
        True si succès, False sinon
    """
    producer = get_producer()
    if producer is None:
        logger.warning(f"[Kafka] Kafka désactivé, événement non publié: {topic}")
        return False
    
    try:
        future = producer.send(topic, value=event)
        record_metadata = future.get(timeout=10)
        
        logger.info(
            f"[Kafka] Événement publié sur '{topic}' "
            f"(partition={record_metadata.partition}, offset={record_metadata.offset})"
        )
        return True
    except KafkaError as e:
        logger.error(f"[Kafka] Erreur publication '{topic}': {e}")
        return False
    except Exception as e:
        logger.error(f"[Kafka] Erreur inattendue publication: {e}")
        return False


def close_producer():
    """Ferme le producteur."""
    global _producer
    if _producer is not None:
        try:
            _producer.flush()
            _producer.close()
            logger.info("[Kafka Producer] Fermé")
        except Exception as e:
            logger.error(f"[Kafka Producer] Erreur fermeture: {e}")
        finally:
            _producer = None
