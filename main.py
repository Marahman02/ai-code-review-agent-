#!/usr/bin/env python3
"""
AI Code Review Agent
Usage:
  python main.py <owner/repo> <pr_number> [--post]

Examples:
  python main.py microsoft/vscode 12345          # dry run, prints review
  python main.py microsoft/vscode 12345 --post   # posts review to GitHub
"""

import sys
import argparse
from agent import run_review


def main():
    parser = argparse.ArgumentParser(description="AI Code Review Agent")
    parser.add_argument("repo", help="GitHub repo in format owner/repo")
    parser.add_argument("pr_number", type=int, help="Pull request number")
    parser.add_argument(
        "--post",
        action="store_true",
        help="Post the review to GitHub (default: dry run, prints only)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("   AI CODE REVIEW AGENT")
    print(f"   Repo   : {args.repo}")
    print(f"   PR     : #{args.pr_number}")
    print(f"   Mode   : {'POST to GitHub' if args.post else 'DRY RUN (print only)'}")
    print("=" * 60)

    result = run_review(
        repo_name=args.repo,
        pr_number=args.pr_number,
        post_to_github=args.post,
    )

    print("\n" + "=" * 60)
    print("   FINAL REVIEW")
    print("=" * 60)
    print(result["final_review"])

    print("\n" + "=" * 60)
    print(f"   VERDICT : {result['verdict']}")
    print(f"   STATUS  : {result['result']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
