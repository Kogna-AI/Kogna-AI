# core/config.py
# AWS-Compatible Configuration

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY is not found")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def get_allowed_origins() -> list[str]:
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