# Fraudly RAG Pipeline — Architecture Complète

## 📋 Vue d'ensemble

Le pipeline **Retrieval-Augmented Generation (RAG)** de Fraudly permet aux agents IA (Tutor, Assessment, etc.) de répondre aux utilisateurs en se basant sur **le contenu réel des cours**. 

**Pipeline complet:**
```
Ressource (PDF/DOCX/PPTX) 
  ↓
[Document Loader] (PyMuPDF, python-pptx)
  ↓
[Chunking Service] (découpe + overlap)
  ↓
[Embedding Service] (sentence-transformers/E5)
  ↓
[Vector Store] (ChromaDB/Weaviate/Pinecone)
  ↓
[Retrieval API] (/knowledge/search)
  ↓
[LLM Prompt Builder] (contexte + question)
  ↓
[Quality Evaluation] (RAGAS metrics)
```

---

## 🏗️ Architecture des composants

### 1. **Document Loading** (`document_loader.py`)

Extraction de texte depuis différents formats :

```python
# PDF : PyMuPDF (fitz)
pages = load_document("cours.pdf", DocumentType.PDF)
# Output: [{"text": "...", "page_number": 1}, ...]

# DOCX : python-docx
pages = load_document("notes.docx", DocumentType.DOCX)

# PPTX : python-pptx  
pages = load_document("slides.pptx", DocumentType.PPTX)
```

**Stratégies OCR** (configurable dans `.env`):
- `text_only` : Extraction texte pur (défaut, rapide)
- `ocr_raster` : OCR sur les images intégrées (slow)

---

### 2. **Chunking Service** (`chunking_service.py`)

Découpe intelligente en chunks sémantiques :

- ✅ Découpe aux frontières de **paragraphes** (pas au caractère aléatoire)
- ✅ **Overlap** préservé entre chunks (contexte de jonction)
- ✅ Taille configurable (`CHUNK_SIZE=800`, `CHUNK_OVERLAP=100`)
- ✅ Gère les paragraphes géants (découpe au caractère si nécessaire)

```python
chunks = chunk_pages(
    pages=pages,
    course_id="MATH_101",
    chapter_id="Ch_2",
    filename="cours.pdf"
)
# Output: [
#   {"text": "...", "metadata": {"course_id": "MATH_101", "chapter_id": "Ch_2", "page": 1}},
#   ...
# ]
```

---

### 3. **Embedding Service** (`embedding_service.py`)

Génération de vecteurs sémantiques :

**Modèle par défaut:** `intfloat/multilingual-e5-base` (768D, multilingue)

```python
# Query : avec préfixe "query:"
query_emb = embed_query("Comment calculer un déterminant?")

# Passages : avec préfixe "passage:"
chunk_embs = embed_chunks(["Le déterminant est...", "Pour une matrice 2x2..."])
```

**Avantages E5 :**
- Conçu pour la tâche retrieval+ranking
- Multilingue (FR/EN/etc.)
- Pas d'API payante (local)

⚠️ **Attention:** Les préfixes "query:" / "passage:" sont **spécifiques à E5**. Si vous changez de modèle, les supprimer !

---

### 4. **Vector Store** (`chroma_client.py` + `vector_store.py`)

Stockage et recherche vectorielle

**Backends supportés:**

| Backend | Dev | Prod | Scalabilité | Coût |
|---------|-----|------|-------------|------|
| **ChromaDB** | ✅ | ❌ | Faible (local) | Gratuit |
| **Weaviate** | ✅ | ✅ | Haute | Faible |
| **Pinecone** | ✅ | ✅ | Très haute | Modéré |

**Config (.env):**
```bash
# Dev (défaut)
VECTOR_STORE_BACKEND=chromadb
CHROMA_PATH=./chroma_db
CHROMA_COLLECTION=fraudly_knowledge

# Prod Weaviate
VECTOR_STORE_BACKEND=weaviate
WEAVIATE_URL=https://fraudly.weaviate.cloud
WEAVIATE_API_KEY=...

# Prod Pinecone
VECTOR_STORE_BACKEND=pinecone
PINECONE_API_KEY=...
PINECONE_ENV=gcp-starter
```

---

### 5. **Ingestion Pipeline** (`rag_service.py`)

Ororchestration complète du processus d'indexation :

```python
# Option A : À partir d'un fichier
response = ingest_file(
    file_path="./cours.pdf",
    filename="cours.pdf",
    course_id="MATH_101",
    chapter_id="Ch_2",
    doc_type=DocumentType.PDF,
)

# Option B : À partir de bytes (upload, Kafka, S3)
response = ingest_bytes(
    file_bytes=pdf_bytes,
    filename="cours.pdf",
    course_id="MATH_101",
    chapter_id="Ch_2",
    doc_type=DocumentType.PDF,
)

# Result: IngestResponse(chunks_indexed=104, status=OK, ...)
```

**Process interne:**
1. Extract text (load_document)
2. Chunk (chunk_pages)
3. Embed (embed_chunks, batched)
4. Index (collection.add, batched)

---

### 6. **Retrieval API** (`api/knowledge.py`)

Endpoints FastAPI pour les agents IA :

#### `POST /knowledge/search`
```python
POST /knowledge/search
{
  "query": "Comment calculer un déterminant?",
  "course_id": "MATH_101",      # Optionnel
  "chapter_id": "Ch_2",         # Optionnel
  "top_k": 5
}

Response:
{
  "query": "...",
  "chunks": [
    {
      "content": "Le déterminant est...",
      "course_id": "MATH_101",
      "chapter_id": "Ch_2",
      "source_file": "cours.pdf",
      "page": 24,
      "score": 0.847
    },
    ...
  ],
  "total_found": 3
}
```

#### `POST /knowledge/ingest` (Upload)
```python
POST /knowledge/ingest
Content-Type: multipart/form-data
{
  "file": <PDF/DOCX/PPTX>,
  "course_id": "MATH_101",
  "chapter_id": "Ch_2"
}

Response:
{
  "filename": "cours.pdf",
  "chunks_indexed": 104,
  "pages_processed": 45,
  "status": "ok"
}
```

#### `GET /knowledge/stats`
```python
Response:
{
  "total_chunks": 8432,
  "collection_name": "fraudly_knowledge",
  "courses_indexed": ["MATH_101", "CS_201", "LAW_301"]
}
```

#### `GET /knowledge/courses`
```python
Response: ["MATH_101", "CS_201", "LAW_301"]
```

---

### 7. **Kafka Consumer** (`kafka/consumer.py`)

Indexation automatique des ressources uploadées :

**Topic:** `resource_uploaded`
```json
{
  "resource_id": "res_12345",
  "course_id": "MATH_101",
  "chapter_id": "Ch_2",
  "filename": "cours.pdf",
  "file_content_base64": "JVBERi0x...",
  "content_type": "application/pdf"
}
```

**Process:**
1. Consumer écoute `resource_uploaded`
2. Parse le message
3. Indexe automatiquement via `ingest_bytes()`
4. Publie le résultat sur `ai_results` topic

**Config (.env):**
```bash
KAFKA_ENABLED=True
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_GROUP_ID=fraudly-ia-service
KAFKA_TOPIC_RESOURCE_UPLOADED=resource_uploaded
KAFKA_TOPIC_AI_RESULTS=ai_results
```

---

### 8. **S3 Integration** (`services/s3_service.py`)

Stockage cloud des ressources pédagogiques :

```python
from app.services.s3_service import download_document, upload_document

# Télécharger un document S3
file_bytes, content_type = download_document("courses/MATH_101/cours.pdf")

# Indexer le document
from app.services.rag_service import ingest_bytes
result = ingest_bytes(file_bytes, "cours.pdf", "MATH_101", "Ch_2", DocumentType.PDF)

# Uploader un résultat vers S3
s3_url = upload_document("./result.pdf", "results/math_101_results.pdf")
```

**Config (.env):**
```bash
S3_ENABLED=True
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=eu-west-1
S3_BUCKET=fraudly-resources
```

---

### 9. **Quality Evaluation** (`services/rag_evaluation.py`)

Évaluation RAGAS de la qualité du RAG :

```python
from app.services.rag_evaluation import evaluate_rag, RAGMetrics

metrics = evaluate_rag(
    query="Comment calculer un déterminant?",
    retrieved_contexts=["Le déterminant est...", "Pour une matrice 2x2..."],
    llm_response="Pour calculer un déterminant...",
    scores=[0.847, 0.812]  # Optionnel : scores de retrieval
)

# Résultat
print(metrics.to_dict())
# {
#   "faithfulness": 0.85,         # Réponse fidèle au contexte ?
#   "relevancy": 0.83,            # Chunks pertinents à la question ?
#   "answer_relevancy": 0.89,     # Réponse répond à la question ?
#   "context_precision": 0.88,    # % du contexte pertinent ?
#   "overall_score": 0.85         # Score global pondéré
# }
```

**Métriques:**
- **Faithfulness** (30%) : La réponse LLM reste-t-elle fidèle aux chunks fournis ?
- **Relevancy** (30%) : Les chunks retournés sont-ils pertinents à la question ?
- **Answer Relevancy** (20%) : La réponse répond-elle réellement à la question ?
- **Context Precision** (20%) : Quel % du contexte fourni est pertinent ?

---

## 🚀 Déploiement

### Dev (Local)

```bash
# 1. Installation dépendances
pip install -r requirements.txt

# 2. Configuration
cp .env.example .env
# CHUNK_SIZE=800, EMBEDDING_MODEL=intfloat/multilingual-e5-base, VECTOR_STORE_BACKEND=chromadb

# 3. Démarrer le service
python -m uvicorn app.main:app --reload --port 8000

# 4. Tester
curl -X POST http://localhost:8000/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Qu'\''est-ce qu'\''une matrice?", "course_id": "MATH_101", "top_k": 3}'
```

### Prod (Docker Compose)

```bash
# Avec Weaviate
docker-compose up -d weaviate
# Configurer WEAVIATE_URL, WEAVIATE_API_KEY dans .env

# Avec Kafka
docker-compose up -d kafka zookeeper
# Configurer KAFKA_BOOTSTRAP_SERVERS dans .env

# Service IA
docker-compose up -d fraudly-rag-service
```

---

## 📊 Monitoring & Logging

**Logs en production:**

```bash
# Ingestion
[RAG] INGEST START → cours.pdf
[RAG] Pages extraites: 45
[RAG] Chunks générés: 104
[RAG] Indexation ChromaDB → 104 chunks...
[RAG] ✓ cours.pdf | 45 pages | 104 chunks | 33.74s

# Recherche
[RAG] SEARCH 'Qu'est-ce qu'une matrice?' → 3 chunks

# Kafka
[Kafka] Message reçu: res_12345
[Kafka] Indexation cours.pdf (course=MATH_101, chapter=Ch_2)
[Kafka] ✓ Indexation complète → 104 chunks, status=ok
```

---

## 🧪 Exemples d'utilisation

Voir `example_rag_integration.py` :

```bash
python example_rag_integration.py
```

Exemples couverts:
1. **Ingestion** : Charger un PDF
2. **Recherche** : Requête sémantique
3. **Prompt RAG** : Construire le contexte pour le LLM
4. **Évaluation** : Metrics RAGAS
5. **Kafka** : Flow automatique
6. **API** : Endpoints disponibles
7. **S3** : Documents cloud

---

## 🔍 Tests

```bash
# Tests unitaires (tous les services)
pytest tests/test_unit.py -v

# Tests E2E (pipeline complet)
pytest tests/test_e2e.py -v

# Test manuel du pipeline
python test_rag.py
```

---

## 📚 Architecture Agents

Les agents IA utilisent le RAG ainsi:

```python
# Tutor Agent
def tutor_respond(question: str, course_id: str):
    # 1. Rechercher le contexte
    search_result = search(question, course_id, top_k=5)
    
    # 2. Construire le prompt RAG
    prompt = build_rag_prompt(question, search_result.chunks)
    
    # 3. Appeler le LLM
    response = anthropic.messages.create(
        model="claude-3-opus",
        max_tokens=2048,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # 4. Évaluer la qualité (optionnel)
    metrics = evaluate_rag(question, search_result.chunks, response.content)
    
    return response.content
```

---

## 🛠️ Configuration avancée

### Modèles d'embedding

```bash
# Alternative léger (distillé)
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Puissant pour multilingue
EMBEDDING_MODEL=intfloat/multilingual-e5-large

# Spécialisé code/technical
EMBEDDING_MODEL=nomic-ai/nomic-embed-text-v1
```

### Chunking

```bash
CHUNK_SIZE=512      # Petits chunks → recherche précise, plus d'API calls
CHUNK_SIZE=1500     # Grands chunks → moins d'API calls, moins précis
CHUNK_OVERLAP=200   # Plus d'overlap → contexte préservé, coût ↑
```

### Vector Store

```bash
# ChromaDB (compact, local)
VECTOR_STORE_BACKEND=chromadb
CHROMA_PATH=/data/chroma_db

# Weaviate (scalable, auto-scaling)
VECTOR_STORE_BACKEND=weaviate
WEAVIATE_URL=https://fraudly.weaviate.cloud
# Voir: https://weaviate.io/developers/weaviate/installation

# Pinecone (fully managed, expensive)
VECTOR_STORE_BACKEND=pinecone
PINECONE_API_KEY=...
PINECONE_ENV=gcp-starter
```

---

## 🤝 Intégration avec Backend Spring

### Endpoints Spring → IA Service

**POST /api/resources/ingest**
```json
{
  "courseId": "MATH_101",
  "chapterId": "Ch_2",
  "file": "cours.pdf"
}

→ POST /knowledge/ingest
   → ChromaDB indexation
   → 104 chunks stored
```

**POST /api/tutor/ask**
```json
{
  "question": "Comment calculer un déterminant?",
  "courseId": "MATH_101",
  "userId": "user_123"
}

→ POST /knowledge/search (retrieval)
→ LLM prompt build
→ Claude API call
→ Response + evaluation metrics
```

---

## 📖 Références

- **Chunking:** Text-splitting strategy for better embeddings
- **E5 Models:** https://huggingface.co/intfloat/multilingual-e5-base
- **RAGAS:** https://docs.ragas.io/ (RAG Assessment)
- **ChromaDB:** https://docs.trychroma.com/
- **Weaviate:** https://weaviate.io/developers/weaviate/
- **Pinecone:** https://docs.pinecone.io/

---

## 📝 Troubleshooting

### Problème: "No module named 'app'"
**Solution:** Ajouter le projet root à `PYTHONPATH`
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python test_rag.py
```

### Problème: Embedding très lent
**Solution:** Réduire `CHUNK_SIZE` ou utiliser un modèle plus léger
```bash
CHUNK_SIZE=512
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Problème: ChromaDB crash (Windows)
**Solution:** Utiliser fallback en-mémoire
```bash
FRAUDLY_CHROMA_IN_MEMORY=1
```

### Problème: Scores retrieval bas
**Solution:** 
1. Vérifier que les documents sont bien indexés (`GET /knowledge/stats`)
2. Essayer une requête plus spécifique
3. Augmenter `top_k`
4. Vérifier le modèle d'embedding (utiliser E5 pour multilingue)

---

## 📞 Support

Pour les questions sur le RAG pipeline, consultez:
- `app/services/rag_service.py` : Logic d'orchestration
- `app/api/knowledge.py` : Endpoints API
- `tests/test_e2e.py` : Exemples d'utilisation complète
