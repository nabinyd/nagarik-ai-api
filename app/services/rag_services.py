from typing import Dict, Any, List
import logging

from app.services.quadrant_services import QdrantService
from app.models.embedding import EmbeddingModel
from app.models.llm import LLMModel

logger = logging.getLogger(__name__)


class RAGService:
    """Handles Retrieval-Augmented Generation operations."""

    def __init__(
        self,
        qdrant_service: QdrantService,
        embedding_model: EmbeddingModel,
        llm_model: LLMModel,
        top_k: int = 2,
    ):
        """Initialize RAG service."""
        self.qdrant = qdrant_service
        self.embedding = embedding_model
        self.llm = llm_model
        self.top_k = top_k

        logger.info("RAG Service initialized")

    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        """Retrieve relevant documents from both English and Nepali collections."""
        query_vector = self.embedding.encode_query(query)

        # QdrantService searches both configured collections.
        results = self.qdrant.search(
            query_vector=query_vector,
            top_k=self.top_k,
        )

        return results

    def generate_prompt(self, query: str, context: str) -> str:
        """Generate the prompt for the LLM."""
        return f"""
तपाईं नेपालको कानुनी सहायक (Legal Assistant) हुनुहुन्छ।

प्रश्न: {query}

सन्दर्भ:
{context}

निर्देशनहरू:
- नेपाली भाषामा उत्तर दिनुहोस्।
- सन्दर्भमा उपलब्ध कानुनी जानकारीका आधारमा मात्र उत्तर दिनुहोस्।
- सान्दर्भिक धारा, परिच्छेद, ऐन वा कानुनी प्रावधान उल्लेख गर्नुहोस्।
- सन्दर्भमा आवश्यक जानकारी छैन भने "उपलब्ध छैन" भन्नुहोस्।
- कानुन वा कानुनी सन्दर्भ नबनाउनुहोस्।
- स्पष्ट, सटीक र बुझ्न सजिलो उत्तर दिनुहोस्।

उत्तर:
"""

    def generate_answer(self, query: str) -> Dict[str, Any]:
        """Retrieve relevant context and generate a legal answer."""
        try:
            # Step 1: Retrieve from both language collections.
            sources = self.retrieve(query)

            if not sources:
                return {
                    "answer": (
                        "क्षमा गर्नुहोस्, यस प्रश्नको लागि "
                        "कुनै सान्दर्भिक जानकारी भेटिएन।"
                    ),
                    "sources": [],
                }

            # Step 2: Build limited context.
            MAX_CHUNK_CHARS = 1500
            MAX_CONTEXT_CHARS = 6000

            context_parts = []
            current_size = 0

            for source in sources:
                content = source.get("content", "")[:MAX_CHUNK_CHARS]

                if not content:
                    continue

                if current_size + len(content) > MAX_CONTEXT_CHARS:
                    continue

                language = source.get("language", "unknown")
                source_path = source.get("source", "")

                context_parts.append(
                    f"भाषा: {language}\n"
                    f"स्रोत: {source_path}\n"
                    f"सामग्री:\n{content}"
                )

                current_size += len(content)

            if not context_parts:
                return {
                    "answer": (
                        "क्षमा गर्नुहोस्, यस प्रश्नको लागि "
                        "कुनै सान्दर्भिक जानकारी भेटिएन।"
                    ),
                    "sources": sources,
                }

            context = "\n\n---\n\n".join(context_parts)

            logger.info(
                "Using %d documents, context size=%d chars",
                len(context_parts),
                len(context),
            )

            # Step 3: Generate prompt.
            prompt = self.generate_prompt(query, context)

            logger.info("Prompt size=%d chars", len(prompt))

            # Step 4: Generate answer.
            system_prompt = (
                "तपाईं नेपालको कानुनी जानकारीमा आधारित "
                "सहायक हुनुहुन्छ। उपलब्ध सन्दर्भमा आधारित भएर "
                "उत्तर दिनुहोस् र कानुनी तथ्य नबनाउनुहोस्।"
            )

            answer = self.llm.generate(prompt, system_prompt)

            # Step 5: Return answer and source documents.
            return {
                "answer": answer,
                "sources": sources,
            }

        except Exception as e:
            logger.exception("RAG generation failed: %s", e)
            raise

    def health_check(self) -> Dict[str, bool]:
        """Check the health of all components."""
        return {
            "qdrant": self.qdrant.health_check(),
            "embedding": True,
            "llm": True,
        }


# Singleton instance
_rag_service = None


def get_rag_service(
    config,
    qdrant_service,
    embedding_model,
    llm_model,
) -> RAGService:
    """Get or create the RAG service instance."""
    global _rag_service

    if _rag_service is None:
        _rag_service = RAGService(
            qdrant_service=qdrant_service,
            embedding_model=embedding_model,
            llm_model=llm_model,
            top_k=config.TOP_K_RESULTS,
        )

    return _rag_service