#!/usr/bin/env python3
"""
Nagarik AI - Legal Assistant API
Run with: python run.py
"""

import sys
import os

from flask_cors import CORS


# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import config
from app import create_app

if __name__ == "__main__":
    # Create app instance
    app = create_app(config)

    CORS(
        app,
        origins=["http://localhost:3000"],
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "OPTIONS"]
    )

    
    
    # Run server
    print(f"""
    🚀 Starting Nagarik AI API Server
    📍 Host: {config.HOST}
    🔌 Port: {config.PORT}
    🐛 Debug: {config.DEBUG}
    """)
    
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG,
        use_reloader=True  
    )