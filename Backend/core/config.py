# core/config.py
# AWS-Compatible Configuration

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import List

def get_allowed_origins() -> List[str]:
    """Get allowed CORS origins from environment variable."""
    env_origins = os.getenv(
        "ALLOWED_ORIGINS", 
        "http://localhost:3000,http://127.0.0.1:3000"
    )
    
    origins = [origin.strip() for origin in env_origins.split(",") if origin.strip()]
    print(f"[CORS] Loaded origins: {origins}")
    return origins

def setup_cors(app: FastAPI):
    """Sets up CORS middleware with dynamic origins."""
    allowed_origins = get_allowed_origins()
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,      # Now dynamic!
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=600,
    )