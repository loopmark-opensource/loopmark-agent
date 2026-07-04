"""
Dedicated Email Marketing tools.

Covers: campaign drafting, drip sequences, A/B subject lines,
plain-text conversion, and an email campaign library.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta

from langchain_core.tools import tool

from config import config


# ─── helpers ───────────────────────────────────────────────────────────────

EMAIL_FILE = os.path.join(config.DATA_DIR, "emails.json")


def _load_emails() -> list[dict]:
    os.makedirs(config.DATA_DIR, exist_ok=True)
    if not os.path.exists(EMAIL_FILE):
        return []
    with open(EMAIL_FILE) as f:
        return json.load(f)


def _save_emails(data: list[dict]) -> None:
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(EMAIL_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


# ─── tools ─────────────────────────────────────────────────────────────────

@tool
def draft_email_campaign(
    campaign_name: str,
    subject_line: str,
    goal: str,
    audience: str,
    key_message: str,
    cta_text: str,
    cta_url: str = "",
    tone: str = "professional",
) -> str:
    """
    Draft a full marketing email campaign (subject line + body).
    The LLM writes the email body based on the inputs provided.

    Args:
        campaign_name: Internal name for this campaign.
        subject_line: The email subject line (keep ≤50 chars for best open rates).
        goal: Campaign goal, e.g. 'product launch', 'flash sale', 'newsletter'.
        audience: Target audience description, e.g. 'existing customers', 'cold leads'.
        key_message: The single most important thing the reader should take away.
        cta_text: Call-to-action button text, e.g. 'Shop Now', 'Book a Demo'.
        cta_url: URL the CTA links to (optional).
        tone: Writing tone — professional, friendly, urgent, inspirational.

    Returns:
        A structured email brief for the LLM to write the full email copy.
    """
    brief = (
        f"Write a marketing email with the following brief:\n\n"
        f"Campaign: {campaign_name}\n"
        f"Goal: {goal}\n"
        f"Audience: {audience}\n"
        f"Subject line: {subject_line}\n"
        f"Key message: {key_message}\n"
        f"CTA: {cta_text}" + (f" → {cta_url}" if cta_url else "") + "\n"
        f"Tone: {tone}\n\n"
        f"Structure:\n"
        f"1. Preheader text (1 sentence, max 85 chars)\n"
        f"2. Greeting line\n"
        f"3. Opening hook (1–2 sentences)\n"
        f"4. Body (2–3 short paragraphs)\n"
        f"5. CTA block\n"
        f"6. Sign-off\n\n"
        f"Guidelines: Subject ≤50 chars. Body paragraphs ≤60 words each. "
        f"Single CTA only. Personalise with {{first_name}} placeholder."
    )
    return brief


@tool
def save_email_campaign(
    campaign_name: str,
    subject_line: str,
    preheader: str,
    body: str,
    cta_text: str,
    cta_url: str = "",
    audience: str = "",
    scheduled_date: str = "",
) -> str:
    """
    Save a completed email campaign to the email library.

    Args:
        campaign_name: Internal campaign name.
        subject_line: Email subject line.
        preheader: Preview text shown in the inbox.
        body: Full email body text.
        cta_text: Call-to-action button label.
        cta_url: CTA link URL.
        audience: Target audience segment.
        scheduled_date: ISO date string for send date (e.g. 2026-07-15).

    Returns:
        Confirmation with the campaign ID.
    """
    campaign = {
        "id": f"EMAIL-{int(datetime.utcnow().timestamp())}",
        "campaign_name": campaign_name,
        "subject_line": subject_line,
        "preheader": preheader,
        "body": body,
        "cta_text": cta_text,
        "cta_url": cta_url,
        "audience": audience,
        "character_count": len(body),
        "scheduled_date": scheduled_date or "",
        "status": "scheduled" if scheduled_date else "draft",
        "created_at": datetime.utcnow().isoformat(),
    }
    emails = _load_emails()
    emails.append(campaign)
    _save_emails(emails)
    return f"Email campaign saved. ID: {campaign['id']}  |  Status: {campaign['status']}"


@tool
def generate_ab_subject_lines(
    topic: str,
    goal: str,
    count: int = 3,
) -> str:
    """
    Generate A/B test variants for an email subject line.

    Args:
        topic: What the email is about (e.g. 'summer sale', 'product launch').
        goal: The email goal (e.g. 'drive clicks', 'increase opens', 're-engage').
        count: Number of variants to generate (2–5).

    Returns:
        A brief for the LLM to write subject line variants with rationale.
    """
    count = max(2, min(5, count))
    return (
        f"Generate {count} A/B subject line variants for an email about '{topic}'.\n"
        f"Goal: {goal}\n\n"
        f"For each variant, use a DIFFERENT psychological trigger:\n"
        f"  - Curiosity gap (e.g. 'You won't believe what we...')\n"
        f"  - Urgency/scarcity (e.g. 'Only 24 hours left...')\n"
        f"  - Personalisation (e.g. 'Hey {{first_name}}, this is for you')\n"
        f"  - Benefit-led (e.g. 'Save 30% on your next order')\n"
        f"  - Question (e.g. 'Ready to double your results?')\n\n"
        f"Rules:\n"
        f"  - Each subject line ≤50 characters\n"
        f"  - No spam trigger words (FREE!, 100%%, Act Now)\n"
        f"  - Include a preheader suggestion for each\n\n"
        f"Format as a numbered list: Subject | Preheader | Trigger used | Why it works"
    )


@tool
def build_drip_sequence(
    sequence_name: str,
    trigger: str,
    audience: str,
    goal: str,
    num_emails: int = 5,
) -> str:
    """
    Generate a drip email sequence plan (automated nurture series).

    Args:
        sequence_name: Name for this sequence (e.g. 'New Lead Welcome').
        trigger: What starts the sequence (e.g. 'user signs up', 'downloaded lead magnet').
        audience: Who receives this sequence.
        goal: What the sequence should achieve (e.g. 'convert to paid', 'onboard user').
        num_emails: Number of emails in the sequence (3–10).

    Returns:
        A day-by-day drip sequence plan with email briefs.
    """
    num_emails = max(3, min(10, num_emails))

    send_delays = [0, 2, 4, 7, 10, 14, 18, 21, 25, 30][:num_emails]

    lines = [
        f"Drip Sequence: {sequence_name}",
        f"Trigger: {trigger}",
        f"Audience: {audience}",
        f"Goal: {goal}",
        f"Emails: {num_emails}",
        "",
        "=" * 60,
        "",
        "Generate a full plan for each email below. For each email provide:",
        "  - Day sent (relative to trigger)",
        "  - Subject line (≤50 chars)",
        "  - Preheader (≤85 chars)",
        "  - Purpose / focus",
        "  - Key message (1 sentence)",
        "  - CTA",
        "",
    ]

    purposes = [
        "Welcome & set expectations",
        "Deliver value / educational content",
        "Social proof (case study or testimonial)",
        "Address top objection",
        "Soft pitch / introduce the offer",
        "Urgency / limited-time offer",
        "Follow-up on non-openers",
        "Feature highlight",
        "Customer success story",
        "Final CTA / last chance",
    ]

    for i, (day, purpose) in enumerate(zip(send_delays, purposes[:num_emails]), 1):
        lines.append(f"Email {i} — Day {day}")
        lines.append(f"  Purpose: {purpose}")
        lines.append(f"  Write subject, preheader, focus, key message, and CTA for this email.")
        lines.append("")

    return "\n".join(lines)


@tool
def convert_to_plain_text(html_or_rich_body: str) -> str:
    """
    Convert a rich HTML or formatted email body to clean plain-text fallback.

    Args:
        html_or_rich_body: The HTML or richly formatted email content.

    Returns:
        Instructions for the LLM to produce a clean plain-text version.
    """
    return (
        f"Convert the following email body to a clean plain-text version:\n\n"
        f"{html_or_rich_body}\n\n"
        f"Rules for plain text:\n"
        f"  - Remove all HTML tags\n"
        f"  - Replace bullet points with '-'\n"
        f"  - Replace CTA buttons with: CTA: [text] → [url]\n"
        f"  - Keep paragraphs separated by a blank line\n"
        f"  - Max line width 72 characters\n"
        f"  - Preserve all personalisation placeholders like {{first_name}}"
    )


@tool
def list_email_campaigns(status: str = "all", limit: int = 10) -> str:
    """
    List saved email campaigns from the library.

    Args:
        status: Filter by 'draft', 'scheduled', 'sent', or 'all'.
        limit: Maximum number of campaigns to return.

    Returns:
        Formatted list of campaigns.
    """
    emails = _load_emails()

    if status != "all":
        emails = [e for e in emails if e.get("status") == status.lower()]

    emails = emails[:limit]
    if not emails:
        return "No email campaigns found."

    lines = []
    for e in emails:
        lines.append(
            f"[{e['id']}] [{e['status'].upper()}] '{e['subject_line']}' "
            f"→ {e.get('audience', 'all')} | Scheduled: {e.get('scheduled_date', 'not set')}"
        )
    return "\n".join(lines)


@tool
def get_email_best_practices(category: str = "general") -> str:
    """
    Return email marketing best practices for a specific area.

    Args:
        category: One of 'general', 'subject_lines', 'deliverability',
                  'design', 'cta', 'timing', 'segmentation'.

    Returns:
        A checklist of best practices.
    """
    practices = {
        "general": [
            "Single goal per email — one message, one CTA.",
            "Personalise subject line and greeting at minimum.",
            "Mobile-first: 60%+ of emails are opened on mobile.",
            "Keep body copy scannable: short paragraphs, bullets, bold key points.",
            "Always include an unsubscribe link (legal requirement).",
            "Test before sending: check rendering on Gmail, Outlook, Apple Mail.",
        ],
        "subject_lines": [
            "Keep it under 50 characters (40–50 is the sweet spot).",
            "Front-load the most important word — don't bury it.",
            "Avoid ALL CAPS and excessive punctuation!!!",
            "A/B test every campaign — minimum 2 variants.",
            "Use numbers when possible ('5 ways to...', 'Save 20%').",
            "Create curiosity without being clickbait.",
        ],
        "deliverability": [
            "Authenticate your domain with SPF, DKIM, and DMARC.",
            "Warm up new sending domains gradually.",
            "Maintain a bounce rate below 2% and spam rate below 0.1%.",
            "Clean your list every 3–6 months — remove hard bounces.",
            "Never buy email lists.",
            "Use a dedicated sending IP for volumes >100k/month.",
        ],
        "design": [
            "Max width 600px for email clients.",
            "Use system-safe fonts or web-safe fallbacks.",
            "Alt text on every image — many clients block images by default.",
            "CTA button: min 44×44px tap target, high contrast colour.",
            "Plain-text fallback is required for deliverability.",
            "Dark mode support: test your email in dark mode.",
        ],
        "cta": [
            "One primary CTA per email — max two (primary + secondary).",
            "Use action verbs: 'Get', 'Start', 'Claim', 'Download'.",
            "Make the CTA button stand out — contrasting colour.",
            "Place CTA above the fold AND at the bottom.",
            "Repeat the CTA as a text link if it's a long email.",
        ],
        "timing": [
            "B2C best days: Tuesday, Wednesday, Thursday.",
            "B2B best times: 8–10 AM or 3–4 PM recipient's local time.",
            "Avoid Friday afternoons, weekends, and Monday mornings.",
            "Welcome emails: send immediately after sign-up.",
            "Cart abandonment: send within 1 hour, then 24h, then 72h.",
        ],
        "segmentation": [
            "Segment by engagement: active (opened last 90d) vs. inactive.",
            "Segment by purchase history: first-time vs. repeat buyers.",
            "Segment by funnel stage: awareness, consideration, intent.",
            "Segment by demographics if you have the data.",
            "Re-engagement sequence for subscribers inactive >90 days.",
        ],
    }

    tips = practices.get(category.lower(), practices["general"])
    header = f"Email Best Practices — {category.upper()}\n" + "=" * 50
    return header + "\n" + "\n".join(f"  ✓ {tip}" for tip in tips)


EMAIL_TOOLS = [
    draft_email_campaign,
    save_email_campaign,
    generate_ab_subject_lines,
    build_drip_sequence,
    convert_to_plain_text,
    list_email_campaigns,
    get_email_best_practices,
]
