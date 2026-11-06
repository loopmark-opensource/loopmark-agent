"""Records created in one clock tick must remain independently addressable."""

from datetime import datetime, timezone

import pytest

from models.schemas import AudiencePersona, Complaint, Lead
from storage import get_storage
from tools.email_tools import save_email_campaign
from tools.funnel_tools import update_lead_stage
from tools.publisher_tools import _mark_published
from tools.social_tools import save_post


@pytest.fixture(autouse=True)
def frozen_clock(monkeypatch):
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for module in ("models.schemas", "tools.social_tools", "tools.email_tools"):
        monkeypatch.setattr(f"{module}.utcnow", lambda: now)


@pytest.mark.parametrize(
    "model, fields, prefix",
    [
        (Complaint, {"message": "Damaged package"}, "CMP"),
        (AudiencePersona, {"name": "Founder"}, "PERSONA"),
        (Lead, {"name": "Jane", "email": "jane@example.com"}, "LEAD"),
    ],
)
def test_model_ids_are_unique_in_one_clock_tick(model, fields, prefix):
    ids = [model(**fields).id for _ in range(1000)]
    assert len(set(ids)) == len(ids)
    assert all(record_id.startswith(f"{prefix}-") for record_id in ids)


@pytest.mark.parametrize(
    "save, fields, load, prefix",
    [
        (save_post, {"platform": "twitter", "content": "Hello"}, "load_posts", "POST"),
        (
            save_email_campaign,
            {
                "campaign_name": "Launch", "subject_line": "Hello", "preheader": "Preview",
                "body": "News", "cta_text": "Read more",
            },
            "load_emails",
            "EMAIL",
        ),
    ],
)
def test_saved_ids_are_unique_in_one_clock_tick(save, fields, load, prefix):
    for _ in range(100):
        save.invoke(fields)
    records = getattr(get_storage(), load)()
    assert len(records) == 100
    assert len({record["id"] for record in records}) == 100
    assert all(record["id"].startswith(f"{prefix}-") for record in records)


def test_lead_updates_preserve_legacy_ids_and_target_one_new_record():
    legacy = Lead(id="LEAD-1700000000", name="Legacy", email="old@example.com")
    first = Lead(name="First", email="first@example.com")
    second = Lead(name="Second", email="second@example.com")
    storage = get_storage()
    storage.save_leads([lead.model_dump(mode="json") for lead in (legacy, first, second)])

    update_lead_stage.invoke({"lead_id": second.id, "new_stage": "interest"})
    update_lead_stage.invoke({"lead_id": legacy.id, "new_stage": "purchase"})

    records = storage.load_leads()
    assert [record["id"] for record in records] == [legacy.id, first.id, second.id]
    assert [record["stage"] for record in records] == ["purchase", "awareness", "interest"]


def test_publishing_targets_one_new_post_and_accepts_legacy_ids():
    storage = get_storage()
    storage.save_posts([{"id": "POST-1700000000", "status": "draft"}])
    for content in ("First", "Second"):
        save_post.invoke({"platform": "twitter", "content": content})
    posts = storage.load_posts()

    _mark_published(posts[2]["id"])
    _mark_published("POST-1700000000")

    updated = storage.load_posts()
    assert [post["id"] for post in updated] == [post["id"] for post in posts]
    assert [post["status"] for post in updated] == ["published", "draft", "published"]
