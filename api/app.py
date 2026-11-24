"""
FastAPI wrapper around the marketing agent.

Endpoints reuse `storage`, `core.run`, and the audience research helpers, so the
HTTP layer holds no agent logic of its own. OpenAPI docs are served at `/docs`.

Set `LOOPMARK_API_KEY` to require an `X-API-Key` header on every request
except `/health`. Leave it unset only when the server is bound to localhost.

Request size and rate limits live in `api/limits.py` (overridable via env).
"""

from __future__ import annotations

import hmac
import json
import os
from datetime import datetime
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from pydantic import BaseModel, Field

from models.schemas import AudiencePersona, BusinessProfile
from storage import get_storage
from tools.audience_research import (
    UnsafeURLError,
    _enrich_site_with_social_crawl,
    assert_public_http_url,
    fetch_site_summary,
    personas_from_website,
)
from tools.audience_tools import _parse_crm_csv, _parse_crm_json, _summarize_crm_segments
from api.limits import (
    ANALYZE_RATE_ENV,
    CHAT_RATE_ENV,
    DEFAULT_ANALYZE_PER_MIN,
    DEFAULT_CHAT_PER_MIN,
    DEFAULT_MAX_BODY,
    MAX_BODY_ENV,
    BodySizeLimitMiddleware,
    RateLimiter,
    env_int,
    rate_limit,
)

API_KEY_ENV = "LOOPMARK_API_KEY"

# Field caps keep a single request from burning model quota or filling DATA_DIR.
MAX_CHAT_HISTORY = 50
MAX_TEXT_CHARS = 8_000
MAX_CRM_ROWS_PER_IMPORT = 5_000
MAX_CRM_ROWS_TOTAL = 50_000


# ─── request / response models ─────────────────────────────────────────────

class ProfileIn(BaseModel):
    product_name: str
    tagline: str = ""
    description: str = ""
    target_audience: str = ""
    brand_tone: str = ""
    website_url: str = ""
    default_cta: str = ""


class PersonaIn(BaseModel):
    name: str
    demographics: str = ""
    pain_points: str = ""
    goals: str = ""
    preferred_platforms: list[str] = Field(default_factory=list)
    messaging_angles: list[str] = Field(default_factory=list)
    source: str = "api"


class WebsiteIn(BaseModel):
    url: str = Field(max_length=2048)


class CRMImportIn(BaseModel):
    data: str
    format: Literal["csv", "json"] = "csv"
    merge: bool = True


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=MAX_TEXT_CHARS)


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=MAX_TEXT_CHARS)
    history: list[ChatTurn] = Field(default_factory=list, max_length=MAX_CHAT_HISTORY)
    model: str | None = Field(default=None, max_length=100)


class ChatOut(BaseModel):
    reply: str
    intent: str


# ─── helpers ───────────────────────────────────────────────────────────────

def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = os.getenv(API_KEY_ENV)
    if not expected:
        return
    if not x_api_key or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header.")


def _to_messages(history: list[ChatTurn]) -> list[BaseMessage]:
    return [
        HumanMessage(content=t.content) if t.role == "user" else AIMessage(content=t.content)
        for t in history
    ]


# ─── app ───────────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    max_body = env_int(MAX_BODY_ENV, DEFAULT_MAX_BODY)
    chat_per_min = env_int(CHAT_RATE_ENV, DEFAULT_CHAT_PER_MIN)
    analyze_per_min = env_int(ANALYZE_RATE_ENV, DEFAULT_ANALYZE_PER_MIN)
    app = FastAPI(
        title="Loopmark Agent API",
        description=(
            "REST API for the open-source LangGraph marketing agent.\n\n"
            f"**Limits:** request bodies up to {max_body:,} bytes (413 above). "
            f"`POST /chat` {chat_per_min}/min and `POST /analyze/website` {analyze_per_min}/min per client (429 with "
            f"`Retry-After`). Chat history up to {MAX_CHAT_HISTORY} turns, {MAX_TEXT_CHARS:,} characters per message. "
            f"CRM import up to {MAX_CRM_ROWS_PER_IMPORT:,} rows per request and {MAX_CRM_ROWS_TOTAL:,} stored."
        ),
        version="1.0.0",
    )
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=max_body)
    secured = [Depends(require_api_key)]
    chat_limited = secured + [Depends(rate_limit(RateLimiter(chat_per_min)))]
    analyze_limited = secured + [Depends(rate_limit(RateLimiter(analyze_per_min)))]

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/profile", dependencies=secured)
    def get_profile() -> dict:
        profile = get_storage().load_business_profile()
        if not profile:
            raise HTTPException(status_code=404, detail="No business profile saved yet.")
        return profile

    @app.put("/profile", dependencies=secured)
    def put_profile(body: ProfileIn) -> dict:
        profile = BusinessProfile(**body.model_dump(), updated_at=datetime.utcnow())
        data = profile.model_dump(mode="json")
        get_storage().save_business_profile(data)
        return data

    @app.get("/personas", dependencies=secured)
    def list_personas(limit: int = Query(default=50, ge=1, le=500)) -> list[dict]:
        return get_storage().load_audience_personas()[:limit]

    @app.post("/personas", status_code=201, dependencies=secured)
    def create_persona(body: PersonaIn) -> dict:
        persona = AudiencePersona(**body.model_dump()).model_dump(mode="json")
        storage = get_storage()
        personas = storage.load_audience_personas()
        personas.append(persona)
        storage.save_audience_personas(personas)
        return persona

    @app.post("/analyze/website", dependencies=analyze_limited)
    def analyze_website(body: WebsiteIn) -> dict:
        try:
            assert_public_http_url(body.url)
            site = fetch_site_summary(body.url)
        except UnsafeURLError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if site.get("error") and "public address" in site["error"].lower():
            raise HTTPException(status_code=422, detail=site["error"])
        site = _enrich_site_with_social_crawl(site)
        profile = get_storage().load_business_profile() or {}
        research = personas_from_website(
            site,
            product_name=profile.get("product_name"),
            existing_audience=profile.get("target_audience"),
        )
        return {"site": site, "research": research}

    @app.post("/crm/import", dependencies=secured)
    def crm_import(body: CRMImportIn) -> dict:
        try:
            contacts = _parse_crm_csv(body.data) if body.format == "csv" else _parse_crm_json(body.data)
        except (ValueError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=422, detail=f"Failed to parse CRM data: {exc}")
        if not contacts:
            raise HTTPException(status_code=422, detail="No contacts found in the provided data.")
        if len(contacts) > MAX_CRM_ROWS_PER_IMPORT:
            raise HTTPException(
                status_code=413, detail=f"Too many rows ({len(contacts)}); limit is {MAX_CRM_ROWS_PER_IMPORT} per import."
            )

        storage = get_storage()
        existing = storage.load_crm_segments() if body.merge else []
        if len(existing) + len(contacts) > MAX_CRM_ROWS_TOTAL:
            raise HTTPException(
                status_code=413,
                detail=f"Import would store more than {MAX_CRM_ROWS_TOTAL} CRM contacts; use merge=false to replace.",
            )
        existing.extend(c.model_dump() for c in contacts)
        storage.save_crm_segments(existing)

        segments: dict[str, int] = {}
        for c in contacts:
            segments[c.segment or "general"] = segments.get(c.segment or "general", 0) + 1
        return {
            "imported": len(contacts),
            "total": len(existing),
            "segments": segments,
            "summary": _summarize_crm_segments(contacts),
        }

    @app.post("/chat", response_model=ChatOut, dependencies=chat_limited)
    def chat(body: ChatIn) -> ChatOut:
        from core.run import run_agent

        result = run_agent(body.message, history=_to_messages(body.history), model=body.model)
        return ChatOut(reply=str(result.reply), intent=result.intent)

    return app


app = create_app()
