import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Union
import logging

logger = logging.getLogger(__name__)

class EmbeddingModel:
    """Handles text embedding operations"""
    
    def __init__(self, model_name: str):
        """Initialize the embedding model"""
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"✅ Loaded embedding model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def encode(self, texts: Union[str, List[str]], normalize: bool = True) -> np.ndarray:
        """
        Encode text(s) into embeddings
        
        Args:
            texts: Single text or list of texts
            normalize: Whether to normalize embeddings
            
        Returns:
            numpy array of embeddings
        """
        if isinstance(texts, str):
            texts = [texts]
        
        # Add passage prefix for better retrieval
        texts = [f"passage: {text}" for text in texts]
        
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=normalize,
            show_progress_bar=False
        )
        
        return embeddings
    
    def encode_query(self, query: str) -> List[float]:
        """
        Encode a query for search
        
        Args:
            query: User query string
            
        Returns:
            List of floats representing the embedding
        """
        embedding = self.encode(query, normalize=True)
        return embedding[0].tolist()

# Singleton instance
_embedding_model = None

def get_embedding_model(config) -> EmbeddingModel:
    """Get or create embedding model instance"""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = EmbeddingModel(config.EMBEDDING_MODEL)
    return _embedding_model