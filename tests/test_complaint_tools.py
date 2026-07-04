import json

from config import config
from tools.complaint_tools import (
    log_complaint,
    list_complaints,
    resolve_complaint,
    get_complaint_stats,
    draft_complaint_response,
)


def test_log_and_list_complaint():
    result = log_complaint.invoke(
        {
            "message": "Package arrived damaged",
            "customer_name": "Alice",
            "category": "shipping",
            "severity": "high",
        }
    )
    assert "Complaint logged successfully" in result
    assert "CMP-" in result

    listed = list_complaints.invoke({"status": "open", "limit": 5})
    assert "Package arrived damaged" in listed
    assert "HIGH" in listed


def test_resolve_complaint():
    log_complaint.invoke({"message": "Late delivery", "severity": "medium"})

    with open(config.COMPLAINTS_FILE) as f:
        complaint_id = json.load(f)[0]["id"]

    result = resolve_complaint.invoke(
        {"complaint_id": complaint_id, "response_message": "We apologise for the delay."}
    )
    assert "resolved successfully" in result

    listed = list_complaints.invoke({"status": "resolved"})
    assert complaint_id in listed


def test_get_complaint_stats():
    log_complaint.invoke({"message": "Issue A", "severity": "low"})
    log_complaint.invoke({"message": "Issue B", "severity": "critical", "category": "billing"})

    stats = get_complaint_stats.invoke({})
    assert "Total complaints: 2" in stats
    assert "Open: 2" in stats


def test_draft_complaint_response_not_found():
    result = draft_complaint_response.invoke({"complaint_id": "CMP-0000000000"})
    assert "not found" in result
