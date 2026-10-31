
import logging
import sys

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.exceptions import register_exception_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def create_app(config) -> FastAPI:
    """FastAPI application factory."""

    app = FastAPI(
        title="Nagarik AI - Legal Assistant API",
        description="Nagarikai RAG chatbot API",
        version="1.0.0",
    )
    register_exception_handlers(app)

    @app.get("/health", tags=["Health"])
    def health_check() -> JSONResponse:
        try:
            qdrant_connected = app.state.rag_service.get_qdrant().health_check()
        except Exception:
            logger.exception("Qdrant health check failed")
            qdrant_connected = False

        if not qdrant_connected:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "degraded",
                    "qdrant": "unavailable",
                },
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ok",
                "qdrant": "connected",
            },
        )

    # Enable CORS
    app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",  # Allow all origins for development; restrict in production.
        "http://localhost:3000",
        # Add your actual staging frontend origin here.
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

    # Store configuration
    app.state.config = config

    logger.info("Initializing services...")

    from app.services.rag_services import get_rag_service

    rag_service = get_rag_service(config)

    # Store services for access in routes
    app.state.rag_service = rag_service

    # Register FastAPI routes
    from app.api.v1.router import api_router

    app.include_router(api_router, prefix="/api/v1")

    logger.info("Application initialized successfully")

    return app

