"""Inject saved business profile into agent system prompts."""

from __future__ import annotations

from storage import get_storage

_PROFILE_FIELDS = (
    ("product_name", "Product"),
    ("tagline", "Tagline"),
    ("description", "Description"),
    ("target_audience", "Target audience"),
    ("brand_tone", "Brand tone"),
    ("website_url", "Website"),
    ("default_cta", "Default CTA"),
)


def format_business_context() -> str:
    """
    Return a prompt block for the saved business profile, or empty string if none.

    Safe to call when no profile exists — posting/funnel agents behave as before.
    """
    profile = get_storage().load_business_profile()
    if not profile:
        return ""

    lines = [
        "Saved business profile (use for audience, tone, and CTAs unless the user overrides):",
    ]
    has_content = False
    for key, label in _PROFILE_FIELDS:
        value = (profile.get(key) or "").strip()
        if value:
            has_content = True
            lines.append(f"  {label}: {value}")

    if not has_content:
        return ""

    lines.append("Call get_business_profile for updates; use save_business_profile when the user changes their brand.")
    return "\n".join(lines)
