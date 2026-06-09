from github import Github
from config import GITHUB_TOKEN

_gh = Github(GITHUB_TOKEN)


def get_pr_info(repo_name: str, pr_number: int) -> dict:
    repo = _gh.get_repo(repo_name)
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


def get_pr_files(repo_name: str, pr_number: int) -> list[dict]:
    repo = _gh.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    files = []
    for f in pr.get_files():
        files.append({
            "filename": f.filename,
            "status": f.status,       # added, modified, removed
            "additions": f.additions,
            "deletions": f.deletions,
            "patch": f.patch or "",   # the actual diff
        })
    return files


def get_open_prs(repo_name: str) -> list[dict]:
    repo = _gh.get_repo(repo_name)
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
) -> str:
    """
    Post a full review with optional inline comments.
    event: COMMENT | REQUEST_CHANGES | APPROVE
    inline_comments: list of {"path": str, "line": int, "body": str}
    """
    repo = _gh.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    # Build review comments in GitHub format
    review_comments = []
    commit = list(pr.get_commits())[-1]  # latest commit

    for c in inline_comments:
        review_comments.append({
            "path": c["path"],
            "line": c["line"],
            "body": c["body"],
        })

    pr.create_review(
        commit=commit,
        body=body,
        event=event,
        comments=review_comments,
    )
    return f"Review posted successfully on PR #{pr_number}"
