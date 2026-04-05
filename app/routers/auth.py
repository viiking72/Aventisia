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


@router.get(
    "/auth/callback",
    include_in_schema=False,
    response_model=None,
)
async def auth_callback(
    request: Request,
    settings: Settings = Depends(get_settings),
    code: str | None = Query(None),
) -> Response:
    """GitHub redirects the browser here—do not call manually from Swagger (codes are single-use)."""
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
        detail: Any = e.detail
        if isinstance(detail, dict) and detail.get("error") == "bad_verification_code":
            detail = (
                "Invalid or already used authorization code. GitHub codes work once and expire "
                "quickly. Use GET /auth/login, approve on GitHub, and let the browser hit this URL "
                "automatically—do not paste the same ?code= into Swagger or call it twice."
            )
        raise HTTPException(status_code=e.status_code, detail=detail) from e

    request.session["github_access_token"] = data["access_token"]

    if _wants_json_response(request):
        return JSONResponse(
            {
                "status": "ok",
                "message": "GitHub connected. Session cookie set; call /repos etc.",
            }
        )
    return RedirectResponse(url="/docs?github=connected", status_code=302)
