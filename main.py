"""ASGI entrypoint: `uvicorn main:app` (see app.main)."""
from app.main import app

__all__ = ["app"]
