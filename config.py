from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))

    # LangSmith
    LANGCHAIN_TRACING_V2: bool = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "marketing-agent")

    # Data persistence
    DATA_DIR: str = os.path.join(os.path.dirname(__file__), "data")
    COMPLAINTS_FILE: str = os.path.join(DATA_DIR, "complaints.json")
    LEADS_FILE: str = os.path.join(DATA_DIR, "leads.json")
    POSTS_FILE: str = os.path.join(DATA_DIR, "posts.json")


config = Config()
