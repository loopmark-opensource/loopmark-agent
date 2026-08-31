"""Tests for audience research tools."""

from __future__ import annotations

import httpx

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


def test_import_crm_invalid_format():
    result = import_crm_segments.invoke({"data": "not-json", "format": "json"})
    assert "Failed to parse CRM data" in result
