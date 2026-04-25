"""
Vector Store Configuration — Abstraction pour multiple backends.
Supporte ChromaDB (dev), Weaviate (prod scalable), Pinecone (prod managed).
"""

from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class VectorStoreClient(ABC):
    """Interface abstraite pour les différents backends vectoriels."""
    
    @abstractmethod
    def add(self, ids: List[str], embeddings: List[List[float]], documents: List[str], metadatas: List[Dict]):
        """Ajoute des vecteurs au store."""
        pass
    
    @abstractmethod
    def query(self, query_embedding: List[float], n_results: int = 5, where: Optional[Dict] = None) -> Dict:
        """Recherche par vecteur."""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Nombre total de vecteurs."""
        pass
    
    @abstractmethod
    def delete_collection(self):
        """Supprime la collection."""
        pass


class ChromaDBStore(VectorStoreClient):
    """ChromaDB backend — léger, local, idéal pour dev/test."""
    
    def __init__(self):
        import chromadb
        from chromadb.config import Settings as ChromaSettings
        
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PATH,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"[VectorStore] ChromaDB collection '{settings.CHROMA_COLLECTION}' prête")
    
    def add(self, ids, embeddings, documents, metadatas):
        self.collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    
    def query(self, query_embedding, n_results=5, where=None):
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
    
    def count(self):
        return self.collection.count()
    
    def delete_collection(self):
        self.client.delete_collection(settings.CHROMA_COLLECTION)


class WeaviateStore(VectorStoreClient):
    """Weaviate backend — scalable, cloud, production-grade."""
    
    def __init__(self):
        try:
            import weaviate
            from weaviate.auth import Auth
        except ImportError:
            raise RuntimeError("weaviate client not installed. pip install weaviate-client")
        
        # Config depuis .env
        weaviate_url = getattr(settings, "WEAVIATE_URL", "http://localhost:8080")
        weaviate_api_key = getattr(settings, "WEAVIATE_API_KEY", "")
        
        # Connexion avec ou sans auth
        if weaviate_api_key:
            auth = Auth.api_key(weaviate_api_key)
            self.client = weaviate.Client(url=weaviate_url, auth_client_secret=auth)
        else:
            self.client = weaviate.Client(url=weaviate_url)
        
        self.collection_name = "FraudlyKnowledge"
        
        # Crée la classe si elle n'existe pas
        if not self.client.schema.exists(self.collection_name):
            schema = {
                "class": self.collection_name,
                "vectorizer": "none",  # On fournit nos propres embeddings
                "properties": [
                    {"name": "text", "dataType": ["text"]},
                    {"name": "course_id", "dataType": ["string"]},
                    {"name": "chapter_id", "dataType": ["string"]},
                    {"name": "source_file", "dataType": ["string"]},
                    {"name": "page", "dataType": ["int"]},
                ],
            }
            self.client.schema.create_class(schema)
        
        logger.info(f"[VectorStore] Weaviate collection '{self.collection_name}' prête")
    
    def add(self, ids, embeddings, documents, metadatas):
        for id_, emb, doc, meta in zip(ids, embeddings, documents, metadatas):
            obj = {
                "text": doc,
                **meta,  # course_id, chapter_id, source_file, page
            }
            self.client.data_object.create(
                data_object=obj,
                class_name=self.collection_name,
                uuid=id_,
                vector=emb,
            )
    
    def query(self, query_embedding, n_results=5, where=None):
        """Query Weaviate avec vecteur et filtres métadata."""
        # Construction du filtre Weaviate
        where_filter = None
        if where:
            if "$and" in where:
                where_filter = {"operator": "And", "operands": [
                    {"path": list(f.keys())[0], "operator": "Equal", "valueString": list(f.values())[0]}
                    for f in where["$and"]
                ]}
            else:
                k, v = list(where.items())[0]
                where_filter = {"path": k, "operator": "Equal", "valueString": v}
        
        result = self.client.query.get(self.collection_name, ["text"]).with_near_vector({
            "vector": query_embedding
        }).with_limit(n_results).with_where(where_filter).do()
        
        docs = [obj["text"] for obj in result.get("data", {}).get("Get", {}).get(self.collection_name, [])]
        
        return {
            "documents": [docs],
            "metadatas": [[]],  # TODO: extraire les métadonnées
            "distances": [[0.0] * len(docs)],  # TODO: distance réelle
        }
    
    def count(self):
        agg = self.client.query.aggregate(self.collection_name).with_meta_count().do()
        return agg.get("data", {}).get("Aggregate", {}).get(self.collection_name, [{}])[0].get("meta", {}).get("count", 0)
    
    def delete_collection(self):
        self.client.schema.delete_class(self.collection_name)


class PineconeStore(VectorStoreClient):
    """Pinecone backend — managed vector DB, fully hosted."""
    
    def __init__(self):
        try:
            from pinecone import Pinecone
        except ImportError:
            raise RuntimeError("pinecone client not installed. pip install pinecone-client")
        
        # Config depuis .env
        pinecone_api_key = getattr(settings, "PINECONE_API_KEY", "")
        pinecone_env = getattr(settings, "PINECONE_ENV", "gcp-starter")
        index_name = "fraudly-knowledge"
        
        if not pinecone_api_key:
            raise ValueError("PINECONE_API_KEY manquant dans .env")
        
        self.pc = Pinecone(api_key=pinecone_api_key, environment=pinecone_env)
        self.index = self.pc.Index(index_name)
        
        logger.info(f"[VectorStore] Pinecone index '{index_name}' prêt")
    
    def add(self, ids, embeddings, documents, metadatas):
        vectors = [
            (id_, emb, meta)
            for id_, emb, meta in zip(ids, embeddings, metadatas)
        ]
        self.index.upsert(vectors=vectors)
    
    def query(self, query_embedding, n_results=5, where=None):
        results = self.index.query(
            vector=query_embedding,
            top_k=n_results,
            include_metadata=True,
            filter=where,
        )
        
        docs = [match["metadata"]["text"] for match in results["matches"]]
        metas = [match["metadata"] for match in results["matches"]]
        scores = [match["score"] for match in results["matches"]]
        
        # Convertir scores Pinecone (0-1, plus proche = plus grand) en distances (0-1, plus proche = plus petit)
        distances = [1.0 - s for s in scores]
        
        return {
            "documents": [docs],
            "metadatas": [metas],
            "distances": [distances],
        }
    
    def count(self):
        desc = self.index.describe_index_stats()
        return desc.get("total_vector_count", 0)
    
    def delete_collection(self):
        # Pinecone ne supprime pas facilement ; on peut vider l'index
        logger.warning("[VectorStore] Suppression complète de Pinecone — vider manuellement via console")


def get_vector_store() -> VectorStoreClient:
    """Factory pour instancier le backend vectoriel configuré."""
    backend = getattr(settings, "VECTOR_STORE_BACKEND", "chromadb").lower()
    
    if backend == "weaviate":
        return WeaviateStore()
    elif backend == "pinecone":
        return PineconeStore()
    else:  # chromadb par défaut
        return ChromaDBStore()
