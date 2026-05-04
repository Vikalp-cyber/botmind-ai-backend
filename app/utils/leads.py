import re

from app.db.models import LeadTag

EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"(\+?\d[\d\s().-]{7,}\d)")
NAME_PATTERNS = [
    re.compile(r"\bmy name is ([A-Za-z][A-Za-z\s'-]{1,60})", re.IGNORECASE),
    re.compile(r"\bi am ([A-Za-z][A-Za-z\s'-]{1,60})", re.IGNORECASE),
    re.compile(r"\bthis is ([A-Za-z][A-Za-z\s'-]{1,60})", re.IGNORECASE),
]
HOT_KEYWORDS = ("buy", "pricing", "quote", "demo", "sales", "contact me", "call me", "enterprise")
WARM_KEYWORDS = ("interested", "learn more", "trial", "features", "help me")


def extract_contact_details(text: str) -> dict[str, str | None]:
    email_match = EMAIL_PATTERN.search(text)
    phone_match = PHONE_PATTERN.search(text)
    name = None
    for pattern in NAME_PATTERNS:
        match = pattern.search(text)
        if match:
            name = match.group(1).strip(" .,-")
            break
    return {
        "name": name,
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0).strip() if phone_match else None,
    }


def classify_lead_tag(text: str, details: dict[str, str | None]) -> LeadTag:
    lowered = text.lower()
    has_contact = any(details.values())
    if has_contact and any(keyword in lowered for keyword in HOT_KEYWORDS):
        return LeadTag.HOT
    if has_contact or any(keyword in lowered for keyword in WARM_KEYWORDS):
        return LeadTag.WARM
    return LeadTag.COLD
