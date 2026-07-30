"""Tests for business profile prompt injection."""

from __future__ import annotations

from prompts.business_context import format_business_context
from prompts.templates import get_posting_prompt
from tools.audience_tools import save_business_profile


def test_format_business_context_empty_when_no_profile():
    assert format_business_context() == ""


def test_format_business_context_includes_saved_profile():
    save_business_profile.invoke(
        {
            "product_name": "Acme Co",
            "target_audience": "SMB founders",
            "brand_tone": "friendly",
        }
    )
    context = format_business_context()
    assert "Acme Co" in context
    assert "SMB founders" in context
    assert "Saved business profile" in context


def test_posting_prompt_includes_business_context():
    save_business_profile.invoke(
        {
            "product_name": "Loopmark",
            "description": "AI marketing assistant",
        }
    )
    prompt = get_posting_prompt()
    system_message = prompt.format_messages(messages=[])[0].content
    assert "Loopmark" in system_message
    assert "AI marketing assistant" in system_message
