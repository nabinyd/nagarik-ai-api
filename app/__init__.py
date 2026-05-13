from flask import Flask
from flask_cors import CORS
from flasgger import Swagger
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def create_app(config):
    """Application factory pattern"""
    app = Flask(__name__)
    # Enable CORS
    CORS(app, resources={
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    # swagger = Swagger(app)
    
    # Store config in app
    app.config["config"] = config
    
    # Initialize services
    logger.info("Initializing services...")
    
    from app.services.quadrant_services import get_qdrant_service
    from app.models.embedding import get_embedding_model
    from app.models.llm import get_llm_model
    from app.services.rag_services import get_rag_service
    
    qdrant_service = get_qdrant_service(config)
    embedding_model = get_embedding_model(config)
    llm_model = get_llm_model(config)
    rag_service = get_rag_service(config, qdrant_service, embedding_model, llm_model)
    
    # Store services in app config
    app.config["rag_service"] = rag_service
    app.config["qdrant_service"] = qdrant_service
    
    # Register blueprints
    from app.routes.api import api_bp
    app.register_blueprint(api_bp)
    
    logger.info("✅ Application initialized successfully")
    swagger = Swagger(app)
    return app