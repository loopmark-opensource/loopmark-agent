"""
Tools for the Complaints Agent.

Each tool is a plain Python function decorated with @tool so LangChain
can bind it to the LLM.  All persistence is file-backed JSON stored in
the data/ directory.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from langchain_core.tools import tool

from models.schemas import (
    Complaint, ComplaintCategory, ComplaintSeverity,
)
from storage import get_storage


# ─── helpers ───────────────────────────────────────────────────────────────

def _load_complaints() -> list[dict]:
    return get_storage().load_complaints()


def _save_complaints(data: list[dict]) -> None:
    get_storage().save_complaints(data)


# ─── tools ─────────────────────────────────────────────────────────────────

@tool
def log_complaint(
    message: str,
    customer_name: str = "",
    customer_email: str = "",
    category: str = "other",
    severity: str = "medium",
) -> str:
    """
    Log a new customer complaint into the system.

    Args:
        message: The complaint text from the customer.
        customer_name: Name of the customer (optional).
        customer_email: Email of the customer (optional).
        category: One of product, shipping, billing, customer_service, other.
        severity: One of low, medium, high, critical.

    Returns:
        Confirmation message with the assigned complaint ID.
    """
    complaint = Complaint(
        message=message,
        customer_name=customer_name,
        customer_email=customer_email,
        category=ComplaintCategory(category.lower()),
        severity=ComplaintSeverity(severity.lower()),
    )
    complaints = _load_complaints()
    complaints.append(complaint.model_dump())
    _save_complaints(complaints)
    return f"Complaint logged successfully. ID: {complaint.id}"


@tool
def list_complaints(
    status: str = "all",
    severity: str = "all",
    limit: int = 10,
) -> str:
    """
    List complaints from the system.

    Args:
        status: 'all', 'open', or 'resolved'.
        severity: Filter by severity — 'all', 'low', 'medium', 'high', 'critical'.
        limit: Maximum number of complaints to return.

    Returns:
        JSON string of matching complaints.
    """
    complaints = _load_complaints()

    if status == "open":
        complaints = [c for c in complaints if not c.get("resolved")]
    elif status == "resolved":
        complaints = [c for c in complaints if c.get("resolved")]

    if severity != "all":
        complaints = [c for c in complaints if c.get("severity") == severity]

    complaints = complaints[:limit]

    if not complaints:
        return "No complaints found matching the criteria."

    lines = []
    for c in complaints:
        lines.append(
            f"[{c['id']}] [{c['severity'].upper()}] {c['category']} — "
            f"{c['message'][:80]}... (resolved: {c['resolved']})"
        )
    return "\n".join(lines)


@tool
def resolve_complaint(complaint_id: str, response_message: str) -> str:
    """
    Mark a complaint as resolved and attach the response sent to the customer.

    Args:
        complaint_id: The complaint ID (e.g. CMP-1234567890).
        response_message: The response message sent to the customer.

    Returns:
        Confirmation or error message.
    """
    complaints = _load_complaints()
    for c in complaints:
        if c["id"] == complaint_id:
            c["resolved"] = True
            c["response"] = response_message
            _save_complaints(complaints)
            return f"Complaint {complaint_id} resolved successfully."
    return f"Complaint {complaint_id} not found."


@tool
def get_complaint_stats() -> str:
    """
    Return summary statistics about all complaints in the system.

    Returns:
        A human-readable summary: total, open, resolved, breakdown by severity and category.
    """
    complaints = _load_complaints()
    if not complaints:
        return "No complaints on record."

    total = len(complaints)
    open_count = sum(1 for c in complaints if not c.get("resolved"))
    resolved_count = total - open_count

    sev_counts: dict[str, int] = {}
    cat_counts: dict[str, int] = {}
    for c in complaints:
        sev_counts[c.get("severity", "unknown")] = sev_counts.get(c.get("severity", "unknown"), 0) + 1
        cat_counts[c.get("category", "unknown")] = cat_counts.get(c.get("category", "unknown"), 0) + 1

    lines = [
        f"Total complaints: {total}",
        f"  Open: {open_count}  |  Resolved: {resolved_count}",
        "",
        "By severity:",
        *[f"  {k}: {v}" for k, v in sorted(sev_counts.items())],
        "",
        "By category:",
        *[f"  {k}: {v}" for k, v in sorted(cat_counts.items())],
    ]
    return "\n".join(lines)


@tool
def draft_complaint_response(
    complaint_id: str,
    tone: str = "professional",
) -> str:
    """
    Retrieve the complaint details so the LLM can draft a personalised response.

    Args:
        complaint_id: The complaint ID.
        tone: Tone of the response — professional, empathetic, apologetic.

    Returns:
        The complaint details as a formatted string for the LLM to use.
    """
    complaints = _load_complaints()
    for c in complaints:
        if c["id"] == complaint_id:
            return (
                f"Complaint ID: {c['id']}\n"
                f"Customer: {c.get('customer_name', 'Unknown')}\n"
                f"Email: {c.get('customer_email', 'N/A')}\n"
                f"Category: {c['category']}\n"
                f"Severity: {c['severity']}\n"
                f"Message: {c['message']}\n"
                f"Tone requested: {tone}\n"
                f"\nPlease draft a {tone} response addressing this complaint."
            )
    return f"Complaint {complaint_id} not found."


COMPLAINT_TOOLS = [
    log_complaint,
    list_complaints,
    resolve_complaint,
    get_complaint_stats,
    draft_complaint_response,
]
