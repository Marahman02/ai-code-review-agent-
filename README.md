🤖 AI Code Review Agent
An autonomous AI agent that reviews GitHub Pull Requests like a senior developer — identifying bugs, security issues, performance problems, and code quality improvements.
🌐 Live Demo
Try it live — no installation needed:
👉 https://6qerbhls2iponst9xrqkb5.streamlit.app
To use it you need:

A free Anthropic API key from console.anthropic.com
A free GitHub token from github.com/settings/tokens (repo scope)

🛠️ Tech Stack

LangGraph — Agent workflow orchestration
Claude API (Anthropic) — AI-powered code analysis
PyGithub — GitHub API integration
Python — Core language

⚙️ Agent Flow
fetch_pr → analyze_files → generate_final_review → post_review
📋 Features

Detects bugs, logic errors, and security vulnerabilities
Identifies performance issues and bad practices
Posts inline comments directly to GitHub PRs
Supports dry run mode (prints review without posting)
Works on any public GitHub repository

🔧 Setup

Clone the repo and install dependencies
Add your API keys to .env file
Run: streamlit run app.py

🔗 Connect
Built by Mohammed Abdur Rahman — CS Graduate specializing in AI and Data Science

GitHub: github.com/Marahman02
