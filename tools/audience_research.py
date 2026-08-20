"""Audience research: website analysis and CRM segment persona generation."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlparse

import httpx

_ALLOWED_SCHEMES = frozenset({"http", "https"})
_FETCH_HEADERS = {"User-Agent": "LoopmarkAudienceBot/1.0 (+https://loopmark.io)"}


class _PageMetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.description = ""
        self.h1: list[str] = []
        self._in_title = False
        self._in_h1 = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "title":
            self._in_title = True
        elif tag == "h1":
            self._in_h1 = True
        elif tag == "meta":
            attr = dict(attrs)
            name = (attr.get("name") or attr.get("property") or "").lower()
            if name in ("description", "og:description") and attr.get("content"):
                self.description = attr["content"] or self.description

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        elif tag == "h1":
            self._in_h1 = False

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text:
            return
        if self._in_title:
            self.title += text
        elif self._in_h1 and len(self.h1) < 3:
            self.h1.append(text)


def _strip_html(html: str) -> str:
    text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.I | re.S)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _normalize_url(url: str) -> str:
    url = url.strip()
    parsed = urlparse(url)
    if not parsed.scheme:
        return f"https://{url}"
    return url


def _empty_site_result(url: str, error: str = "") -> dict[str, str]:
    return {
        "url": url,
        "error": error,
        "title": "",
        "description": "",
        "headings": "",
        "snippet": "",
    }


def fetch_site_summary(url: str, timeout: int = 8) -> dict[str, str]:
    fetch_url = _normalize_url(url)
    parsed = urlparse(fetch_url)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        return _empty_site_result(fetch_url, f"Unsupported URL scheme: {parsed.scheme}")

    try:
        with httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers=_FETCH_HEADERS,
        ) as client:
            response = client.get(fetch_url)
            response.raise_for_status()
            raw = response.text[:120_000]
    except httpx.HTTPError as exc:
        return _empty_site_result(fetch_url, str(exc))

    parser = _PageMetaParser()
    parser.feed(raw)

    title = parser.title.strip()
    description = parser.description.strip()
    snippet = _strip_html(raw)[:600]
    if not description and snippet:
        description = snippet[:220]

    return {
        "url": fetch_url,
        "title": title,
        "description": description,
        "headings": " · ".join(parser.h1),
        "snippet": snippet,
    }


def _infer_industry(text: str) -> str:
    lower = text.lower()
    if any(w in lower for w in ("saas", "software", "platform", "api", "cloud")):
        return "B2B software"
    if any(w in lower for w in ("shop", "store", "ecommerce", "retail", "buy")):
        return "e-commerce / retail"
    if any(w in lower for w in ("agency", "marketing", "consulting", "services")):
        return "professional services"
    if any(w in lower for w in ("health", "wellness", "fitness", "clinic")):
        return "health & wellness"
    if any(w in lower for w in ("course", "learn", "education", "training")):
        return "education"
    return "small business"


def personas_from_website(
    site: dict[str, str],
    product_name: str | None = None,
    existing_audience: str | None = None,
) -> dict[str, Any]:
    title = site.get("title") or product_name or "Your business"
    description = site.get("description") or site.get("snippet") or ""
    industry = _infer_industry(f"{title} {description}")
    brand = product_name or title.split("|")[0].split("-")[0].strip()

    primary_name = existing_audience.split(",")[0].strip() if existing_audience else f"Ideal {industry} buyer"

    personas = [
        {
            "name": primary_name,
            "description": f"Primary buyer for {brand} — found via website analysis.",
            "demographics": f"{industry} decision-makers and operators, 28–55, active on LinkedIn and email",
            "pain_points": [
                "Needs clear ROI before adopting new tools",
                "Limited time for marketing and growth tasks",
                "Wants proof from peers in their industry",
            ],
            "goals": [
                "Grow revenue without hiring a full marketing team",
                "Reach qualified prospects consistently",
                "Build trust with audience-fit content",
            ],
            "platforms": ["linkedin", "email", "twitter"],
            "source": "website",
            "source_ref": site.get("url"),
        },
        {
            "name": f"Early adopter — {industry}",
            "description": "Engaged prospect researching solutions like yours.",
            "demographics": "Individual contributors and founders, 25–45, consumes short-form social content",
            "pain_points": [
                "Overwhelmed by generic marketing advice",
                "Unsure which channel reaches their customers",
            ],
            "goals": [
                "Learn quickly from practical tips",
                "Find tools that save time",
            ],
            "platforms": ["twitter", "instagram", "email"],
            "source": "website",
            "source_ref": site.get("url"),
        },
    ]

    site_summary = description[:300] if description else f"We analyzed {site.get('url', 'the site')} for {brand}."
    if site.get("error"):
        site_summary = f"Could not fully fetch site ({site['error']}). Personas inferred from business profile."

    return {
        "personas": personas,
        "suggested_target_audience": existing_audience or f"{industry} owners and growth-focused teams",
        "suggested_business_goals": "Increase qualified leads, grow brand awareness, and improve audience engagement",
        "suggested_audience_engagement": "Educational posts, customer stories, and platform-specific tips that address buyer pain points",
        "site_summary": site_summary,
    }


def personas_from_segment(
    segment: str,
    leads: list[dict[str, str]],
    product_name: str | None = None,
) -> dict[str, Any]:
    companies = [l.get("company", "").strip() for l in leads if l.get("company")]
    stages: dict[str, int] = {}
    for l in leads:
        st = l.get("stage", "awareness")
        stages[st] = stages.get(st, 0) + 1

    top_stage = max(stages, key=stages.get) if stages else "awareness"
    company_sample = ", ".join(sorted(set(companies))[:5]) or "mixed industries"
    brand = product_name or "your business"

    personas = [
        {
            "name": f"{segment} — core segment",
            "description": f"Imported CRM segment with {len(leads)} contacts from {company_sample}.",
            "demographics": f"B2B/B2C contacts in funnel stage '{top_stage}', sourced from CRM import",
            "pain_points": [
                "Needs messaging matched to their funnel stage",
                "Expects relevant follow-up, not generic blasts",
            ],
            "goals": [
                "Move from awareness to purchase",
                "Stay engaged with valuable content",
            ],
            "platforms": ["email", "linkedin"],
            "source": "crm_segment",
            "source_ref": segment,
        },
        {
            "name": f"{segment} — high-intent subset",
            "description": "Contacts further along the pipeline within this segment.",
            "demographics": f"Leads in consideration/intent stages within {segment}",
            "pain_points": ["Needs proof and social validation", "Comparing options before buying"],
            "goals": ["Get a demo or trial", "Understand ROI clearly"],
            "platforms": ["email", "linkedin"],
            "source": "crm_segment",
            "source_ref": segment,
        },
    ]

    return {
        "personas": personas,
        "suggested_target_audience": f"Contacts in CRM segment '{segment}' ({len(leads)} leads)",
        "suggested_business_goals": f"Nurture {segment} toward {top_stage} and convert high-intent leads",
        "suggested_audience_engagement": f"Segment-specific emails and LinkedIn posts referencing {company_sample}",
        "segment_summary": f"{len(leads)} leads · top stage: {top_stage} · companies: {company_sample}",
    }


def research_audience(
    website_url: str | None = None,
    segment: str | None = None,
    segment_leads: list[dict[str, str]] | None = None,
    product_name: str | None = None,
    description: str | None = None,
    existing_audience: str | None = None,
) -> dict[str, Any]:
    if segment and segment_leads:
        result = personas_from_segment(segment, segment_leads, product_name)
        if website_url:
            site = fetch_site_summary(website_url)
            if not site.get("error"):
                result["site_summary"] = site.get("description") or site.get("snippet", "")[:300]
        return result

    url = website_url or ""
    if not url:
        raise ValueError("website_url or segment with leads is required")

    site = fetch_site_summary(url)
    if description and not site.get("description"):
        site["description"] = description

    return personas_from_website(site, product_name, existing_audience)
