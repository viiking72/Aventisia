"""Request/response models for the HTTP API."""
from pydantic import BaseModel, Field


class IssueSummary(BaseModel):
    """Subset of GitHub issue fields exposed by list-issues."""

    number: int
    title: str
    body: str | None = None


class CreateIssueBody(BaseModel):
    owner: str = Field(..., min_length=1)
    repo: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    body: str | None = None


class CreateIssueResponse(BaseModel):
    """Confirmation payload returned by POST /create-issue (not the full GitHub issue)."""

    created: bool = True
    title: str
    body: str | None = None
