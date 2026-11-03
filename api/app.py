"""
FastAPI wrapper around the marketing agent.

Endpoints reuse `storage`, `core.run`, and the audience research helpers, so the
HTTP layer holds no agent logic of its own. OpenAPI docs are served at `/docs`.

Set `LOOPMARK_API_KEY` to require an `X-API-Key` header on every request
except `/health`. Leave it unset only when the server is bound to localhost.
"""

from __future__ import annotations

import hmac
import ipaddress
import json
import os
import socket
from datetime import datetime
from typing import Literal
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from pydantic import BaseModel, Field

from models.schemas import AudiencePersona, BusinessProfile
from storage import get_storage
from tools.audience_research import _normalize_url, fetch_site_summary, personas_from_website
from tools.audience_tools import _parse_crm_csv, _parse_crm_json, _summarize_crm_segments

API_KEY_ENV = "LOOPMARK_API_KEY"


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
    url: str


class CRMImportIn(BaseModel):
    data: str
    format: Literal["csv", "json"] = "csv"
    merge: bool = True


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatIn(BaseModel):
    message: str = Field(min_length=1)
    history: list[ChatTurn] = Field(default_factory=list)
    model: str | None = None


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


def _assert_public_url(url: str) -> str:
    """Reject URLs that resolve to private, loopback, or link-local addresses (SSRF guard)."""
    fetch_url = _normalize_url(url)
    parsed = urlparse(fetch_url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise HTTPException(status_code=422, detail="URL must be http(s) with a hostname.")
    try:
        infos = socket.getaddrinfo(parsed.hostname, parsed.port or 443)
    except socket.gaierror:
        raise HTTPException(status_code=422, detail=f"Could not resolve host '{parsed.hostname}'.")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:
            raise HTTPException(status_code=422, detail="URL must point to a public address.")
    return fetch_url


def _to_messages(history: list[ChatTurn]) -> list[BaseMessage]:
    return [
        HumanMessage(content=t.content) if t.role == "user" else AIMessage(content=t.content)
        for t in history
    ]


# ─── app ───────────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title="Loopmark Agent API",
        description="REST API for the open-source LangGraph marketing agent.",
        version="1.0.0",
    )
    secured = [Depends(require_api_key)]

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

    @app.post("/analyze/website", dependencies=secured)
    def analyze_website(body: WebsiteIn) -> dict:
        site = fetch_site_summary(_assert_public_url(body.url))
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

        storage = get_storage()
        existing = storage.load_crm_segments() if body.merge else []
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

    @app.post("/chat", response_model=ChatOut, dependencies=secured)
    def chat(body: ChatIn) -> ChatOut:
        from core.run import run_agent

        result = run_agent(body.message, history=_to_messages(body.history), model=body.model)
        return ChatOut(reply=str(result.reply), intent=result.intent)

    return app


app = create_app()
