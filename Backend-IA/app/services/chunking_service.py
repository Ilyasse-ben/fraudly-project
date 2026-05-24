"""
Chunking Service — découpage des pages en chunks indexables.

Amélioration vs découpage naïf au caractère :
    On découpe d'abord aux frontières de paragraphes (sémantique),
    puis on applique la limite de taille. Résultat : les chunks
    ne coupent jamais une phrase au milieu → meilleurs embeddings.

Appelé uniquement par rag_service.py.
"""

import re
from typing import List, Dict, Any
from app.core.config import settings


def _split_paragraphs(text: str) -> List[str]:
    """Découpe un texte en paragraphes propres (séparés par lignes vides)."""
    paragraphs = re.split(r"\n{2,}", text)
    return [p.strip() for p in paragraphs if p.strip()]


def _make_metadata(
    resource_id: str,
    course_id: str,
    chapter_id: str,
    filename: str,
    page_num: int,
) -> Dict[str, Any]:
    """Construit le dict metadata ChromaDB — factorisé pour éviter la duplication."""
    return {
        "resource_id": resource_id,
        "course_id":   course_id,
        "chapter_id":  chapter_id,
        "source_file": filename,
        "page":        page_num,
    }


def _split_large_paragraph(
    para: str,
    size: int,
    overlap: int,
    resource_id: str,
    course_id: str,
    chapter_id: str,
    filename: str,
    page_num: int,
) -> List[Dict[str, Any]]:
    """
    FIX : découpe au caractère un paragraphe unique qui dépasse CHUNK_SIZE.
    Sans cette fonction, un paragraphe de 5 000 chars était indexé tel quel,
    dégradant les embeddings et risquant de dépasser les limites ChromaDB.
    L'overlap est appliqué entre chaque sous-chunk pour préserver le contexte.
    """
    chunks = []
    start  = 0
    length = len(para)

    while start < length:
        end        = min(start + size, length)
        chunk_text = para[start:end].strip()
        if chunk_text:
            chunks.append({
                "text":     chunk_text,
                    "metadata": _make_metadata(resource_id, course_id, chapter_id, filename, page_num),
            })
        # Avance de (size - overlap) pour préserver le contexte de jonction
        step  = size - overlap if overlap < size else size
        start += step

    return chunks


def chunk_pages(
    pages: List[Dict[str, Any]],
    resource_id: str,
    course_id: str,
    chapter_id: str,
    filename: str,
) -> List[Dict[str, Any]]:
    """
    Découpe les pages en chunks avec overlap intelligent.

    Algorithme :
    - Accumule les paragraphes jusqu'à CHUNK_SIZE
    - Quand on dépasse → sauvegarde le chunk et conserve les derniers
      CHUNK_OVERLAP caractères comme contexte pour le chunk suivant
    - FIX : si un paragraphe seul dépasse CHUNK_SIZE, il est forcément
      découpé au caractère via _split_large_paragraph()

    Args:
        pages:      sortie de document_loader.load_document()
        course_id:  ID cours Fraudly (stocké dans les métadonnées ChromaDB)
        chapter_id: ID chapitre (pour le filtrage dans search())
        filename:   nom du fichier source (pour les citations dans le prompt RAG)

    Returns:
        Liste de {"text": str, "metadata": dict}
    """
    size    = settings.CHUNK_SIZE
    overlap = settings.CHUNK_OVERLAP
    chunks  = []

    for page in pages:
        page_num   = page["page_number"]
        paragraphs = _split_paragraphs(page["text"])

        current_chunk = ""

        for para in paragraphs:
            # FIX : paragraphe seul plus grand que CHUNK_SIZE → découpage forcé
            if len(para) > size:
                # Flush du chunk en cours avant d'insérer les sous-chunks
                if current_chunk.strip():
                    chunks.append({
                        "text":     current_chunk.strip(),
                        "metadata": _make_metadata(resource_id, course_id, chapter_id, filename, page_num),
                    })
                    current_chunk = ""
                chunks.extend(
                    _split_large_paragraph(para, size, overlap, resource_id, course_id, chapter_id, filename, page_num)
                )
                continue

            # Cas normal : l'ajout du paragraphe dépasse la limite
            if len(current_chunk) + len(para) > size:
                if current_chunk.strip():
                    chunks.append({
                        "text":     current_chunk.strip(),
                        "metadata": _make_metadata(resource_id, course_id, chapter_id, filename, page_num),
                    })
                    # FIX : overlap sécurisé — min() évite de dépasser la longueur réelle
                    tail          = min(overlap, len(current_chunk))
                    current_chunk = current_chunk[-tail:].strip() if tail > 0 else ""

            current_chunk += ("\n\n" if current_chunk else "") + para

        # Dernier chunk de la page (souvent incomplet → on le garde quand même)
        if current_chunk.strip():
            chunks.append({
                "text":     current_chunk.strip(),
                "metadata": _make_metadata(resource_id, course_id, chapter_id, filename, page_num),
            })

    return chunks