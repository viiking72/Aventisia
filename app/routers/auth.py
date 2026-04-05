"""OAuth login and callback (session stores the GitHub access token)."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from app.config import Settings, get_settings
from app.oauth import OAuthExchangeError, build_authorize_url, exchange_code_for_token

router = APIRouter(tags=["auth"])


@router.get("/auth/login")
async def auth_login(settings: Settings = Depends(get_settings)) -> RedirectResponse:
    url = build_authorize_url(
        client_id=settings.github_client_id,
        redirect_uri=settings.github_redirect_uri,
    )
    return RedirectResponse(url)


@router.get("/auth/callback")
async def auth_callback(
    request: Request,
    settings: Settings = Depends(get_settings),
    code: str | None = None,
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
