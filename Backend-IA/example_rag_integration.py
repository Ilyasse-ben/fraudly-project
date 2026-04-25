"""
Example integration script — Comment utiliser le pipeline RAG dans une application.
Démontre le cycle complet : ingest → search → build_prompt → eval.
"""

from app.services.rag_service import search, build_rag_prompt, ingest_file
from app.services.rag_evaluation import evaluate_rag
from app.schemas.common import DocumentType
from app.core.logger import get_logger

logger = get_logger(__name__)


def example_ingest_document():
    """Exemple 1 : Ingérer un document PDF."""
    logger.info("=== EXEMPLE 1 : Ingestion ===")
    
    result = ingest_file(
        file_path="./Algebre_Lineaire.pdf",
        filename="Algebre_Lineaire.pdf",
        course_id="MATH_101",
        chapter_id="Ch_2_Matrices",
        doc_type=DocumentType.PDF,
    )
    
    logger.info(f"Ingestion complète:")
    logger.info(f"  - Pages: {result.pages_processed}")
    logger.info(f"  - Chunks: {result.chunks_indexed}")
    logger.info(f"  - Status: {result.status}")


def example_search():
    """Exemple 2 : Recherche sémantique."""
    logger.info("=== EXEMPLE 2 : Recherche ===")
    
    query = "Comment calculer le déterminant d'une matrice?"
    
    result = search(
        query=query,
        course_id="MATH_101",
        top_k=3,
    )
    
    logger.info(f"Recherche: '{query}'")
    logger.info(f"Résultats: {result.total_found} chunks")
    
    for i, chunk in enumerate(result.chunks, 1):
        logger.info(f"  [{i}] Score={chunk.score:.4f} | Page {chunk.page} | {chunk.source_file}")
        logger.info(f"      {chunk.content[:100]}...")
    
    return result


def example_build_prompt(search_result):
    """Exemple 3 : Construire le prompt RAG pour le LLM."""
    logger.info("=== EXEMPLE 3 : Construction Prompt RAG ===")
    
    question = "Comment calculer le déterminant d'une matrice?"
    prompt = build_rag_prompt(question, search_result.chunks)
    
    logger.info(f"Prompt RAG ({len(prompt)} chars):")
    logger.info(prompt[:500] + "...")
    
    return prompt


def example_evaluate_rag():
    """Exemple 4 : Évaluer la qualité du RAG."""
    logger.info("=== EXEMPLE 4 : Évaluation RAGAS ===")
    
    # Simule une question, contexte, et réponse LLM
    query = "Comment calculer le déterminant d'une matrice?"
    
    context = """
    Le déterminant d'une matrice est un nombre associé à chaque matrice carrée.
    Il est noté det(A) ou |A|.
    
    Pour une matrice 2×2: det([a b; c d]) = ad - bc
    
    Pour une matrice 3×3, on peut utiliser la règle de Sarrus ou développer par rapport à une ligne ou colonne.
    """
    
    llm_response = """
    Pour calculer le déterminant d'une matrice:
    
    1. Si c'est une matrice 2×2 [a b; c d], utilisez la formule: det = ad - bc
    
    2. Pour une matrice 3×3 ou plus grande, vous pouvez:
       - Utiliser la règle de Sarrus (pour 3×3)
       - Développer par rapport à une ligne ou colonne
       - Utiliser l'élimination gaussienne
    
    3. Le déterminant a plusieurs applications: calcul d'inverse, volume, système d'équations
    """
    
    metrics = evaluate_rag(
        query=query,
        retrieved_contexts=[context],
        llm_response=llm_response,
        scores=[0.85],  # Score de similarité du retrieval
    )
    
    logger.info(f"Métriques RAGAS:")
    logger.info(f"  - Faithfulness: {metrics.faithfulness:.4f}")
    logger.info(f"  - Relevancy: {metrics.relevancy:.4f}")
    logger.info(f"  - Answer Relevancy: {metrics.answer_relevancy:.4f}")
    logger.info(f"  - Context Precision: {metrics.context_precision:.4f}")
    logger.info(f"  - Overall Score: {metrics.overall_score:.4f}")


def example_kafka_flow():
    """Exemple 5 : Flow Kafka (resource_uploaded → indexation automatique)."""
    logger.info("=== EXEMPLE 5 : Kafka Flow ===")
    
    # En production, ce message serait envoyé par le Frontend/Backend Spring
    # Ici, on simule
    
    kafka_message = {
        "resource_id": "res_12345",
        "course_id": "MATH_101",
        "chapter_id": "Ch_2_Matrices",
        "filename": "cours_matrices.pdf",
        "file_content_base64": "JVBERi0x...",  # Contenu PDF en base64
    }
    
    logger.info(f"Message Kafka reçu:")
    logger.info(f"  - Resource: {kafka_message['resource_id']}")
    logger.info(f"  - File: {kafka_message['filename']}")
    logger.info(f"  - Course: {kafka_message['course_id']}")
    logger.info(f"→ Consumer indexe automatiquement le document")
    logger.info(f"→ Puis publie le résultat sur KAFKA_TOPIC_AI_RESULTS")


def example_api_flow():
    """Exemple 6 : Utilisation depuis l'API FastAPI."""
    logger.info("=== EXEMPLE 6 : API Flow ===")
    
    logger.info("Endpoints disponibles:")
    logger.info("  POST /knowledge/search")
    logger.info("    query='Comment...?' course_id='MATH_101' top_k=5")
    logger.info("    → KnowledgeSearchResponse")
    logger.info("")
    logger.info("  POST /knowledge/ingest")
    logger.info("    file=(multipart) course_id='MATH_101' chapter_id='Ch_2'")
    logger.info("    → IngestResponse")
    logger.info("")
    logger.info("  GET /knowledge/stats")
    logger.info("    → {total_chunks, collection_name, courses_indexed}")
    logger.info("")
    logger.info("  GET /knowledge/courses")
    logger.info("    → ['MATH_101', 'CS_201', ...]")


def example_s3_integration():
    """Exemple 7 : Intégration S3 pour documents cloud."""
    logger.info("=== EXEMPLE 7 : S3 Integration ===")
    
    # Import conditionnel (si S3 activé)
    try:
        from app.services.s3_service import download_document, upload_document
        
        # Télécharger un document S3
        s3_key = "courses/MATH_101/Ch_2_Matrices/cours.pdf"
        file_bytes, content_type = download_document(s3_key)
        
        # Indexer le document téléchargé
        from app.services.rag_service import ingest_bytes
        result = ingest_bytes(
            file_bytes=file_bytes,
            filename="cours.pdf",
            course_id="MATH_101",
            chapter_id="Ch_2_Matrices",
            doc_type=DocumentType.PDF,
        )
        
        logger.info(f"Document S3 indexé: {result.chunks_indexed} chunks")
        
    except Exception as e:
        logger.warning(f"S3 non configuré: {e}")


if __name__ == "__main__":
    import sys
    from app.core.logger import get_logger
    
    logger = get_logger(__name__)
    
    logger.info("╔════════════════════════════════════════════════════╗")
    logger.info("║  Fraudly RAG Pipeline — Exemples d'intégration      ║")
    logger.info("╚════════════════════════════════════════════════════╝\n")
    
    # À commenter/décommenter selon le test souhaité
    # example_ingest_document()
    # search_result = example_search()
    # example_build_prompt(search_result)
    example_evaluate_rag()
    # example_kafka_flow()
    # example_api_flow()
    # example_s3_integration()
    
    logger.info("\n✓ Exemples terminés")
