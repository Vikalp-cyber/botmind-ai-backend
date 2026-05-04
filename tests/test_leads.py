from app.db.models import LeadTag
from app.utils.leads import classify_lead_tag, extract_contact_details


def test_extract_contact_details_reads_common_fields():
    details = extract_contact_details(
        "Hi, my name is Priya Sharma. Email me at priya@example.com or call +1 415 555 1212."
    )
    assert details["name"] == "Priya Sharma"
    assert details["email"] == "priya@example.com"
    assert "+1 415 555 1212" in details["phone"]


def test_classify_lead_tag_marks_hot_when_contact_and_buy_intent():
    text = "I want pricing for your enterprise plan. Contact me at lead@example.com."
    details = extract_contact_details(text)
    assert classify_lead_tag(text, details) == LeadTag.HOT
