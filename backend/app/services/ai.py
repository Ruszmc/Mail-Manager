import os
from .classifier import guess_category


def _stub_response(task: str, subject: str | None, snippet: str | None) -> str:
    category = guess_category(subject, snippet, False)
    return f"[{task}] Dieses Ergebnis ist ein Platzhalter. Kategorie: {category}."


def summarize(subject: str | None, snippet: str | None, body: str | None) -> str:
    if os.getenv("MAILPILOT_AI_KEY"):
        return _stub_response("Zusammenfassung", subject, snippet)
    return _stub_response("Zusammenfassung", subject, snippet)


def extract_actions(subject: str | None, snippet: str | None, body: str | None) -> str:
    return "- Aufgabe 1\n- Aufgabe 2\n(Hinweis: KI-Integration fehlt, bitte API-Key konfigurieren.)"


def draft_reply(subject: str | None, snippet: str | None, body: str | None, language: str | None) -> str:
    lang_hint = "Deutsch" if (language or "").lower().startswith("de") else "Englisch"
    return f"Vielen Dank für Ihre Nachricht. (Entwurf in {lang_hint}, KI-Stub)"
