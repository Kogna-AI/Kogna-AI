# Re-export app so "uvicorn api:app" works (uses main app)
from main import app

__all__ = ["app"]
