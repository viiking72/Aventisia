"""Configuration loaded from the environment (no secrets in code)."""
from dataclasses import dataclass
from functools import lru_cache
import os

from dotenv import load_dotenv

load_dotenv()


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


@dataclass(frozen=True)
class Settings:
    session_secret: str
    github_client_id: str
    github_client_secret: str
    github_redirect_uri: str
    https_only: bool


@lru_cache
def get_settings() -> Settings:
    return Settings(
        session_secret=_require_env("SESSION_SECRET"),
        github_client_id=_require_env("GITHUB_CLIENT_ID"),
        github_client_secret=_require_env("GITHUB_CLIENT_SECRET"),
        github_redirect_uri=_require_env("GITHUB_REDIRECT_URI"),
        https_only=os.getenv("HTTPS_ONLY", "").lower() in ("1", "true", "yes"),
    )
