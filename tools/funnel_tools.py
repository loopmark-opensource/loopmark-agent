"""
Tools for the Funnel Agent.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from langchain_core.tools import tool

from models.schemas import Lead, FunnelStage
from storage import get_storage


# ─── helpers ───────────────────────────────────────────────────────────────

def _load_leads() -> list[dict]:
    return get_storage().load_leads()


def _save_leads(data: list[dict]) -> None:
    get_storage().save_leads(data)


_STAGE_ORDER = [
    FunnelStage.AWARENESS,
    FunnelStage.INTEREST,
    FunnelStage.CONSIDERATION,
    FunnelStage.INTENT,
    FunnelStage.EVALUATION,
    FunnelStage.PURCHASE,
    FunnelStage.RETENTION,
    FunnelStage.ADVOCACY,
]


# ─── tools ─────────────────────────────────────────────────────────────────

@tool
def add_lead(
    name: str,
    email: str,
    company: str = "",
    source: str = "",
    stage: str = "awareness",
    notes: str = "",
) -> str:
    """
    Add a new lead to the funnel.

    Args:
        name: Full name of the lead.
        email: Email address.
        company: Company name (optional).
        source: Acquisition source (e.g. 'google_ads', 'referral', 'organic').
        stage: Initial funnel stage (awareness, interest, consideration, intent,
               evaluation, purchase, retention, advocacy).
        notes: Any additional notes.

    Returns:
        Confirmation with the assigned lead ID.
    """
    lead = Lead(
        name=name,
        email=email,
        company=company,
        source=source,
        stage=FunnelStage(stage.lower()),
        notes=notes,
    )
    leads = _load_leads()
    leads.append(lead.model_dump())
    _save_leads(leads)
    return f"Lead added. ID: {lead.id}  |  Stage: {lead.stage.value}"


@tool
def update_lead_stage(lead_id: str, new_stage: str, notes: str = "") -> str:
    """
    Move a lead to a new funnel stage and optionally update notes.

    Args:
        lead_id: The lead ID (e.g. LEAD-1234567890).
        new_stage: Target stage name.
        notes: Optional notes about the stage transition.

    Returns:
        Confirmation or error message.
    """
    leads = _load_leads()
    for lead in leads:
        if lead["id"] == lead_id:
            old_stage = lead["stage"]
            lead["stage"] = new_stage.lower()
            lead["last_contacted"] = datetime.utcnow().isoformat()
            if notes:
                lead["notes"] = (lead.get("notes", "") + f"\n[{datetime.utcnow().date()}] {notes}").strip()
            _save_leads(leads)
            return f"Lead {lead_id} moved from '{old_stage}' → '{new_stage}'."
    return f"Lead {lead_id} not found."


@tool
def score_lead(lead_id: str, score: int, reason: str = "") -> str:
    """
    Set the lead score (0–100) for a given lead.

    Args:
        lead_id: The lead ID.
        score: Score between 0 (cold) and 100 (hot / ready to buy).
        reason: Optional reason for the score.

    Returns:
        Confirmation or error message.
    """
    if not 0 <= score <= 100:
        return "Score must be between 0 and 100."
    leads = _load_leads()
    for lead in leads:
        if lead["id"] == lead_id:
            lead["score"] = score
            if reason:
                lead["notes"] = (lead.get("notes", "") + f"\n[score={score}] {reason}").strip()
            _save_leads(leads)
            return f"Lead {lead_id} score updated to {score}/100."
    return f"Lead {lead_id} not found."


@tool
def get_funnel_metrics() -> str:
    """
    Return overall funnel health metrics: lead counts by stage, average score,
    and top acquisition sources.

    Returns:
        A formatted funnel metrics report.
    """
    leads = _load_leads()
    if not leads:
        return "No leads in the funnel yet."

    stage_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}
    scores: list[int] = []

    for lead in leads:
        stage = lead.get("stage", "unknown")
        stage_counts[stage] = stage_counts.get(stage, 0) + 1

        source = lead.get("source", "unknown") or "unknown"
        source_counts[source] = source_counts.get(source, 0) + 1

        scores.append(lead.get("score", 0))

    avg_score = sum(scores) / len(scores) if scores else 0
    top_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:3]

    lines = [
        f"Total leads: {len(leads)}",
        f"Average lead score: {avg_score:.1f}/100",
        "",
        "Leads by stage:",
    ]
    for stage in _STAGE_ORDER:
        count = stage_counts.get(stage.value, 0)
        bar = "█" * count
        lines.append(f"  {stage.value:<15} {count:>3}  {bar}")

    lines += [
        "",
        "Top acquisition sources:",
        *[f"  {src}: {cnt}" for src, cnt in top_sources],
    ]
    return "\n".join(lines)


@tool
def list_leads(stage: str = "all", min_score: int = 0, limit: int = 10) -> str:
    """
    List leads in the funnel, optionally filtered by stage and minimum score.

    Args:
        stage: Funnel stage to filter by or 'all'.
        min_score: Only show leads with score ≥ this value.
        limit: Maximum number of leads to return.

    Returns:
        A formatted list of leads.
    """
    leads = _load_leads()

    if stage != "all":
        leads = [l for l in leads if l.get("stage") == stage.lower()]
    leads = [l for l in leads if l.get("score", 0) >= min_score]
    leads = leads[:limit]

    if not leads:
        return "No leads found matching the criteria."

    lines = []
    for l in leads:
        lines.append(
            f"[{l['id']}] {l['name']} <{l['email']}> | "
            f"Stage: {l.get('stage')} | Score: {l.get('score', 0)}/100 | "
            f"Source: {l.get('source', 'N/A')}"
        )
    return "\n".join(lines)


@tool
def get_nurture_sequence(stage: str) -> str:
    """
    Return a recommended nurture sequence (email / touchpoint plan) for leads
    at a given funnel stage.

    Args:
        stage: The funnel stage (awareness, interest, consideration, intent,
               evaluation, purchase, retention, advocacy).

    Returns:
        A step-by-step nurture sequence recommendation.
    """
    sequences = {
        "awareness": [
            "Day 0: Send welcome email with brand story + value proposition.",
            "Day 3: Share a top-performing blog post / educational content.",
            "Day 7: Invite to a free webinar or download a lead magnet.",
        ],
        "interest": [
            "Day 0: Send case study relevant to their industry.",
            "Day 2: Follow up with product demo video.",
            "Day 5: Offer a free consultation call.",
        ],
        "consideration": [
            "Day 0: Send comparison guide (your product vs. alternatives).",
            "Day 2: Share testimonials and social proof.",
            "Day 4: Provide a limited-time trial or discount offer.",
        ],
        "intent": [
            "Day 0: Personalised outreach from a sales rep.",
            "Day 1: Send ROI calculator or pricing sheet.",
            "Day 3: Address objections with an FAQ / 1-on-1 demo.",
        ],
        "evaluation": [
            "Day 0: Send a decision-making guide.",
            "Day 2: Offer a pilot / proof-of-concept.",
            "Day 4: Executive sponsor call if deal is large.",
        ],
        "purchase": [
            "Day 0: Send order confirmation + onboarding guide.",
            "Day 3: Check-in call / welcome email from customer success.",
            "Day 14: Request first review / NPS survey.",
        ],
        "retention": [
            "Monthly: Share product updates and new features.",
            "Quarterly: Business review with success metrics.",
            "Annually: Renewal reminder with loyalty discount.",
        ],
        "advocacy": [
            "Month 1: Invite to customer advisory board.",
            "Month 2: Co-author a case study.",
            "Month 3: Referral programme invitation.",
        ],
    }

    seq = sequences.get(stage.lower())
    if not seq:
        return f"Unknown stage '{stage}'. Valid stages: {', '.join(sequences.keys())}"

    lines = [f"Nurture sequence for '{stage.upper()}' stage:", ""]
    lines += [f"  {step}" for step in seq]
    return "\n".join(lines)


FUNNEL_TOOLS = [
    add_lead,
    update_lead_stage,
    score_lead,
    get_funnel_metrics,
    list_leads,
    get_nurture_sequence,
]
