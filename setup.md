# AI Code Review Agent — Setup Guide

## Prerequisites
- Python 3.10+
- An Anthropic API key (https://console.anthropic.com)
- A GitHub Personal Access Token with `repo` scope

## Installation

```bash
cd ai-code-review-agent

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Set up environment
copy .env.example .env
# Open .env and fill in your API keys
```

## Usage

### Dry run (prints review, does NOT post to GitHub)
```bash
python main.py owner/repo 42
```

### Post review to GitHub
```bash
python main.py owner/repo 42 --post
```

### Example
```bash
python main.py microsoft/vscode 12345
python main.py facebook/react 9999 --post
```

## Output Example
```
============================================================
   AI CODE REVIEW AGENT
   Repo   : owner/repo
   PR     : #42
   Mode   : DRY RUN (print only)
============================================================

[1/4] Fetching PR #42 from owner/repo...
      Found 3 reviewable file(s): ['src/api.py', 'utils/helpers.py', 'tests/test_api.py']

[2/4] Analyzing 3 file(s) with Claude...
      Reviewing [1/3]: src/api.py
      Reviewing [2/3]: utils/helpers.py
      Reviewing [3/3]: tests/test_api.py

[3/4] Generating final review summary...

[4/4] Skipping GitHub post (dry run mode).

============================================================
   FINAL REVIEW
============================================================
## Summary
...

## Verdict
REQUEST_CHANGES — SQL injection risk in api.py line 34
============================================================
```

## GitHub Token Scopes Required
- `repo` (full control of private repositories)  
  OR for public repos only: `public_repo`

## Architecture
```
main.py          CLI entry point
agent.py         LangGraph state graph (4 nodes)
github_tools.py  GitHub API wrapper (PyGithub)
prompts.py       Claude prompts for review
config.py        Environment config
```

## LangGraph Flow
```
fetch_pr → analyze_files → generate_final_review → post_review → END
```
