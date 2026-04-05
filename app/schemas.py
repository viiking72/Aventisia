"""Request/response models for the HTTP API."""
from pydantic import BaseModel, Field


class CreateIssueBody(BaseModel):
    owner: str = Field(..., min_length=1)
    repo: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    body: str | None = None
