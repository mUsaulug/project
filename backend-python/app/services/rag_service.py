import chromadb
from chromadb.utils import embedding_functions
import os
from typing import List, Dict, Optional

from app.core.logging import get_logger

class RAGManager:
    def __init__(self):
        # Initialize ChromaDB Client
        # Persistent storage in ./chroma_db
        db_path = os.path.join(os.getcwd(), "chroma_db")
        self.client = chromadb.PersistentClient(path=db_path)
        self.default_top_k = int(os.getenv("RAG_TOP_K", "4"))
        self.logger = get_logger("complaintops.rag_manager")
        
        # Use simple default embedding function (all-MiniLM-L6-v2)
        # Note: In production for Turkish, a multilingual model like 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2' is better
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction() 
        
        self.collection = self.client.get_or_create_collection(
            name="complaint_sops",
            embedding_function=self.embedding_fn
        )

    def retrieve(
        self,
        query: str,
        n_results: Optional[int] = None,
        category: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        try:
            resolved_top_k = n_results or self.default_top_k
            where_filter = {"category": category} if category else None
            results = self.collection.query(
                query_texts=[query],
                n_results=resolved_top_k,
                where=where_filter,
                include=["documents", "metadatas"]
            )
            # Flatten results list
            if results["documents"]:
                documents = results["documents"][0]
                metadatas = results["metadatas"][0]
                return [
                    {
                        "snippet": doc,
                        "source": metadata.get("source", "unknown"),
                        "doc_name": metadata.get("doc_name", "unknown"),
                        "chunk_id": metadata.get("chunk_id", "unknown"),
                    }
                    for doc, metadata in zip(documents, metadatas)
                ]
            return []
        except Exception as e:
            self.logger.error("RAG retrieve error: %s", e)
            return []

rag_manager = RAGManager()
