"""OAuth login and callback (session stores the GitHub access token)."""
import html
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response

from app.config import Settings, get_settings
from app.oauth import OAuthExchangeError, build_authorize_url, exchange_code_for_token

router = APIRouter(tags=["auth"])


def _wants_json_response(request: Request) -> bool:
    """Swagger / API clients send Accept: application/json; a normal browser tab sends text/html."""
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return False
    return "application/json" in accept


def _callback_code_landing_page(code: str) -> HTMLResponse:
    safe = html.escape(code)
    body = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>GitHub authorization code</title></head>
<body style="font-family:system-ui,sans-serif;max-width:40rem;margin:2rem auto;padding:0 1rem;">
  <h1>Authorization code</h1>
  <p>Copy the value below. In <a href="/docs">/docs</a>, run <strong>GET /auth/callback</strong> and paste it into the <code>code</code> query parameter, then <strong>Execute</strong> to finish login.</p>
  <pre style="background:#f4f4f5;padding:1rem;word-break:break-all;border-radius:6px;">{safe}</pre>
  <p style="color:#666;font-size:0.9rem;">This page does not log you in by itself. Codes expire quickly and work once.</p>
</body>
</html>"""
    return HTMLResponse(content=body)


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
                    "Open authorize_url, approve on GitHub. When redirected back, copy the code "
                    "from the page, then in /docs run GET /auth/callback with that code to finish."
                ),
            }
        )
    return RedirectResponse(url)


@router.get("/auth/callback", response_model=None)
async def auth_callback(
    request: Request,
    settings: Settings = Depends(get_settings),
    code: str | None = Query(
        None,
        description=(
            "Paste the GitHub OAuth `code` from the page you see after approving the app "
            "(browser redirect). Use **Try it out** here with Accept: application/json (Swagger default)."
        ),
    ),
) -> Response:
    """Browser: show the code (no token yet). Swagger: exchange code and set session."""
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")

    # GitHub redirect hits this with a normal browser Accept → show HTML only; user pastes code in Swagger next.
    if not _wants_json_response(request):
        return _callback_code_landing_page(code)

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
                "Invalid or already used authorization code. Codes are single-use. Start again from "
                "GET /auth/login, approve on GitHub, copy the code from the landing page, then run "
                "GET /auth/callback once in Swagger with that code."
            )
        raise HTTPException(status_code=e.status_code, detail=detail) from e

    request.session["github_access_token"] = data["access_token"]
    return JSONResponse(
        {
            "status": "ok",
            "message": "GitHub connected. Session cookie set; call /repos etc.",
        }
    )
