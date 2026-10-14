"""Tests for audience research tools."""

from __future__ import annotations

import httpx

from tools import audience_research
from tools.audience_tools import (
    analyze_website_for_audience,
    get_audience_research_capabilities,
    get_business_profile,
    import_crm_segments,
    list_audience_personas,
    save_audience_persona,
    save_business_profile,
    summarize_crm_segments,
)


SAMPLE_HTML = """
<html>
<head>
  <title>Loopmark | AI Marketing for Small Teams</title>
  <meta name="description" content="Automate social posts and email for SMB marketers.">
</head>
<body>
  <h1>Marketing made simple</h1>
  <h2>For small business owners</h2>
  <p>Save time on content and grow your audience with AI.</p>
</body>
</html>
"""

SAMPLE_CSV = """segment,name,email,company,industry,job_title,tags
Enterprise,Sarah Lee,s@bigco.com,BigCo,SaaS,CTO,automation;content
SMB,John Doe,j@shop.com,ShopCo,Retail,Owner,local;instagram
Enterprise,Mike Chen,m@bigco.com,BigCo,SaaS,VP Marketing,automation
"""


def test_get_audience_research_capabilities():
    result = get_audience_research_capabilities.invoke({})
    assert "website URL" in result
    assert "Meta" in result
    assert "Not available" in result


def test_save_and_get_business_profile():
    save_business_profile.invoke(
        {
            "product_name": "Loopmark",
            "description": "AI marketing assistant",
            "target_audience": "Small business owners",
            "brand_tone": "friendly",
            "website_url": "https://loopmark.example",
        }
    )
    profile = get_business_profile.invoke({})
    assert "Loopmark" in profile
    assert "Small business owners" in profile
    assert "friendly" in profile


def test_import_and_summarize_crm_segments():
    result = import_crm_segments.invoke({"data": SAMPLE_CSV, "format": "csv", "merge": False})
    assert "3 CRM contacts" in result
    assert "Enterprise" in result
    assert "SaaS" in result

    summary = summarize_crm_segments.invoke({})
    assert "Enterprise" in summary
    assert "SMB" in summary
    assert "CRM-derived draft personas" in summary


def test_import_crm_json():
    data = """[
      {"segment": "Trials", "name": "Amy", "email": "a@test.com", "industry": "Healthcare", "job_title": "CMO"}
    ]"""
    result = import_crm_segments.invoke({"data": data, "format": "json", "merge": False})
    assert "Trials" in result
    assert "Healthcare" in result


def test_save_and_list_audience_personas():
    save_audience_persona.invoke(
        {
            "name": "Busy Retail Owner",
            "demographics": "35-50, owns a local shop",
            "pain_points": "no time for marketing",
            "goals": "more foot traffic",
            "preferred_platforms": "instagram, facebook",
            "messaging_angles": "save time, local growth",
            "source": "website",
        }
    )
    listed = list_audience_personas.invoke({})
    assert "Busy Retail Owner" in listed
    assert "instagram" in listed


def test_analyze_website_for_audience(monkeypatch):
    class MockResponse:
        text = SAMPLE_HTML

        def raise_for_status(self):
            return None

    class MockClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, url):
            return MockResponse()

    monkeypatch.setattr("tools.audience_tools.httpx.Client", MockClient)

    result = analyze_website_for_audience.invoke({"url": "loopmark.example"})
    assert "Loopmark" in result
    assert "small business owners" in result.lower() or "Draft personas" in result
    assert "Suggested target audience" in result
    assert "Pain points" in result

    profile = get_business_profile.invoke({})
    assert "loopmark.example" in profile.lower()


def test_analyze_website_fetch_error(monkeypatch):
    def raise_error(*args, **kwargs):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr("tools.audience_tools.httpx.Client", raise_error)

    result = analyze_website_for_audience.invoke({"url": "https://offline.example"})
    assert "Could not fetch website" in result


def test_personas_from_website_uses_llm_when_available(monkeypatch):
    site = {
        "url": "https://loopmark.example",
        "title": "Loopmark | AI Marketing for Small Teams",
        "description": "Automate social posts and email for SMB marketers.",
        "keywords": "marketing, AI",
        "headings": "Marketing made simple",
        "subheadings": "For small business owners",
        "paragraphs": ["Save time on content and grow your audience with AI."],
        "social_links": {},
        "social_presence": [],
    }
    llm_payload = {
        "suggested_target_audience": "SMB marketers adopting AI for social and email",
        "what_they_do": "AI marketing automation for small teams",
        "suggested_business_goals": "Grow audience with less manual posting",
        "suggested_audience_engagement": "Practical how-to posts and email tips",
        "personas": [
            {
                "name": "Time-strapped SMB marketer",
                "description": "Runs social and email for a small team using Loopmark AI tools",
                "demographics": "Marketing lead at 5–50 person company",
                "pain_points": [
                    "Too little time to post consistently",
                    "Hard to keep email and social aligned",
                ],
                "goals": ["Ship campaigns faster", "Reach more qualified leads"],
                "platforms": ["linkedin", "email"],
            },
            {
                "name": "Owner-operator",
                "description": "Small business owner evaluating AI for content",
                "demographics": "Founder, 30–50",
                "pain_points": ["Needs clear ROI before adopting tools"],
                "goals": ["Grow revenue"],
                "platforms": ["instagram", "email"],
            },
        ],
    }

    monkeypatch.setattr(
        audience_research,
        "_analyze_with_llm",
        lambda *args, **kwargs: llm_payload,
    )

    result = audience_research.personas_from_website(site, product_name="Loopmark")
    assert result["analysis_source"] == "llm"
    assert result["research_findings"]["analysis_method"] == "llm"
    assert "SMB marketers" in result["suggested_target_audience"]
    assert "Loopmark" in result["personas"][0]["description"] or "social" in result["personas"][0][
        "description"
    ].lower()
    assert len(result["personas"]) == 2


def test_personas_from_website_falls_back_without_llm(monkeypatch):
    site = {
        "url": "https://loopmark.example",
        "title": "Loopmark | AI Marketing for Small Teams",
        "description": "Automate social posts and email for SMB marketers.",
        "keywords": "",
        "headings": "Marketing made simple",
        "subheadings": "For small business owners",
        "paragraphs": ["Save time on content and grow your audience with AI."],
        "social_links": {},
        "social_presence": [],
    }
    monkeypatch.setattr(audience_research, "_analyze_with_llm", lambda *args, **kwargs: None)

    result = audience_research.personas_from_website(site, product_name="Loopmark")
    assert result["analysis_source"] == "website_content"
    assert result["research_findings"]["analysis_method"] == "website_content"
    assert result["personas"]
    assert result["what_they_do"]
    assert "email" in result["what_they_do"].lower() or "SMB" in result["what_they_do"]


def test_personas_from_website_fallback_on_fetch_error():
    site = {"url": "https://offline.example", "error": "connection refused", "title": "", "description": ""}
    result = audience_research.personas_from_website(site)
    assert result["analysis_source"] == "fallback"
    assert result["research_findings"]["analysis_method"] == "fallback"
    assert result["personas"]


def test_import_crm_invalid_format():
    result = import_crm_segments.invoke({"data": "not-json", "format": "json"})
    assert "Failed to parse CRM data" in result
