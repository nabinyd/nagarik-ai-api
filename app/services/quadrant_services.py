from qdrant_client import QdrantClient
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class QdrantService:
    """Handles Qdrant vector database operations across languages."""

    def __init__(
        self,
        url: str,
        api_key: str,
        collection_names: List[str] = None,
    ):
        try:
            self.client = QdrantClient(url=url, api_key=api_key)

            self.collection_names = collection_names or [
                "nagarikai_legal_en",
                "nagarikai_legal_ne",
            ]

            logger.info(
                "Connected to Qdrant. Collections: %s",
                self.collection_names,
            )

        except Exception as e:
            logger.error("Failed to initialize Qdrant: %s", e)
            raise

    def search(
        self,
        query_vector: List[float],
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """Search all configured collections and merge the results."""

        try:
            all_results = []

            for collection_name in self.collection_names:
                response = self.client.query_points(
                    collection_name=collection_name,
                    query=query_vector,
                    limit=top_k,
                    with_payload=True,
                )

                for result in response.points:
                    payload = result.payload or {}

                    all_results.append({
                        "content": payload.get("content", ""),
                        "metadata": payload.get("metadata", {}),
                        "source": (
                            payload.get("source")
                            or payload.get("source_path", "")
                        ),
                        "language": payload.get("language", ""),
                        "score": float(result.score),
                        "id": result.id,
                        "collection": collection_name,
                    })

                logger.info(
                    "Collection %s returned %d results",
                    collection_name,
                    len(response.points),
                )

            # Merge and rank results across both languages.
            all_results.sort(
                key=lambda item: item["score"],
                reverse=True,
            )

            final_results = all_results[:top_k]

            logger.info(
                "Combined search returned %d results",
                len(final_results),
            )

            return final_results

        except Exception as e:
            logger.error("Qdrant search failed: %s", e)
            raise

    def health_check(self) -> bool:
        """Check whether Qdrant is accessible."""

        try:
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error("Qdrant health check failed: %s", e)
            return False


# Singleton instance
_qdrant_service = None


def get_qdrant_service(config) -> QdrantService:
    """Get or create Qdrant service instance."""

    global _qdrant_service

    if _qdrant_service is None:
        _qdrant_service = QdrantService(
            url=config.QDRANT_URL,
            api_key=config.QDRANT_API_KEY,
            collection_names=[
                "nagarikai_legal_en",
                "nagarikai_legal_ne",
            ],
        )

    return _qdrant_service