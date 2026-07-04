from tools.funnel_tools import (
    add_lead,
    update_lead_stage,
    score_lead,
    get_funnel_metrics,
    list_leads,
    get_nurture_sequence,
)


def test_add_and_list_leads():
    result = add_lead.invoke(
        {
            "name": "John Smith",
            "email": "john@acme.com",
            "company": "Acme Corp",
            "source": "google_ads",
            "stage": "interest",
        }
    )
    assert "Lead added" in result
    assert "interest" in result

    listed = list_leads.invoke({"stage": "interest"})
    assert "John Smith" in listed
    assert "john@acme.com" in listed


def test_update_lead_stage():
    add_result = add_lead.invoke({"name": "Jane Doe", "email": "jane@example.com"})
    lead_id = add_result.split("ID: ")[1].split()[0]

    result = update_lead_stage.invoke(
        {"lead_id": lead_id, "new_stage": "consideration", "notes": "Booked demo"}
    )
    assert "consideration" in result


def test_score_lead():
    add_result = add_lead.invoke({"name": "Bob", "email": "bob@example.com"})
    lead_id = add_result.split("ID: ")[1].split()[0]

    result = score_lead.invoke({"lead_id": lead_id, "score": 75, "reason": "Demo booked"})
    assert "75/100" in result

    invalid = score_lead.invoke({"lead_id": lead_id, "score": 150})
    assert "between 0 and 100" in invalid


def test_get_funnel_metrics():
    add_lead.invoke({"name": "A", "email": "a@test.com", "source": "referral"})
    add_lead.invoke({"name": "B", "email": "b@test.com", "source": "referral"})

    metrics = get_funnel_metrics.invoke({})
    assert "Total leads: 2" in metrics
    assert "awareness" in metrics


def test_get_nurture_sequence():
    result = get_nurture_sequence.invoke({"stage": "consideration"})
    assert "consideration" in result.lower()
    assert "Day 0" in result


def test_get_nurture_sequence_unknown_stage():
    result = get_nurture_sequence.invoke({"stage": "invalid"})
    assert "Unknown stage" in result
