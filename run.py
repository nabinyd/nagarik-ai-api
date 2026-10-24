
"""
Nagarik AI - Legal Assistant API
Run with: uvicorn run:app --host 0.0.0.0 --port 5000 --reload
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import config
from app import create_app

# Create FastAPI application
app: FastAPI = create_app(config)


if __name__ == "__main__":
    import uvicorn

    print(f"""
    Starting Nagarik AI API Server
    Host: {config.HOST}
    Port: {config.PORT}
    Debug: {config.DEBUG}
    Swagger UI: http://localhost:{config.PORT}/docs
    """)

    uvicorn.run(
        "run:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
    )

