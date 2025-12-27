"""
Complaint Similarity Service
Uses ChromaDB embeddings to find semantically similar past complaints.
Based on ADR-002: ChromaDB for Similarity Search
"""
import os
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Optional

from app.core.logging import get_logger


class ComplaintSimilarityService:
    """Service for indexing and finding similar complaints using embeddings."""
    
    def __init__(self):
        self.logger = get_logger("complaintops.similarity")
        
        # Initialize ChromaDB Client (same path as RAG)
        db_path = os.path.join(os.getcwd(), "chroma_db")
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Use same embedding function as RAG for consistency
        # Note: For Turkish, consider 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        
        # Separate collection for complaints (not SOPs)
        self.collection = self.client.get_or_create_collection(
            name="complaint_embeddings",
            embedding_function=self.embedding_fn
        )
        
        self.logger.info("ComplaintSimilarityService initialized with collection: complaint_embeddings")
    
    def index_complaint(
        self, 
        complaint_id: str, 
        masked_text: str, 
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Add a complaint to the embedding index.
        
        Args:
            complaint_id: Unique complaint ID (string)
            masked_text: PII-masked complaint text
            metadata: Optional metadata (category, status, created_at)
            
        Returns:
            True if indexed successfully
        """
        try:
            # Upsert to handle re-indexing
            self.collection.upsert(
                ids=[complaint_id],
                documents=[masked_text],
                metadatas=[metadata or {}]
            )
            self.logger.info("Indexed complaint: %s", complaint_id)
            return True
        except Exception as e:
            self.logger.error("Failed to index complaint %s: %s", complaint_id, e)
            return False
    
    def find_similar(
        self, 
        query_text: str, 
        n_results: int = 5, 
        exclude_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Find complaints similar to the query text.
        
        Args:
            query_text: Text to find similar complaints for
            n_results: Maximum number of results to return
            exclude_id: Optional complaint ID to exclude (e.g., self)
            
        Returns:
            List of similar complaints with similarity scores
        """
        try:
            # Query with +1 to allow for self-exclusion
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results + (1 if exclude_id else 0),
                include=["documents", "metadatas", "distances"]
            )
            
            if not results["documents"] or not results["documents"][0]:
                return []
            
            similar = []
            for i, doc in enumerate(results["documents"][0]):
                complaint_id = results["ids"][0][i]
                
                # Skip self
                if exclude_id and complaint_id == exclude_id:
                    continue
                
                # Convert L2 distance to similarity score (0-1 range)
                distance = results["distances"][0][i]
                similarity = 1 / (1 + distance)
                
                # Truncate long text for response
                truncated_text = doc[:200] + "..." if len(doc) > 200 else doc
                
                similar.append({
                    "id": complaint_id,
                    "masked_text": truncated_text,
                    "similarity_score": round(similarity, 2),
                    **(results["metadatas"][0][i] if results["metadatas"][0] else {})
                })
            
            return similar[:n_results]
            
        except Exception as e:
            self.logger.error("Similarity search failed: %s", e)
            return []
    
    def delete_complaint(self, complaint_id: str) -> bool:
        """Remove a complaint from the index."""
        try:
            self.collection.delete(ids=[complaint_id])
            return True
        except Exception as e:
            self.logger.error("Failed to delete complaint %s: %s", complaint_id, e)
            return False
    
    def get_collection_count(self) -> int:
        """Return number of indexed complaints."""
        return self.collection.count()


# Global instance
similarity_service = ComplaintSimilarityService()
