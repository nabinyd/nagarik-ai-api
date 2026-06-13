from flask import Blueprint, request, jsonify, current_app
from app.utils.validators import validate_request
import logging
import time

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

# Simple in-memory rate limiting (for production, use Redis)
rate_limit_cache = {}

def rate_limit_check(client_ip: str, limit: int, period: int) -> bool:
    """Check if rate limit is exceeded"""
    current_time = time.time()
    key = f"rate_limit:{client_ip}"
    
    if key not in rate_limit_cache:
        rate_limit_cache[key] = []
    
    # Clean old requests
    rate_limit_cache[key] = [t for t in rate_limit_cache[key] if current_time - t < period]
    
    if len(rate_limit_cache[key]) >= limit:
        return False
    
    rate_limit_cache[key].append(current_time)
    return True

@api_bp.route("/", methods=["GET"])
def home():
    """Health check endpoint"""
    return jsonify({
        "message": "Nagarik AI API running 🚀",
        "status": "healthy",
        "version": "1.0.0"
    })

@api_bp.route("/health", methods=["GET"])
def health():
    """Detailed health check"""
    rag_service = current_app.config["rag_service"]
    health_status = rag_service.health_check()
    
    return jsonify({
        "status": "healthy" if all(health_status.values()) else "degraded",
        "components": health_status
    })

@api_bp.route("/ask", methods=["POST"])
def ask():
    """
    Main query endpoint for Nagarik AI
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: QueryRequest
          required:
            - query
          properties:
            query:
              type: string
              description: The question or query for the AI
              example: "What are my legal rights?"
    responses:
      200:
        description: Successful AI response
      429:
        description: Rate limit exceeded
      400:
        description: Invalid request data
      500:
        description: Internal server error
    """
    start_time = time.time()
    
    # Rate limiting
    client_ip = request.remote_addr
    config = current_app.config["config"]
    
    if not rate_limit_check(client_ip, config.RATE_LIMIT, config.RATE_LIMIT_PERIOD):
        return jsonify({
            "error": "Rate limit exceeded",
            "message": f"Maximum {config.RATE_LIMIT} requests per {config.RATE_LIMIT_PERIOD} seconds"
        }), 429
    
    # Validate request
    data = request.get_json()
    is_valid, error_message = validate_request(data)
    
    if not is_valid:
        return jsonify({"error": error_message}), 400
    
    query = data["query"].strip()
    logger.info(f"Processing query from {client_ip}: {query[:100]}...")
    
    try:
        # Get RAG service from app config
        rag_service = current_app.config["rag_service"]
        
        # Generate answer
        result = rag_service.generate_answer(query)
        
        # Add metadata
        response_time = time.time() - start_time
        result["metadata"] = {
            "response_time_ms": round(response_time * 1000, 2),
            "sources_count": len(result.get("sources", []))
        }
        
        logger.info(f"Query processed in {response_time:.2f}s: {query[:50]}...")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e) if current_app.config["config"].DEBUG else "Please try again later"
        }), 500

# @api_bp.route("/ask", methods=["OPTIONS"])
# def ask_options():
#     """Handle CORS preflight"""
#     return jsonify({}), 200