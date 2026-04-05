"""REST endpoints that proxy to the GitHub API using the session token."""
from fastapi import APIRouter, Depends, HTTPException

from app.deps import github_access_token, get_github_client
from app.github_client import GitHubApiError, GitHubClient
from app.schemas import CreateIssueBody, CreateIssueResponse, IssueSummary

router = APIRouter(tags=["github"])


def _map_github_error(exc: GitHubApiError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.body)


@router.get("/repos")
async def list_repos(
    token: str = Depends(github_access_token),
    gh: GitHubClient = Depends(get_github_client),
) -> list[str]:
    try:
        return await gh.list_user_repos(token)
    except GitHubApiError as e:
        raise _map_github_error(e) from e


@router.get("/list-issues")
async def list_issues(
    owner: str,
    repo: str,
    token: str = Depends(github_access_token),
    gh: GitHubClient = Depends(get_github_client),
) -> list[IssueSummary]:
    try:
        return await gh.list_repo_issues(token, owner, repo)
    except GitHubApiError as e:
        raise _map_github_error(e) from e


@router.post("/create-issue", status_code=201)
async def create_issue(
    payload: CreateIssueBody,
    token: str = Depends(github_access_token),
    gh: GitHubClient = Depends(get_github_client),
) -> CreateIssueResponse:
    try:
        raw = await gh.create_issue(
            token,
            payload.owner,
            payload.repo,
            title=payload.title,
            body=payload.body,
        )
    except GitHubApiError as e:
        raise _map_github_error(e) from e
    return CreateIssueResponse(
        title=str(raw.get("title", payload.title)),
        body=raw.get("body"),
    )
