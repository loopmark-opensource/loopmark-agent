from models.schemas import (
    Complaint,
    ComplaintCategory,
    ComplaintSeverity,
    FunnelStage,
    Lead,
    Platform,
    PostRequest,
    ContentTone,
    BusinessProfile,
    AudiencePersona,
    CRMContact,
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


def test_business_profile_defaults():
    profile = BusinessProfile(product_name="Acme")
    assert profile.product_name == "Acme"
    assert profile.website_url == ""


def test_audience_persona_defaults():
    persona = AudiencePersona(name="Founder")
    assert persona.name == "Founder"
    assert persona.id.startswith("PERSONA-")


def test_crm_contact_segment_default():
    contact = CRMContact(name="Jane", email="jane@example.com")
    assert contact.segment == "general"
