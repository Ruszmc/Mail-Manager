import re

NEWSLETTER_HINTS = [
    "unsubscribe", "abbestellen", "manage preferences", "newsletter", "marketing"
]

def normalize_subject(subject: str | None) -> str:
    if not subject:
        return ""
    s = subject.strip().lower()
    s = re.sub(r"^(re:|fw:|fwd:)\s*", "", s)
    s = re.sub(r"\s+", " ", s)
    return s

def thread_key(subject: str | None, from_addr: str | None) -> str:
    subj = normalize_subject(subject)
    dom = ""
    if from_addr and "@" in from_addr:
        dom = from_addr.split("@")[-1].strip(" >").lower()
    return f"{subj}::{dom}"

def is_newsletter(list_unsubscribe: str | None, snippet: str | None) -> bool:
    if list_unsubscribe and len(list_unsubscribe) > 0:
        return True
    text = (snippet or "").lower()
    return any(h in text for h in NEWSLETTER_HINTS)

def category_guess(subject: str | None, snippet: str | None, newsletter: bool) -> str:
    if newsletter:
        return "newsletter"
    text = f"{subject or ''} {snippet or ''}".lower()
    if any(k in text for k in ["rechnung", "invoice", "zahlung", "payment", "lastschrift"]):
        return "finance"
    if any(k in text for k in ["termin", "meeting", "kalender", "invite", "zoom", "teams"]):
        return "calendar"
    if any(k in text for k in ["passwort", "security", "2fa", "code", "verify", "verifizieren"]):
        return "security"
    return "general"

def priority_score(subject: str | None, snippet: str | None, newsletter: bool) -> int:
    if newsletter:
        return 5
    text = f"{subject or ''} {snippet or ''}".lower()
    score = 20
    if any(k in text for k in ["dringend", "asap", "heute", "deadline", "frist", "sofort"]):
        score += 40
    if any(k in text for k in ["rechnung", "invoice", "zahlung", "payment"]):
        score += 30
    if "?" in (subject or ""):
        score += 10
    return min(score, 100)

def generate_reply_suggestion(subject: str | None, snippet: str | None) -> str:
    """
    Simuliert eine KI-Antwortgenerierung. 
    In einer echten App würde hier ein LLM (OpenAI/Mistral) aufgerufen werden.
    """
    subj = (subject or "").lower()
    text = (snippet or "").lower()

    if "termin" in text or "meeting" in text or "invite" in text:
        return "Vielen Dank für die Einladung. Ich schaue in meinen Kalender und melde mich zeitnah zurück."
    if "rechnung" in text or "invoice" in text:
        return "Vielen Dank für die Zusendung der Rechnung. Ich werde diese prüfen und die Zahlung veranlassen."
    if "frage" in text or "?" in subj:
        return "Vielen Dank für Ihre Nachricht. Ich werde mir Ihre Frage ansehen und Ihnen so schnell wie möglich antworten."
    
    return "Vielen Dank für Ihre Nachricht. Ich habe sie erhalten und werde mich bei Bedarf zurückmelden."


def generate_thread_summary(subject: str | None, snippet: str | None) -> str:
    subject_text = (subject or "Ohne Betreff").strip()
    snippet_text = (snippet or "").strip()
    if not snippet_text:
        return f"Zusammenfassung: Thread zum Thema „{subject_text}“ ohne Vorschautext."
    return f"Zusammenfassung: {subject_text} – {snippet_text[:160]}"


def extract_action_items(subject: str | None, snippet: str | None) -> list[str]:
    text = f"{subject or ''} {snippet or ''}".lower()
    actions: list[str] = []
    if any(k in text for k in ["termin", "meeting", "kalender", "invite", "zoom", "teams"]):
        actions.append("Kalendereinladung prüfen und zusagen/ablehnen.")
    if any(k in text for k in ["rechnung", "invoice", "zahlung", "payment", "überweisung"]):
        actions.append("Rechnung prüfen und Zahlung einplanen.")
    if any(k in text for k in ["angebot", "quote", "proposal"]):
        actions.append("Angebot prüfen und Rückmeldung geben.")
    if any(k in text for k in ["frage", "bitte", "kannst du"]):
        actions.append("Antwort formulieren und Rückfragen klären.")
    if not actions:
        actions.append("Falls nötig, kurz antworten oder archivieren.")
    return actions


def suggest_labels(subject: str | None, snippet: str | None, newsletter: bool) -> list[str]:
    labels = {category_guess(subject, snippet, newsletter)}
    text = f"{subject or ''} {snippet or ''}".lower()
    if any(k in text for k in ["login", "passwort", "security", "2fa", "code"]):
        labels.add("security")
    if any(k in text for k in ["versand", "lieferung", "tracking", "zustellung"]):
        labels.add("shipping")
    if newsletter:
        labels.add("newsletter")
    return sorted(labels)
