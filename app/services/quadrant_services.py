
from typing import List, Dict, Any, Optional
import logging

from qdrant_client import QdrantClient, models

logger = logging.getLogger(__name__)


class QdrantService:
    """Qdrant operations with semantic and metadata-based retrieval."""

    def __init__(
        self,
        url: str,
        api_key: str,
        collection_names: Optional[List[str]] = None,
    ):
        self.client = QdrantClient(url=url, api_key=api_key)

        self.collection_names = collection_names or [
            "nagarikai_legal_en",
            "nagarikai_legal_ne",
        ]

        logger.info(
            "Connected to Qdrant. Collections: %s",
            self.collection_names,
        )

    @staticmethod
    def _point_to_source(point, collection_name: str) -> Dict[str, Any]:
        payload = point.payload or {}

        return {
            "content": payload.get("content", ""),
            "metadata": payload.get("metadata") or {},
            "source": (
                payload.get("source")
                or payload.get("source_path", "")
            ),
            "language": payload.get("language", ""),
            "score": (
                float(point.score)
                if getattr(point, "score", None) is not None
                else None
            ),
            "id": str(point.id),
            "collection": collection_name,
        }

    @staticmethod
    def _deduplicate(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate Qdrant points while preserving order."""

        unique = []
        seen = set()

        for item in results:
            key = (
                item.get("collection"),
                item.get("id"),
            )

            if key in seen:
                continue

            seen.add(key)
            unique.append(item)

        return unique

    # --------------------------------------------------
    # SEMANTIC SEARCH
    # --------------------------------------------------

    def search(
        self,
        query_vector: List[float],
        top_k: int = 8,
    ) -> List[Dict[str, Any]]:
        """
        Search each configured collection independently.

        top_k applies to each collection, not the combined
        results. This prevents one language collection from
        consuming the entire retrieval limit.
        """

        all_results = []

        try:
            for collection_name in self.collection_names:
                response = self.client.query_points(
                    collection_name=collection_name,
                    query=query_vector,
                    limit=top_k,
                    with_payload=True,
                )

                for point in response.points:
                    source = self._point_to_source(
                        point,
                        collection_name,
                    )

                    source["retrieval_method"] = "semantic"
                    all_results.append(source)

                logger.info(
                    "Semantic search | collection=%s | results=%d",
                    collection_name,
                    len(response.points),
                )

            all_results.sort(
                key=lambda item: item.get("score") or 0,
                reverse=True,
            )

            return self._deduplicate(all_results)

        except Exception:
            logger.exception("Qdrant semantic search failed")
            raise

    # --------------------------------------------------
    # STRUCTURAL SEARCH: PART
    # --------------------------------------------------

    def search_by_part(
        self,
        part: str,
        max_points_per_collection: int = 1000,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all chunks belonging to a constitutional part.

        Requires payload metadata similar to:
        {
            "metadata": {
                "part": "PART 3"
            }
        }
        """

        results = []

        part_variants = [
            part.upper(),
            part.title(),
            part.lower(),
        ]

        for collection_name in self.collection_names:
            try:
                points, _ = self.client.scroll(
                    collection_name=collection_name,
                    scroll_filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="metadata.part",
                                match=models.MatchAny(
                                    any=part_variants
                                ),
                            )
                        ]
                    ),
                    limit=max_points_per_collection,
                    with_payload=True,
                    with_vectors=False,
                )

                for point in points:
                    source = self._point_to_source(
                        point,
                        collection_name,
                    )

                    source["retrieval_method"] = "structural"
                    source["structural_match"] = {
                        "part": part,
                    }

                    results.append(source)

                logger.info(
                    "Part retrieval | collection=%s | part=%s | results=%d",
                    collection_name,
                    part,
                    len(points),
                )

            except Exception:
                logger.exception(
                    "Part retrieval failed | collection=%s | part=%s",
                    collection_name,
                    part,
                )

        return self._deduplicate(results)

    # --------------------------------------------------
    # STRUCTURAL SEARCH: ARTICLE
    # --------------------------------------------------

    def search_by_article(
        self,
        article_number: int,
        max_points_per_collection: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve chunks associated with an article number.

        Supports metadata fields:
        metadata.article
        metadata.article_number

        The metadata values may be strings or integers.
        """

        results = []

        article_values = [
            str(article_number),
            article_number,
        ]

        for collection_name in self.collection_names:
            try:
                article_filter = models.Filter(
                    should=[
                        models.FieldCondition(
                            key="metadata.article",
                            match=models.MatchAny(any=article_values),
                        ),
                        models.FieldCondition(
                            key="metadata.article_number",
                            match=models.MatchAny(any=article_values),
                        ),
                    ],
                    min_should=1,
                )

                points, _ = self.client.scroll(
                    collection_name=collection_name,
                    scroll_filter=article_filter,
                    limit=max_points_per_collection,
                    with_payload=True,
                    with_vectors=False,
                )

                for point in points:
                    source = self._point_to_source(
                        point,
                        collection_name,
                    )

                    source["retrieval_method"] = "structural"
                    source["structural_match"] = {
                        "article": article_number,
                    }

                    results.append(source)

                logger.info(
                    "Article retrieval | collection=%s | article=%s | results=%d",
                    collection_name,
                    article_number,
                    len(points),
                )

            except Exception:
                logger.exception(
                    "Article retrieval failed | collection=%s | article=%s",
                    collection_name,
                    article_number,
                )

        return self._deduplicate(results)

    # --------------------------------------------------
    # HEALTH CHECK
    # --------------------------------------------------

    def health_check(self) -> bool:
        try:
            response = self.client.get_collections()

            available = {
                collection.name
                for collection in response.collections
            }

            missing = set(self.collection_names) - available

            if missing:
                logger.error(
                    "Missing Qdrant collections: %s",
                    missing,
                )
                return False

            return True

        except Exception:
            logger.exception("Qdrant health check failed")
            return False


# --------------------------------------------------
# SINGLETON
# --------------------------------------------------

_qdrant_service = None


def get_qdrant_service(config) -> QdrantService:
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
