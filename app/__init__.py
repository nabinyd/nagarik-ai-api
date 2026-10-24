
import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

    from app.services.quadrant_services import get_qdrant_service
    from app.models.embedding import get_embedding_model
    from app.models.llm import get_llm_model
    from app.services.rag_services import get_rag_service

    qdrant_service = get_qdrant_service(config)
    embedding_model = get_embedding_model(config)
    llm_model = get_llm_model(config)

    rag_service = get_rag_service(
        config,
        qdrant_service,
        embedding_model,
        llm_model,
    )

    # Store services for access in routes
    app.state.rag_service = rag_service
    app.state.qdrant_service = qdrant_service

    # Register FastAPI routes
    from app.routes.api import router
    app.include_router(router)

    logger.info("Application initialized successfully")

    return app
