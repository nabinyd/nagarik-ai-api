
import logging
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory rate limiting: suitable for development/staging only.
rate_limit_cache = defaultdict(deque)
rate_limit_lock = Lock()


class QueryRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        description="The question or query for the AI",
        examples=["What are my legal rights?"],
    )


def rate_limit_check(
    client_ip: str, limit: int, period: int
) -> bool:
    current_time = time.time()
    key = f"rate_limit:{client_ip}"

    with rate_limit_lock:
        timestamps = rate_limit_cache[key]

        while timestamps and current_time - timestamps[0] >= period:
            timestamps.popleft()

        if len(timestamps) >= limit:
            return False

        timestamps.append(current_time)
        return True


@router.get("/", tags=["General"])
async def home():
    return {
        "message": "Nagarik AI API running 🚀",
        "status": "healthy",
        "version": "1.0.0",
    }


@router.get("/health", tags=["General"])
async def health(request: Request):
    rag_service = request.app.state.rag_service
    health_status = rag_service.health_check()

    return {
        "status": (
            "healthy"
            if all(health_status.values())
            else "degraded"
        ),
        "components": health_status,
    }


@router.post("/ask", tags=["RAG"])
async def ask(payload: QueryRequest, request: Request):
    start_time = time.perf_counter()

    config = request.app.state.config
    rag_service = request.app.state.rag_service

    client_ip = (
        request.client.host
        if request.client
        else "unknown"
    )

    if not rate_limit_check(
        client_ip,
        config.RATE_LIMIT,
        config.RATE_LIMIT_PERIOD,
    ):
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": (
                    f"Maximum {config.RATE_LIMIT} requests "
                    f"per {config.RATE_LIMIT_PERIOD} seconds"
                ),
            },
        )

    query = payload.query.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail={"error": "Query cannot be empty"},
        )

    logger.info(
        "Processing query from %s: %s...",
        client_ip,
        query[:100],
    )

    try:
        result = rag_service.generate_answer(query)

        response_time = time.perf_counter() - start_time

        result["metadata"] = {
            "response_time_ms": round(
                response_time * 1000, 2
            ),
            "sources_count": len(result.get("sources", [])),
        }

        logger.info(
            "Query processed in %.2f seconds",
            response_time,
        )

        return result

    except Exception:
        logger.exception("RAG request failed")

        if config.DEBUG:
            raise HTTPException(
                status_code=500,
                detail={"error": "Internal server error"},
            )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "Please try again later",
            },
        )
