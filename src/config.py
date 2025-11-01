"""Configuration helpers to read provider API keys from environment.

Do NOT hard-code secrets in code. Put keys in a `.env` file or export them in
your shell. Example `.env`:

GROQ_API_KEY=your_groq_key_here
LANGSMITH_API_KEY=your_langsmith_key_here
OPENAI_API_KEY=your_openai_key_here

The project will prefer Groq if `GROQ_API_KEY` is present, otherwise LangSmith,
otherwise OpenAI.
"""
from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # dotenv is optional; environment variables may already be set
    pass


MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("GROQ")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGSMITH")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI")


def preferred_provider() -> str | None:
    if MISTRAL_API_KEY:
        return "mistral"
    if GROQ_API_KEY:
        return "groq"
    if LANGSMITH_API_KEY:
        return "langsmith"
    if OPENAI_API_KEY:
        return "openai"
    return None


BASE_DIR = Path(__file__).resolve().parent.parent
