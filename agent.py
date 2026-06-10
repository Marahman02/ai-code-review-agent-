import json
from typing import TypedDict, Annotated
import operator

from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from config import MODEL
from prompts import SYSTEM_PROMPT, FILE_REVIEW_PROMPT, FINAL_REVIEW_PROMPT
from github_tools import get_pr_info, get_pr_files, post_pr_review


class ReviewState(TypedDict):
    repo_name: str
    pr_number: int
    pr_info: dict
    files: list[dict]
    file_reviews: Annotated[list[dict], operator.add]
    final_review: str
    verdict: str
    post_to_github: bool
    result: str
    # credentials passed through state so nodes are pure functions
    anthropic_api_key: str
    github_token: str


def fetch_pr_node(state: ReviewState) -> dict:
    print(f"\n[1/4] Fetching PR #{state['pr_number']} from {state['repo_name']}...")
    pr_info = get_pr_info(state["repo_name"], state["pr_number"], state["github_token"])
    files = get_pr_files(state["repo_name"], state["pr_number"], state["github_token"])
    files = [f for f in files if f["patch"] and f["status"] != "removed"]
    print(f"      Found {len(files)} reviewable file(s): {[f['filename'] for f in files]}")
    return {"pr_info": pr_info, "files": files}


def analyze_files_node(state: ReviewState) -> dict:
    print(f"\n[2/4] Analyzing {len(state['files'])} file(s) with Claude...")
    llm = ChatAnthropic(
        model=MODEL,
        max_tokens=4096,
        anthropic_api_key=state["anthropic_api_key"],
    )
    file_reviews = []

    for i, file in enumerate(state["files"], 1):
        print(f"      Reviewing [{i}/{len(state['files'])}]: {file['filename']}")
        prompt = FILE_REVIEW_PROMPT.format(
            pr_title=state["pr_info"]["title"],
            pr_body=state["pr_info"]["body"][:500],
            filename=file["filename"],
            status=file["status"],
            patch=file["patch"][:6000],
        )
        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        try:
            review = json.loads(response.content)
        except json.JSONDecodeError:
            review = {
                "filename": file["filename"],
                "summary": "Could not parse structured review.",
                "issues": [],
                "overall": response.content,
            }
        file_reviews.append(review)

    return {"file_reviews": file_reviews}


def generate_final_review_node(state: ReviewState) -> dict:
    print("\n[3/4] Generating final review summary...")
    llm = ChatAnthropic(
        model=MODEL,
        max_tokens=4096,
        anthropic_api_key=state["anthropic_api_key"],
    )

    file_summaries = ""
    for r in state["file_reviews"]:
        file_summaries += f"\n### {r['filename']}\n"
        file_summaries += f"Summary: {r['summary']}\n"
        if r["issues"]:
            for issue in r["issues"]:
                file_summaries += f"- Line {issue['line']} [{issue['severity'].upper()}]: {issue['comment']}\n"
        else:
            file_summaries += "- No issues found.\n"
        file_summaries += f"Overall: {r['overall']}\n"

    prompt = FINAL_REVIEW_PROMPT.format(
        pr_title=state["pr_info"]["title"],
        pr_author=state["pr_info"]["author"],
        file_count=len(state["file_reviews"]),
        file_summaries=file_summaries,
    )

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ])

    final_review = response.content
    verdict = "COMMENT"
    if "REQUEST_CHANGES" in final_review:
        verdict = "REQUEST_CHANGES"
    elif "APPROVE" in final_review:
        verdict = "APPROVE"

    return {"final_review": final_review, "verdict": verdict}


def post_review_node(state: ReviewState) -> dict:
    if not state.get("post_to_github", False):
        print("\n[4/4] Skipping GitHub post (dry run mode).")
        return {"result": "dry_run"}

    print(f"\n[4/4] Posting review to GitHub PR #{state['pr_number']}...")
    inline_comments = []
    for review in state["file_reviews"]:
        for issue in review.get("issues", []):
            inline_comments.append({
                "path": review["filename"],
                "line": issue["line"],
                "body": f"**[{issue['severity'].upper()}]** {issue['comment']}",
            })

    result = post_pr_review(
        repo_name=state["repo_name"],
        pr_number=state["pr_number"],
        body=state["final_review"],
        inline_comments=inline_comments,
        event=state["verdict"],
        token=state["github_token"],
    )
    return {"result": result}


def build_graph() -> StateGraph:
    graph = StateGraph(ReviewState)

    graph.add_node("fetch_pr", fetch_pr_node)
    graph.add_node("analyze_files", analyze_files_node)
    graph.add_node("generate_final_review", generate_final_review_node)
    graph.add_node("post_review", post_review_node)

    graph.set_entry_point("fetch_pr")
    graph.add_edge("fetch_pr", "analyze_files")
    graph.add_edge("analyze_files", "generate_final_review")
    graph.add_edge("generate_final_review", "post_review")
    graph.add_edge("post_review", END)

    return graph.compile()


def run_review(
    repo_name: str,
    pr_number: int,
    post_to_github: bool = False,
    anthropic_api_key: str = "",
    github_token: str = "",
) -> dict:
    from config import ANTHROPIC_API_KEY, GITHUB_TOKEN
    app = build_graph()
    final_state = app.invoke({
        "repo_name": repo_name,
        "pr_number": pr_number,
        "pr_info": {},
        "files": [],
        "file_reviews": [],
        "final_review": "",
        "verdict": "",
        "post_to_github": post_to_github,
        "result": "",
        "anthropic_api_key": anthropic_api_key or ANTHROPIC_API_KEY,
        "github_token": github_token or GITHUB_TOKEN,
    })
    return final_state
