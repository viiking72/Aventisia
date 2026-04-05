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
            "**GitHub OAuth 2.0.** In **Swagger**, **Try it out** on **GET /auth/login** returns JSON "
            "with **authorize_url** (no redirect—see github note). Open that URL in the same browser, "
            "then use **github** endpoints. Or open **/auth/login** directly in the address bar for an "
            "immediate redirect."
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

1. In **`/docs`**, run **GET /auth/login** → open **`authorize_url`** in the **same browser** (or visit **`/auth/login`** in the address bar). Approve the app on GitHub.
2. GitHub sends you to **`/auth/callback`** (you are redirected to **`/docs?github=connected`** when login succeeds). Do **not** call `/auth/callback` from Swagger—the `code` is **single-use**; reusing it causes `bad_verification_code`.
3. Use **github** endpoints in **`/docs`** (**Try it out**). The session cookie is sent automatically.

**Authorize** in Swagger is not used (auth is cookie-based). **`/auth/callback` is hidden from this page** on purpose—it is only for GitHub’s redirect.

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
