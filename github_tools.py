from github import Github
from config import GITHUB_TOKEN


def _client(token: str = "") -> Github:
    return Github(token or GITHUB_TOKEN)


def get_pr_info(repo_name: str, pr_number: int, token: str = "") -> dict:
    repo = _client(token).get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    return {
        "title": pr.title,
        "body": pr.body or "",
        "author": pr.user.login,
        "base_branch": pr.base.ref,
        "head_branch": pr.head.ref,
        "state": pr.state,
        "url": pr.html_url,
    }


def get_pr_files(repo_name: str, pr_number: int, token: str = "") -> list[dict]:
    repo = _client(token).get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    files = []
    for f in pr.get_files():
        files.append({
            "filename": f.filename,
            "status": f.status,
            "additions": f.additions,
            "deletions": f.deletions,
            "patch": f.patch or "",
        })
    return files


def get_open_prs(repo_name: str, token: str = "") -> list[dict]:
    repo = _client(token).get_repo(repo_name)
    prs = []
    for pr in repo.get_pulls(state="open"):
        prs.append({
            "number": pr.number,
            "title": pr.title,
            "author": pr.user.login,
            "url": pr.html_url,
        })
    return prs


def post_pr_review(
    repo_name: str,
    pr_number: int,
    body: str,
    inline_comments: list[dict],
    event: str = "COMMENT",
    token: str = "",
) -> str:
    repo = _client(token).get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    commit = list(pr.get_commits())[-1]

    review_comments = [
        {"path": c["path"], "line": c["line"], "body": c["body"]}
        for c in inline_comments
    ]

    pr.create_review(
        commit=commit,
        body=body,
        event=event,
        comments=review_comments,
    )
    return f"Review posted successfully on PR #{pr_number}"
