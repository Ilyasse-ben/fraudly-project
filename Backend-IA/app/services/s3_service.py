"""
S3 Service — Récupération des documents depuis AWS S3.
Intégration pour le stockage en production des ressources pédagogiques.
"""
import io
from typing import Optional, Tuple
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

_s3_client = None


def get_s3_client():
    """Lazy initialization du client S3 boto3."""
    global _s3_client
    
    if not settings.S3_ENABLED:
        return None
    
    if _s3_client is None:
        try:
            import boto3
            _s3_client = boto3.client(
                "s3",
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )
            logger.info(f"[S3] Client prêt pour bucket '{settings.S3_BUCKET}'")
        except ImportError:
            logger.error("[S3] boto3 non installé — S3 désactivé")
            return None
        except Exception as e:
            logger.error(f"[S3] Erreur initialisation client: {e}")
            return None
    
    return _s3_client


def download_document(s3_key: str) -> Tuple[bytes, str]:
    """
    Télécharge un document depuis S3.
    
    Args:
        s3_key: Clé S3 du fichier (ex: "courses/course_1/chapter_1/cours.pdf")
    
    Returns:
        Tuple (file_content_bytes, content_type)
    """
    client = get_s3_client()
    if not client:
        raise RuntimeError("S3 désactivé ou non configuré")
    
    try:
        logger.info(f"[S3] Téléchargement s3://{settings.S3_BUCKET}/{s3_key}")
        
        response = client.get_object(Bucket=settings.S3_BUCKET, Key=s3_key)
        file_content = response["Body"].read()
        content_type = response.get("ContentType", "application/octet-stream")
        
        logger.info(f"[S3] ✓ Téléchargé {len(file_content)} bytes")
        return file_content, content_type
        
    except Exception as e:
        logger.error(f"[S3] Erreur téléchargement {s3_key}: {e}")
        raise


def upload_document(local_path: str, s3_key: str) -> str:
    """
    Upload un document local vers S3.
    
    Args:
        local_path: Chemin du fichier local
        s3_key: Clé S3 de destination
    
    Returns:
        S3 URL du fichier uploadé
    """
    client = get_s3_client()
    if not client:
        raise RuntimeError("S3 désactivé ou non configuré")
    
    try:
        logger.info(f"[S3] Upload {local_path} → s3://{settings.S3_BUCKET}/{s3_key}")
        
        client.upload_file(local_path, settings.S3_BUCKET, s3_key)
        
        s3_url = f"s3://{settings.S3_BUCKET}/{s3_key}"
        logger.info(f"[S3] ✓ Uploadé à {s3_url}")
        
        return s3_url
        
    except Exception as e:
        logger.error(f"[S3] Erreur upload: {e}")
        raise


def list_documents(prefix: str = "") -> list:
    """
    Liste les documents dans S3 sous un préfixe.
    
    Args:
        prefix: Préfixe S3 (ex: "courses/course_1/")
    
    Returns:
        Liste des clés S3
    """
    client = get_s3_client()
    if not client:
        raise RuntimeError("S3 désactivé ou non configuré")
    
    try:
        logger.info(f"[S3] Liste objets avec préfixe '{prefix}'")
        
        response = client.list_objects_v2(Bucket=settings.S3_BUCKET, Prefix=prefix)
        
        keys = [obj["Key"] for obj in response.get("Contents", [])]
        logger.info(f"[S3] ✓ {len(keys)} objets trouvés")
        
        return keys
        
    except Exception as e:
        logger.error(f"[S3] Erreur liste: {e}")
        raise


def delete_document(s3_key: str) -> bool:
    """
    Supprime un document de S3.
    
    Args:
        s3_key: Clé S3 du fichier
    
    Returns:
        True si succès, False sinon
    """
    client = get_s3_client()
    if not client:
        raise RuntimeError("S3 désactivé ou non configuré")
    
    try:
        logger.info(f"[S3] Suppression {s3_key}")
        
        client.delete_object(Bucket=settings.S3_BUCKET, Key=s3_key)
        
        logger.info(f"[S3] ✓ Supprimé")
        return True
        
    except Exception as e:
        logger.error(f"[S3] Erreur suppression: {e}")
        return False
