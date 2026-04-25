"""
Test manuel du pipeline RAG — IA-2 Fraudly
Lancer depuis la racine du projet :

    python test_rag.py

Prérequis :
    pip install -r requirements.txt
    Placer un PDF dans le même dossier que ce script (ex: Algebre_Lineaire.pdf)
"""

import sys
import time
from pathlib import Path
import uuid
import os

# Ajoute la racine du projet au PYTHONPATH
# Nécessaire pour que "from app.xxx import ..." fonctionne
sys.path.insert(0, str(Path(__file__).parent))

# Chroma natif peut crasher sur certains environnements Windows pendant add().
# Ce mode force un store vectoriel in-memory pour exécuter le pipeline de test.
os.environ.setdefault("FRAUDLY_CHROMA_IN_MEMORY", "1")

# ── Initialisation ChromaDB + Embedding AVANT les imports services ──
from app.core.config import settings
from app.db.chroma_client import init_chroma
from app.services.embedding_service import warm_up_model

# Isole les runs manuels pour éviter les collisions/corruptions d'une ancienne collection.
settings.CHROMA_COLLECTION = f"fraudly_knowledge_test_{uuid.uuid4().hex[:8]}"

print("=" * 60)
print("FRAUDLY — Test Pipeline RAG")
print("=" * 60)
print(f"[INIT] Collection test : {settings.CHROMA_COLLECTION}")

print("\n[INIT] Chargement ChromaDB...")
init_chroma()

print("[INIT] Chargement modèle embedding (peut prendre 10-30s la 1ère fois)...")
warm_up_model()
print("[INIT] Prêt.\n")

# ── Imports services ──────────────────────────────────────
from app.services.rag_service import ingest_file, search, build_rag_prompt
from app.schemas.common import DocumentType


# ─────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────

def section(title: str):
    print("\n" + "─" * 60)
    print(f"  {title}")
    print("─" * 60)


def ok(msg: str):
    print(f"  ✓  {msg}")


def fail(msg: str):
    print(f"  ✗  {msg}")


def info(msg: str):
    print(f"  →  {msg}")


# ─────────────────────────────────────────────────────────
# TEST 1 — Ingestion
# ─────────────────────────────────────────────────────────

def test_ingestion(pdf_path: Path):
    section("TEST 1 — Ingestion PDF")

    if not pdf_path.exists():
        fail(f"Fichier introuvable : {pdf_path}")
        fail("Placez un PDF dans le même dossier que ce script.")
        return None

    info(f"Fichier    : {pdf_path.name}")
    info(f"Taille     : {pdf_path.stat().st_size / 1024:.1f} KB")
    info(f"Stratégie  : {settings.PDF_IMAGE_STRATEGY}")
    info(f"Chunk size : {settings.CHUNK_SIZE} chars | overlap : {settings.CHUNK_OVERLAP}")

    start = time.time()
    response = ingest_file(
        file_path=str(pdf_path),
        filename=pdf_path.name,
        course_id="course_1",
        chapter_id="chap_1",
        doc_type=DocumentType.PDF,
    )
    duration = time.time() - start

    print()
    info(f"Status          : {response.status}")
    info(f"Pages traitées  : {response.pages_processed}")
    info(f"Chunks indexés  : {response.chunks_indexed}")
    info(f"Durée           : {duration:.2f}s")

    if response.message:
        info(f"Message         : {response.message}")

    # Vérifications
    if response.status == "ok" and response.chunks_indexed > 0:
        ok("Ingestion réussie")
        ok(f"{response.chunks_indexed} chunks dans ChromaDB")
    else:
        fail(f"Ingestion échouée : status={response.status}")

    return response


# ─────────────────────────────────────────────────────────
# TEST 2 — Recherche sémantique
# ─────────────────────────────────────────────────────────

def test_search():
    section("TEST 2 — Recherche sémantique")

    queries = [
        "Qu'est-ce qu'une matrice ?",
        "Comment calculer un déterminant ?",
        "Définition d'un vecteur propre",
    ]

    for query in queries:
        print(f"\n  Question : \"{query}\"")
        start  = time.time()
        result = search(query=query, course_id="course_1", top_k=3)
        duration = time.time() - start

        if not result or not result.chunks:
            fail("Aucun résultat trouvé")
            continue

        ok(f"{result.total_found} chunks en {duration:.3f}s")

        for i, chunk in enumerate(result.chunks, 1):
            print(f"\n    [{i}] Score : {chunk.score:.4f}")
            print(f"        Source : {chunk.source_file} | page {chunk.page}")
            # Afficher les 120 premiers caractères du chunk
            preview = chunk.content[:120].replace("\n", " ")
            print(f"        Extrait : {preview}...")

    return result  # retourne le dernier résultat pour le test suivant


# ─────────────────────────────────────────────────────────
# TEST 3 — Construction du prompt RAG
# ─────────────────────────────────────────────────────────

def test_prompt(chunks):
    section("TEST 3 — Construction du prompt RAG")

    question = "Explique la notion de matrice inversible"
    prompt   = build_rag_prompt(question=question, chunks=chunks)

    ok(f"Prompt généré ({len(prompt)} caractères)")

    print("\n  --- Aperçu (500 premiers caractères) ---")
    print(prompt[:500])
    print("  [...]")

    # Vérifications structure
    checks = [
        ("Contient la question",   question in prompt),
        ("Contient le contexte",   "CONTEXTE" in prompt),
        ("Contient les règles",    "RÈGLES" in prompt),
        ("Contient au moins 1 source", "Source 1" in prompt),
    ]

    print()
    for label, passed in checks:
        if passed:
            ok(label)
        else:
            fail(label)


# ─────────────────────────────────────────────────────────
# TEST 4 — Cas limites
# ─────────────────────────────────────────────────────────

def test_edge_cases():
    section("TEST 4 — Cas limites")

    # 4a. Recherche sans résultats attendus
    print("\n  4a. Recherche hors-sujet (cuisine)")
    result = search(query="recette de tajine marocain", course_id="course_1", top_k=3)
    if result.total_found > 0:
        info(f"  {result.total_found} chunks retournés (scores probablement bas)")
        worst_score = min(c.score for c in result.chunks)
        info(f"  Score minimum : {worst_score:.4f}")
        if worst_score < 0.3:
            ok("Scores faibles → retrieval cohérent")
        else:
            fail("Scores élevés pour une question hors-sujet → vérifier le modèle")
    else:
        ok("Aucun résultat — collection vide ou filtre actif")

    # 4b. Recherche sans filtre courseId
    print("\n  4b. Recherche sans filtre courseId")
    result_global = search(query="matrice", course_id=None, top_k=5)
    ok(f"  {result_global.total_found} chunks (toute la KB)")

    # 4c. Prompt avec chunks vides
    print("\n  4c. Prompt RAG avec chunks vides")
    prompt_vide = build_rag_prompt(question="Test ?", chunks=[])
    if "Aucun document pertinent" in prompt_vide:
        ok("Fallback prompt vide correct")
    else:
        fail("Fallback prompt vide manquant")


# ─────────────────────────────────────────────────────────
# TEST 5 — Stats ChromaDB
# ─────────────────────────────────────────────────────────

def test_stats():
    section("TEST 5 — Stats Knowledge Base")

    from app.services.rag_service import get_kb_stats
    stats = get_kb_stats()

    ok(f"Total chunks      : {stats['total_chunks']}")
    ok(f"Collection        : {stats['collection_name']}")
    ok(f"Cours indexés     : {stats['courses_indexed']}")


# ─────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────

def main():
    # Cherche un PDF dans le dossier courant
    # Priorité : Algebre_Lineaire.pdf → premier .pdf trouvé
    pdf_path = Path(__file__).parent / "Algebre_Lineaire.pdf"
    if not pdf_path.exists():
        pdfs = list(Path(__file__).parent.glob("*.pdf"))
        if pdfs:
            pdf_path = pdfs[0]
            print(f"[INFO] Algebre_Lineaire.pdf non trouvé → utilisation de : {pdf_path.name}")
        else:
            print("\n[ERREUR] Aucun fichier PDF trouvé dans le dossier.")
            print("Placer un PDF à la racine du projet et relancer.\n")
            sys.exit(1)

    # Lancer les tests dans l'ordre
    ingest_response = test_ingestion(pdf_path)

    if ingest_response and ingest_response.chunks_indexed > 0:
        last_chunks = test_search()
        if last_chunks and last_chunks.chunks:
            test_prompt(last_chunks.chunks)
        test_edge_cases()

    test_stats()

    section("RÉSUMÉ")
    print("  Pipeline RAG testé : ingestion → chunking → embedding → ChromaDB → search → prompt")
    print("  Prochaine étape : brancher tutor_agent.py sur build_rag_prompt()\n")


if __name__ == "__main__":
    main()