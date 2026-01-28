import re

NEWSLETTER_HINTS = ["unsubscribe", "abbestellen", "manage preferences", "newsletter", "marketing"]

CATEGORY_KEYWORDS = {
    "finance": ["rechnung", "invoice", "payment", "zahlung", "lastschrift"],
    "calendar": ["termin", "meeting", "invite", "kalender", "zoom", "teams"],
    "security": ["passwort", "security", "2fa", "code", "verify", "verifizieren"],
}

URGENCY_KEYWORDS = ["dringend", "asap", "heute", "deadline", "frist", "sofort"]


def normalize_subject(subject: str | None) -> str:
    if not subject:
        return ""
    normalized = subject.strip().lower()
    normalized = re.sub(r"^(re:|fw:|fwd:)\s*", "", normalized)
    return re.sub(r"\s+", " ", normalized)


def is_newsletter(list_unsubscribe: str | None, snippet: str | None) -> bool:
    if list_unsubscribe:
        return True
    text = (snippet or "").lower()
    return any(hint in text for hint in NEWSLETTER_HINTS)


def guess_category(subject: str | None, snippet: str | None, newsletter: bool) -> str:
    if newsletter:
        return "newsletter"
    text = f"{subject or ''} {snippet or ''}".lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "general"


def priority(subject: str | None, snippet: str | None, newsletter: bool) -> tuple[int, str]:
    if newsletter:
        return 5, "Newsletter erkannt"
    text = f"{subject or ''} {snippet or ''}".lower()
    score = 20
    reasons = []
    if any(keyword in text for keyword in URGENCY_KEYWORDS):
        score += 40
        reasons.append("Dringlichkeitsbegriffe")
    if any(keyword in text for keyword in CATEGORY_KEYWORDS["finance"]):
        score += 30
        reasons.append("Finanzbezug")
    if "?" in (subject or ""):
        score += 10
        reasons.append("Frage erkannt")
    if not reasons:
        reasons.append("Standardpriorität")
    return min(score, 100), ", ".join(reasons)


def thread_key(message_id: str | None, in_reply_to: str | None, references: str | None, subject: str | None, from_addr: str | None) -> str:
    if in_reply_to:
        return in_reply_to.strip()
    if references:
        refs = references.strip().split()
        if refs:
            return refs[-1]
    base = normalize_subject(subject)
    domain = ""
    if from_addr and "@" in from_addr:
        domain = from_addr.split("@")[-1].strip(" >").lower()
    return f"{base}::{domain}"
