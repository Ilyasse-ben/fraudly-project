# Backend-IA

## Stack gratuit retenu (2026)

- LLM principal: Groq (`llama-3.3-70b-versatile`)
- LLM fallback: Google Gemini (`gemini-2.0-flash`)
- Embeddings: HuggingFace (`sentence-transformers/all-MiniLM-L6-v2`)
- Vector DB: ChromaDB local
- Orchestration agents: LangGraph (avec LangChain)

## Variables d'environnement configurees

Configurer les cles API dans `.env`:

- `GROQ_API_KEY`
- `GEMINI_API_KEY`

Les valeurs par defaut appliquees:

- `LLM_PROVIDER=groq`
- `LLM_FALLBACK_PROVIDER=gemini`
- `GROQ_MODEL=llama-3.3-70b-versatile`
- `GEMINI_MODEL=gemini-2.0-flash`
- `EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2`
- `CHROMA_PATH=./chroma_db_miniLM384`
- `CHROMA_COLLECTION=fraudly_knowledge_miniLM384`
- `VECTOR_STORE_BACKEND=chroma`

Modes backend vectoriel:

- `VECTOR_STORE_BACKEND=chroma` (recommande test/prod): ChromaDB persistant (SQLite + index)
- `VECTOR_STORE_BACKEND=simple` (debug uniquement): store JSON local simplifie

## Contrat d'ingestion (Spring -> Backend-IA)

Endpoint principal:

- `POST /knowledge/ingest`

Format attendu (`multipart/form-data`):

- `file` (obligatoire): document a indexer (`pdf`, `docx`, `doc`, `pptx`)
- `course_id` (obligatoire): identifiant du cours
- `chapter_id` (obligatoire): identifiant du chapitre
- `resource_id` (optionnel): identifiant stable de la ressource (UUID ou id metier)
- `version` (optionnel, defaut `v1`): version de la ressource

Regles d'idempotence:

- meme `resource_id` + meme `version` + meme contenu -> pas de reindexation (`idempotent_hit=true`)
- meme `resource_id` + meme `version` + contenu different -> `409 Conflict`
- nouveau `version` (ex: `v2`) -> indexation autorisee

Endpoint de suivi:

- `GET /knowledge/ingest/status/{resource_id}?version=v1`

Exemple de reponse succes:

```json
{
	"resource_id": "res_123",
	"version": "v1",
	"filename": "cours_fraude.pdf",
	"course_id": "fraude-101",
	"chapter_id": "chap-2",
	"pages_processed": 10,
	"chunks_indexed": 42,
	"status": "ok",
	"idempotent_hit": false,
	"message": null
}
```

Exemple de reponse idempotente (rejeu exact):

```json
{
	"resource_id": "res_123",
	"version": "v1",
	"filename": "cours_fraude.pdf",
	"course_id": "fraude-101",
	"chapter_id": "chap-2",
	"pages_processed": 10,
	"chunks_indexed": 42,
	"status": "ok",
	"idempotent_hit": true,
	"message": "Contenu deja indexe pour cette resource/version."
}
```

## Assessment Agent (generation d'evaluations)

Endpoint ajoute:

- `POST /assessment/generate`

Permet de generer des:

- QCM
- Vrai/Faux
- Questions ouvertes

Le professeur peut configurer:

- la difficulte (`facile`, `moyen`, `difficile`)
- le nombre total de questions
- la repartition par type (`qcm_count`, `true_false_count`, `open_count`)
- des consignes pedagogiques additionnelles (`professor_instructions`)
- un chapitre unique (`chapter_id`) ou plusieurs chapitres (`chapter_ids`)

Exemple de payload:

```json
{
	"topic": "Fraude documentaire et techniques de detection",
	"course_id": "fraude-101",
	"chapter_ids": ["chap-2", "chap-3"],
	"difficulty": "difficile",
	"total_questions": 10,
	"qcm_count": 4,
	"true_false_count": 3,
	"open_count": 3,
	"include_explanations": true,
	"professor_instructions": "Couvrir EXIF, incoherences typographiques et verification croisee.",
	"top_k": 8
}
```

Note:

- `chapter_ids` est le format recommande pour couvrir plusieurs chapitres.
- `chapter_id` reste accepte pour compatibilite descendante avec les clients existants.
- si `qcm_count`, `true_false_count` et `open_count` restent a `0`, l'agent applique une repartition automatique.
- si la somme des 3 compteurs est differente de `total_questions`, l'API retourne `400`.