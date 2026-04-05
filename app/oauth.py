"""GitHub OAuth 2.0 authorize URL and authorization-code exchange."""
from typing import Any
from urllib.parse import urlencode

import httpx

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"

DEFAULT_SCOPES = "repo read:user"


class OAuthExchangeError(Exception):
    """Token endpoint returned an error or unexpected payload."""

    def __init__(self, detail: Any, *, status_code: int = 400) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(str(detail))


def build_authorize_url(*, client_id: str, redirect_uri: str, scope: str = DEFAULT_SCOPES) -> str:
    q = urlencode({"client_id": client_id, "redirect_uri": redirect_uri, "scope": scope})
    return f"{GITHUB_AUTH_URL}?{q}"


async def exchange_code_for_token(
    *,
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
    timeout: float = 30.0,
) -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
            },
            timeout=timeout,
        )
    try:
        data = response.json()
    except ValueError:
        raise OAuthExchangeError(response.text, status_code=502) from None
    if response.status_code != 200 or "error" in data:
        raise OAuthExchangeError(data)
    if "access_token" not in data:
        raise OAuthExchangeError(data)
    return data
