from typing import Dict, Any, List
import logging
from app.services.quadrant_services import QdrantService
from app.models.embedding import EmbeddingModel
from app.models.llm import LLMModel

logger = logging.getLogger(__name__)

class RAGService:
    """Handles Retrieval-Augmented Generation operations"""
    
    def __init__(self, 
                 qdrant_service: QdrantService,
                 embedding_model: EmbeddingModel,
                 llm_model: LLMModel,
                 top_k: int = 2):
        """Initialize RAG service"""
        self.qdrant = qdrant_service
        self.embedding = embedding_model
        self.llm = llm_model
        self.top_k = top_k
        
        logger.info("✅ RAG Service initialized")
    
    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        """Retrieve relevant documents from vector store"""
        # Encode query
        query_vector = self.embedding.encode_query(query)
        
        # Search in Qdrant
        results = self.qdrant.search(query_vector, self.top_k)
        
        return results
    
    def generate_prompt(self, query: str, context: str) -> str:
        """Generate the prompt for LLM"""
        prompt = f"""
तपाईं नेपालको कानुनी सहायक (Legal Assistant) हुनुहुन्छ।

प्रश्न: {query}

सन्दर्भ:
{context}

निर्देशनहरू:
- नेपाली भाषामा उत्तर दिनुहोस्
- कानुनी सन्दर्भ (धारा, परिच्छेद) उल्लेख गर्नुहोस्
- यदि जानकारी छैन भने "उपलब्ध छैन" भन्नुहोस्
- स्पष्ट र सटीक उत्तर दिनुहोस्

उत्तर:
"""
        return prompt
    
    def generate_answer(self, query: str) -> Dict[str, Any]:
        try:
            # Step 1: Retrieve relevant documents
            sources = self.retrieve(query)

            if not sources:
                return {
                    "answer": "क्षमा गर्नुहोस्, यस प्रश्नको लागि कुनै सान्दर्भिक जानकारी भेटिएन।",
                    "sources": []
                }

            # Step 2: Build limited context
            MAX_CHUNK_CHARS = 1500
            MAX_CONTEXT_CHARS = 6000

            context_parts = []
            current_size = 0

            for source in sources:
                content = source["content"][:MAX_CHUNK_CHARS]

                if current_size + len(content) > MAX_CONTEXT_CHARS:
                    break

                context_parts.append(content)
                current_size += len(content)

            context = "\n\n---\n\n".join(context_parts)

            logger.info(
                f"Using {len(context_parts)} documents, "
                f"context size={len(context)} chars"
            )

            # Step 3: Generate prompt
            prompt = self.generate_prompt(query, context)

            logger.info(f"Prompt size={len(prompt)} chars")

            # Step 4: Generate answer using LLM
            system_prompt = "तपाईं एक सहायक नेपाली कानुनी विशेषज्ञ हुनुहुन्छ।"

            answer = self.llm.generate(
                prompt,
                system_prompt
            )

            # Step 5: Return result
            return {
                "answer": answer,
                "sources": sources
            }

        except Exception as e:
            logger.error(f"RAG generation failed: {e}")
            raise
        
    def health_check(self) -> Dict[str, bool]:
        """Check health of all components"""
        return {
            "qdrant": self.qdrant.health_check(),
            "embedding": True,  # Always true if initialized
            "llm": True  # Always true if initialized
        }

# Singleton instance
_rag_service = None

def get_rag_service(config, qdrant_service, embedding_model, llm_model) -> RAGService:
    """Get or create RAG service instance"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService(
            qdrant_service,
            embedding_model,
            llm_model,
            config.TOP_K_RESULTS
        )
    return _rag_service