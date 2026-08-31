"""
Tools for audience research: business profile, website analysis, CRM import, personas.
"""

from __future__ import annotations

import csv
import io
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from html import unescape
from urllib.parse import urlparse

import httpx
from langchain_core.tools import tool

from models.schemas import AudiencePersona, BusinessProfile, CRMContact
from storage import get_storage
from tools.audience_research import personas_from_segment, personas_from_website

_MAX_WEBSITE_CHARS = 8000
_MAX_BODY_SNIPPET = 4000
_FETCH_TIMEOUT = 15.0

_CRM_FIELD_ALIASES = {
    "segment": ("segment", "segment_name", "audience", "list", "group"),
    "name": ("name", "full_name", "contact_name"),
    "email": ("email", "email_address"),
    "company": ("company", "organization", "account"),
    "industry": ("industry", "vertical", "sector"),
    "job_title": ("job_title", "title", "role", "position"),
    "tags": ("tags", "labels", "interests"),
}


def _strip_html(text: str) -> str:
    cleaned = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.I | re.S)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = unescape(cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def _meta_content(html: str, *names: str) -> str:
    for name in names:
        match = re.search(
            rf'<meta[^>]+(?:name|property)=["\']{re.escape(name)}["\'][^>]+content=["\'](.*?)["\']',
            html,
            re.I | re.S,
        )
        if not match:
            match = re.search(
                rf'<meta[^>]+content=["\'](.*?)["\'][^>]+(?:name|property)=["\']{re.escape(name)}["\']',
                html,
                re.I | re.S,
            )
        if match:
            return _strip_html(match.group(1))
    return ""


def _headings(html: str, tag: str, limit: int = 8) -> list[str]:
    found = re.findall(rf"<{tag}[^>]*>(.*?)</{tag}>", html, re.I | re.S)
    results: list[str] = []
    for item in found:
        text = _strip_html(item)
        if text and text not in results:
            results.append(text)
        if len(results) >= limit:
            break
    return results


def _normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if not parsed.scheme:
        return f"https://{url.strip()}"
    return url.strip()


def _format_list_field(value: str | list[str]) -> str:
    if isinstance(value, list):
        return "; ".join(str(v) for v in value if v)
    return str(value)


def _format_persona_research(research: dict) -> str:
    lines = [
        "",
        "Suggested target audience:",
        f"  {research.get('suggested_target_audience', '(not inferred)')}",
        "",
        "Suggested business goals:",
        f"  {research.get('suggested_business_goals', '(not inferred)')}",
        "",
        "Suggested engagement approach:",
        f"  {research.get('suggested_audience_engagement', '(not inferred)')}",
        "",
        "Draft personas (offer save_audience_persona to persist):",
    ]
    for persona in research.get("personas", []):
        lines.append(f"\n  • {persona.get('name', 'Persona')}")
        if persona.get("description"):
            lines.append(f"    Description: {persona['description']}")
        if persona.get("demographics"):
            lines.append(f"    Demographics: {persona['demographics']}")
        pain_points = persona.get("pain_points")
        if pain_points:
            lines.append(f"    Pain points: {_format_list_field(pain_points)}")
        goals = persona.get("goals")
        if goals:
            lines.append(f"    Goals: {_format_list_field(goals)}")
        platforms = persona.get("platforms")
        if platforms:
            lines.append(f"    Platforms: {_format_list_field(platforms)}")
    return "\n".join(lines)


def _personas_for_crm_contacts(contacts: list[CRMContact]) -> str:
    profile = get_storage().load_business_profile() or {}
    product_name = profile.get("product_name") or None
    by_segment: dict[str, list[dict[str, str]]] = defaultdict(list)
    for contact in contacts:
        by_segment[contact.segment or "general"].append(contact.model_dump())

    lines = ["", "CRM-derived draft personas:"]
    for segment, members in sorted(by_segment.items(), key=lambda x: (-len(x[1]), x[0])):
        research = personas_from_segment(segment, members, product_name)
        lines.append(_format_persona_research(research))
    return "\n".join(lines)


def _map_crm_row(row: dict[str, str]) -> CRMContact:
    normalized = {k.strip().lower().replace(" ", "_"): v.strip() for k, v in row.items() if k}
    mapped: dict[str, str | list[str]] = {}

    for field, aliases in _CRM_FIELD_ALIASES.items():
        for alias in aliases:
            if alias in normalized and normalized[alias]:
                if field == "tags":
                    mapped[field] = [
                        t.strip() for t in re.split(r"[;,|]", normalized[alias]) if t.strip()
                    ]
                else:
                    mapped[field] = normalized[alias]
                break

    return CRMContact(**mapped)  # type: ignore[arg-type]


def _parse_crm_csv(data: str) -> list[CRMContact]:
    reader = csv.DictReader(io.StringIO(data.strip()))
    if not reader.fieldnames:
        raise ValueError("CSV must include a header row.")
    return [_map_crm_row(row) for row in reader]


def _parse_crm_json(data: str) -> list[CRMContact]:
    payload = json.loads(data)
    if not isinstance(payload, list):
        raise ValueError("JSON must be an array of contact objects.")
    contacts: list[CRMContact] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        contacts.append(_map_crm_row({str(k): str(v) for k, v in item.items()}))
    return contacts


def _summarize_crm_segments(contacts: list[CRMContact]) -> str:
    by_segment: dict[str, list[CRMContact]] = defaultdict(list)
    for contact in contacts:
        by_segment[contact.segment or "general"].append(contact)

    lines = [f"Imported {len(contacts)} CRM contacts across {len(by_segment)} segment(s).", ""]
    for segment, members in sorted(by_segment.items(), key=lambda x: (-len(x[1]), x[0])):
        industries = Counter(c.industry for c in members if c.industry)
        titles = Counter(c.job_title for c in members if c.job_title)
        companies = Counter(c.company for c in members if c.company)
        tag_counter: Counter[str] = Counter()
        for member in members:
            tag_counter.update(member.tags)

        lines.append(f"Segment: {segment} ({len(members)} contacts)")
        if industries:
            top = ", ".join(f"{k} ({v})" for k, v in industries.most_common(3))
            lines.append(f"  Top industries: {top}")
        if titles:
            top = ", ".join(f"{k} ({v})" for k, v in titles.most_common(3))
            lines.append(f"  Top job titles: {top}")
        if companies:
            top = ", ".join(f"{k} ({v})" for k, v in companies.most_common(3))
            lines.append(f"  Sample companies: {top}")
        if tag_counter:
            top = ", ".join(f"{k} ({v})" for k, v in tag_counter.most_common(5))
            lines.append(f"  Tags: {top}")
        lines.append("")

    lines.append(
        "Use these segment patterns to draft audience personas and content angles. "
        "The agent should propose 1–3 personas per major segment."
    )
    return "\n".join(lines).strip()


@tool
def get_audience_research_capabilities() -> str:
    """
    Return what audience research features are supported and what is not available.

    Use when the user asks about Meta/LinkedIn/Google Ads audience data, follower analytics,
    or profile viewers.
    """
    return (
        "Audience research capabilities:\n"
        "  ✓ Save and reuse a business / brand profile\n"
        "  ✓ Analyze a website URL to extract positioning signals for persona drafting\n"
        "  ✓ Import CRM contacts/segments from CSV or JSON\n"
        "  ✓ Summarize CRM segments (industries, titles, tags) for persona ideas\n"
        "  ✓ Save and list audience personas for reuse in posts and emails\n\n"
        "Not available in this agent (requires separate ad-platform integrations):\n"
        "  ✗ Meta / Facebook Ads audience insights API\n"
        "  ✗ LinkedIn Campaign Manager or follower analytics API\n"
        "  ✗ Google Ads audience or keyword planner API\n"
        "  ✗ 'Who viewed my profile' or native social follower breakdowns\n\n"
        "Finding your audience here = saved business profile + website analysis + CRM import + AI personas."
    )


@tool
def save_business_profile(
    product_name: str,
    description: str = "",
    tagline: str = "",
    target_audience: str = "",
    brand_tone: str = "",
    website_url: str = "",
    default_cta: str = "",
) -> str:
    """
    Save or update the business / brand profile used for audience and content work.

    Args:
        product_name: Product or company name.
        description: 2–3 sentence description of what the business offers.
        tagline: Short tagline.
        target_audience: Known or draft target audience description.
        brand_tone: e.g. professional, friendly, bold.
        website_url: Company website URL.
        default_cta: Default call-to-action for campaigns.
    """
    profile = BusinessProfile(
        product_name=product_name,
        tagline=tagline,
        description=description,
        target_audience=target_audience,
        brand_tone=brand_tone,
        website_url=website_url,
        default_cta=default_cta,
        updated_at=datetime.utcnow(),
    )
    get_storage().save_business_profile(profile.model_dump())
    return (
        f"Business profile saved for '{product_name}'. "
        "Use get_business_profile before drafting content or personas."
    )


@tool
def get_business_profile() -> str:
    """Return the saved business / brand profile, or note that none exists yet."""
    profile = get_storage().load_business_profile()
    if not profile:
        return (
            "No business profile saved yet. Use save_business_profile or analyze_website_for_audience "
            "to set one up."
        )

    lines = ["Saved business profile:", ""]
    labels = {
        "product_name": "Product",
        "tagline": "Tagline",
        "description": "Description",
        "target_audience": "Target audience",
        "brand_tone": "Brand tone",
        "website_url": "Website",
        "default_cta": "Default CTA",
    }
    for key, label in labels.items():
        value = profile.get(key, "")
        if value:
            lines.append(f"  {label}: {value}")
    return "\n".join(lines)


@tool
def analyze_website_for_audience(url: str) -> str:
    """
    Fetch a business website and extract positioning signals to help draft audience personas.

    Does not connect to ad platforms. Returns page title, description, headings, and text
    snippets for the agent to infer likely customer segments.

    Args:
        url: Website URL, e.g. https://example.com
    """
    fetch_url = _normalize_url(url)
    try:
        with httpx.Client(
            timeout=_FETCH_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": "MarketingAgent/1.0 (audience-research)"},
        ) as client:
            response = client.get(fetch_url)
            response.raise_for_status()
            html = response.text[:_MAX_WEBSITE_CHARS]
    except httpx.HTTPError as exc:
        return f"Could not fetch website '{fetch_url}': {exc}"

    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    title = _strip_html(title_match.group(1)) if title_match else ""
    description = _meta_content(html, "description", "og:description", "twitter:description")
    h1s = _headings(html, "h1")
    h2s = _headings(html, "h2", limit=6)
    body = _strip_html(html)[:_MAX_BODY_SNIPPET]

    lines = [
        f"Website analysis: {fetch_url}",
        "",
        f"Title: {title or '(not found)'}",
        f"Meta description: {description or '(not found)'}",
    ]
    if h1s:
        lines.append("H1 headings: " + " | ".join(h1s))
    if h2s:
        lines.append("H2 headings: " + " | ".join(h2s))
    lines.extend(
        [
            "",
            "Page text snippet:",
            body or "(no readable text extracted)",
        ]
    )

    existing = get_storage().load_business_profile() or {}
    if not existing.get("website_url"):
        existing.update({"website_url": fetch_url, "updated_at": datetime.utcnow().isoformat()})
        if title and not existing.get("product_name"):
            existing["product_name"] = title.split("|")[0].split("-")[0].strip()
        if description and not existing.get("description"):
            existing["description"] = description
        get_storage().save_business_profile(existing)

    site = {
        "url": fetch_url,
        "title": title,
        "description": description,
        "headings": " | ".join(h1s),
        "snippet": body,
    }
    research = personas_from_website(
        site,
        product_name=existing.get("product_name"),
        existing_audience=existing.get("target_audience"),
    )
    lines.append(research.get("site_summary", ""))
    lines.append(_format_persona_research(research))

    return "\n".join(lines)


@tool
def import_crm_segments(data: str, format: str = "csv", merge: bool = True) -> str:
    """
    Import CRM contacts or audience segments from CSV or JSON text.

    CSV headers (flexible names): segment, name, email, company, industry, job_title, tags.
    JSON: array of objects with the same fields.

    Args:
        data: Raw CSV or JSON string pasted by the user or read from an export file.
        format: 'csv' or 'json'.
        merge: If true, append to existing imports; if false, replace them.
    """
    fmt = format.strip().lower()
    try:
        if fmt == "csv":
            contacts = _parse_crm_csv(data)
        elif fmt == "json":
            contacts = _parse_crm_json(data)
        else:
            return "Unknown format. Use 'csv' or 'json'."
    except (ValueError, json.JSONDecodeError) as exc:
        return f"Failed to parse CRM data: {exc}"

    if not contacts:
        return "No contacts found in the provided data."

    storage = get_storage()
    existing = storage.load_crm_segments() if merge else []
    existing.extend(c.model_dump() for c in contacts)
    storage.save_crm_segments(existing)

    summary = _summarize_crm_segments(contacts)
    persona_block = _personas_for_crm_contacts(contacts)
    return f"{summary}{persona_block}\n\nStored {len(existing)} total CRM contacts in the agent library."


@tool
def summarize_crm_segments() -> str:
    """Summarize imported CRM contacts by segment for audience persona research."""
    contacts_raw = get_storage().load_crm_segments()
    if not contacts_raw:
        return (
            "No CRM segments imported yet. Use import_crm_segments with a CSV or JSON export "
            "(columns: segment, name, email, company, industry, job_title, tags)."
        )
    contacts = [CRMContact(**item) for item in contacts_raw]
    summary = _summarize_crm_segments(contacts)
    return f"{summary}{_personas_for_crm_contacts(contacts)}"


@tool
def save_audience_persona(
    name: str,
    demographics: str = "",
    pain_points: str = "",
    goals: str = "",
    preferred_platforms: str = "",
    messaging_angles: str = "",
    source: str = "manual",
) -> str:
    """
    Save an audience persona for reuse in posts, emails, and funnel planning.

    Args:
        name: Persona label, e.g. 'Busy SaaS Founder'.
        demographics: Age, role, location, company size, etc.
        pain_points: Comma-separated pain points.
        goals: Comma-separated goals or jobs-to-be-done.
        preferred_platforms: Comma-separated platforms, e.g. linkedin, twitter.
        messaging_angles: Comma-separated content angles or hooks.
        source: Origin of persona — website, crm, or manual.
    """
    persona = AudiencePersona(
        name=name,
        demographics=demographics,
        pain_points=pain_points,
        goals=goals,
        preferred_platforms=[p.strip() for p in preferred_platforms.split(",") if p.strip()],
        messaging_angles=[a.strip() for a in messaging_angles.split(",") if a.strip()],
        source=source,
    )
    personas = get_storage().load_audience_personas()
    personas.append(persona.model_dump())
    get_storage().save_audience_personas(personas)
    return f"Audience persona saved: '{name}' (ID: {persona.id})."


@tool
def list_audience_personas(limit: int = 10) -> str:
    """List saved audience personas."""
    personas = get_storage().load_audience_personas()[:limit]
    if not personas:
        return (
            "No audience personas saved yet. Use analyze_website_for_audience or summarize_crm_segments, "
            "then save_audience_persona."
        )

    lines = ["Saved audience personas:", ""]
    for persona in personas:
        lines.append(f"[{persona.get('id', '?')}] {persona.get('name', 'Unnamed')} (source: {persona.get('source', 'manual')})")
        if persona.get("demographics"):
            lines.append(f"  Demographics: {persona['demographics']}")
        if persona.get("pain_points"):
            lines.append(f"  Pain points: {persona['pain_points']}")
        if persona.get("goals"):
            lines.append(f"  Goals: {persona['goals']}")
        platforms = persona.get("preferred_platforms") or []
        if platforms:
            lines.append(f"  Platforms: {', '.join(platforms)}")
        angles = persona.get("messaging_angles") or []
        if angles:
            lines.append(f"  Messaging angles: {', '.join(angles)}")
        lines.append("")
    return "\n".join(lines).strip()


AUDIENCE_TOOLS = [
    get_audience_research_capabilities,
    save_business_profile,
    get_business_profile,
    analyze_website_for_audience,
    import_crm_segments,
    summarize_crm_segments,
    save_audience_persona,
    list_audience_personas,
]
