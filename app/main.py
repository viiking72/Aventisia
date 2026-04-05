"""FastAPI application factory and middleware."""
from fastapi import FastAPI

from app.config import get_settings
from app.routers import auth, github_routes
from starlette.middleware.sessions import SessionMiddleware


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="GitHub Connector", version="1.0.0")
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        https_only=settings.https_only,
        same_site="lax",
    )
    app.include_router(auth.router)
    app.include_router(github_routes.router)
    return app


app = create_app()
