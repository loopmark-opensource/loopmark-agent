from models.schemas import (
    Complaint,
    ComplaintCategory,
    ComplaintSeverity,
    FunnelStage,
    Lead,
    Platform,
    PostRequest,
    ContentTone,
)


def test_complaint_defaults():
    complaint = Complaint(message="Package arrived damaged")
    assert complaint.category == ComplaintCategory.OTHER
    assert complaint.severity == ComplaintSeverity.MEDIUM
    assert complaint.resolved is False
    assert complaint.id.startswith("CMP-")


def test_complaint_custom_fields():
    complaint = Complaint(
        message="Billing error",
        customer_name="Alice",
        category=ComplaintCategory.BILLING,
        severity=ComplaintSeverity.HIGH,
    )
    assert complaint.customer_name == "Alice"
    assert complaint.category == ComplaintCategory.BILLING
    assert complaint.severity == ComplaintSeverity.HIGH


def test_lead_defaults():
    lead = Lead(name="John Smith", email="john@example.com")
    assert lead.stage == FunnelStage.AWARENESS
    assert lead.score == 0
    assert lead.id.startswith("LEAD-")


def test_post_request():
    request = PostRequest(
        topic="Summer sale",
        platform=Platform.LINKEDIN,
        tone=ContentTone.PROFESSIONAL,
    )
    assert request.platform == Platform.LINKEDIN
    assert request.include_cta is True
