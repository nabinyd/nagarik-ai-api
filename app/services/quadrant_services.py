from qdrant_client import QdrantClient
from qdrant_client.models import PointIdsList
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class QdrantService:
    """Handles Qdrant vector database operations"""
    
    def __init__(self, url: str, api_key: str, collection_name: str):
        """Initialize Qdrant client"""
        try:
            self.client = QdrantClient(url=url, api_key=api_key)
            self.collection_name = collection_name
            logger.info(f"✅ Connected to Qdrant: {url}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise
    
    def search(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in Qdrant
        """
        try:
            # This returns a QueryResponse object
            response = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=top_k,
                with_payload=True
            )
            
            # FIX: Access the .points attribute which contains the list
            search_results = response.points
            
            logger.info(f"Qdrant search successful: {len(search_results)} results found")
            
            formatted_results = []
            for result in search_results:
                # In query_points, the result is a ScoredPoint object
                formatted_results.append({
                    "content": result.payload.get("content", ""),
                    "metadata": result.payload.get("metadata", {}),
                    "source": result.payload.get("source", ""),
                    "score": result.score,
                    "id": result.id
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            raise
    
    def health_check(self) -> bool:
        """Check if Qdrant is accessible"""
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False

# Singleton instance
_qdrant_service = None

def get_qdrant_service(config) -> QdrantService:
    """Get or create Qdrant service instance"""
    global _qdrant_service
    if _qdrant_service is None:
        _qdrant_service = QdrantService(
            config.QDRANT_URL,
            config.QDRANT_API_KEY,
            config.COLLECTION_NAME
        )
    return _qdrant_service