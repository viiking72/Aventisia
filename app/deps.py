"""FastAPI dependencies: auth session and shared services."""
from fastapi import HTTPException, Request, status

from app.github_client import GitHubClient


def get_github_client() -> GitHubClient:
    return GitHubClient()


async def github_access_token(request: Request) -> str:
    token = request.session.get("github_access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Open /auth/login first.",
        )
    return str(token)
