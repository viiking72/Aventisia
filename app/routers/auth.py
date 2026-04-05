"""OAuth login and callback (session stores the GitHub access token)."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, RedirectResponse, Response

from app.config import Settings, get_settings
from app.oauth import OAuthExchangeError, build_authorize_url, exchange_code_for_token

router = APIRouter(tags=["auth"])


def _wants_json_response(request: Request) -> bool:
    """Swagger UI sends Accept: application/json; a browser tab sends text/html first."""
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return False
    return "application/json" in accept


@router.get("/auth/login", response_model=None)
async def auth_login(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> Response:
    url = build_authorize_url(
        client_id=settings.github_client_id,
        redirect_uri=settings.github_redirect_uri,
    )
    # fetch() in Swagger follows 302 to github.com → cross-origin → "Failed to fetch"
    if _wants_json_response(request):
        return JSONResponse(
            {
                "authorize_url": url,
                "message": (
                    "Open authorize_url in this browser to complete GitHub login, "
                    "then return to /docs."
                ),
            }
        )
    return RedirectResponse(url)


@router.get("/auth/callback")
async def auth_callback(
    request: Request,
    settings: Settings = Depends(get_settings),
    code: str | None = Query(
        None,
        description=(
            "OAuth 2.0 authorization code issued by GitHub. It appears in the callback URL as "
            "`?code=...` after you approve the app—do not call this endpoint from Swagger with an "
            "empty code; complete login via **authorize_url** from GET /auth/login instead."
        ),
    ),
) -> dict[str, Any]:
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")

    try:
        data = await exchange_code_for_token(
            client_id=settings.github_client_id,
            client_secret=settings.github_client_secret,
            code=code,
            redirect_uri=settings.github_redirect_uri,
        )
    except OAuthExchangeError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e

    request.session["github_access_token"] = data["access_token"]
    return {
        "status": "ok",
        "message": "GitHub connected. Session cookie set; call /repos etc.",
    }
