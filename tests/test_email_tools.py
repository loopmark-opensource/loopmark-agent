from tools.email_tools import (
    draft_email_campaign,
    save_email_campaign,
    generate_ab_subject_lines,
    build_drip_sequence,
    list_email_campaigns,
    get_email_best_practices,
)


def test_draft_email_campaign():
    result = draft_email_campaign.invoke(
        {
            "campaign_name": "Black Friday",
            "subject_line": "Save 30% today",
            "goal": "drive sales",
            "audience": "existing customers",
            "key_message": "Biggest sale of the year",
            "cta_text": "Shop Now",
            "tone": "urgent",
        }
    )
    assert "Black Friday" in result
    assert "Subject line" in result


def test_save_and_list_email_campaigns():
    save_email_campaign.invoke(
        {
            "campaign_name": "Welcome",
            "subject_line": "Welcome aboard",
            "preheader": "Thanks for joining",
            "body": "Hello {{first_name}}, welcome!",
            "cta_text": "Get Started",
            "audience": "new sign-ups",
        }
    )

    listed = list_email_campaigns.invoke({"status": "draft"})
    assert "Welcome aboard" in listed


def test_generate_ab_subject_lines():
    result = generate_ab_subject_lines.invoke(
        {"topic": "summer sale", "goal": "increase opens", "count": 3}
    )
    assert "3" in result
    assert "summer sale" in result


def test_build_drip_sequence():
    result = build_drip_sequence.invoke(
        {
            "sequence_name": "Welcome Series",
            "trigger": "user signs up",
            "audience": "new users",
            "goal": "convert to paid",
            "num_emails": 5,
        }
    )
    assert "Welcome Series" in result
    assert "Email 5" in result


def test_get_email_best_practices():
    result = get_email_best_practices.invoke({"category": "subject_lines"})
    assert "subject" in result.lower()
    assert "50 characters" in result
