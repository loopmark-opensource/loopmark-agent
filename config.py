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

    # Data persistence: cwd/data by default so pip-installed CLI writes beside the user.
    # Override via DATA_DIR (e.g. Loopmark monorepo or a shared volume).
    DATA_DIR: str = os.getenv("DATA_DIR", os.path.join(os.getcwd(), "data"))
    COMPLAINTS_FILE: str = os.path.join(DATA_DIR, "complaints.json")
    LEADS_FILE: str = os.path.join(DATA_DIR, "leads.json")
    POSTS_FILE: str = os.path.join(DATA_DIR, "posts.json")
    EMAILS_FILE: str = os.path.join(DATA_DIR, "emails.json")
    BUSINESS_PROFILE_FILE: str = os.path.join(DATA_DIR, "business_profile.json")
    AUDIENCE_PERSONAS_FILE: str = os.path.join(DATA_DIR, "audience_personas.json")
    CRM_SEGMENTS_FILE: str = os.path.join(DATA_DIR, "crm_segments.json")


config = Config()
