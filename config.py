import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
MODEL = "claude-sonnet-4-6"

if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY is not set in your .env file")
if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN is not set in your .env file")
