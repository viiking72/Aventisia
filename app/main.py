"""FastAPI application factory and middleware."""
import os

from fastapi import FastAPI

from app.config import get_settings
from app.routers import auth, github_routes
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

_TAGS = [
    {
        "name": "auth",
        "description": (
            "**GitHub OAuth 2.0.** **GET /auth/login** → open **authorize_url** → approve on GitHub → "
            "copy **code** from the page you land on → **GET /auth/callback** in Swagger with that **code** "
            "to store the token (same browser session)."
        ),
    },
    {
        "name": "github",
        "description": (
            "Calls the GitHub REST API using the access token stored in your **session cookie** "
            "after OAuth. In Swagger UI, use **Try it out** only **after** you have completed "
            "`/auth/login` in this browser; requests from `/docs` send cookies automatically."
        ),
    },
]

_DESCRIPTION = """
GitHub OAuth connector (session-based).

### Using Swagger UI (`/docs`) on Render

1. **`GET /auth/login`** → open **`authorize_url`** (or **`/auth/login`** in the address bar) → approve on GitHub.
2. Your browser opens **`/auth/callback?code=...`** and shows a **copyable code** (no token stored yet).
3. In **`/docs`**, run **`GET /auth/callback`**, paste the **code**, **Execute** — session is set.
4. Use **github** endpoints; the session cookie is sent from **`/docs`**.

The **`code` is single-use** (GitHub). **Authorize** in Swagger is not used (cookie session).

### Production on Render

Set **`HTTPS_ONLY=true`** so the session cookie is marked `Secure`.
"""


def create_app() -> FastAPI:
    settings = get_settings()
    public_base = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")
    servers = (
        [{"url": public_base, "description": "Public URL"}]
        if public_base
        else None
    )
    app = FastAPI(
        title="GitHub Connector",
        version="1.0.0",
        description=_DESCRIPTION,
        openapi_tags=_TAGS,
        servers=servers,
    )
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        https_only=settings.https_only,
        same_site="lax",
    )
    cors_origins = [
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "").split(",")
        if o.strip()
    ]
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.include_router(auth.router)
    app.include_router(github_routes.router)
    return app


app = create_app()
