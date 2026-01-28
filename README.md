# MailPilot - AI-Powered Email Manager

Ein smarter Email-Manager, der E-Mails synchronisiert, kategorisiert und KI-basierte Antwortvorschläge liefert.

## Features

- **Multi-Account Support**: Verwalte mehrere E-Mail-Konten.
- **IMAP Sync**: Synchronisiert E-Mails und organisiert sie in Threads.
- **AI Classification**: Automatische Kategorisierung (Newsletter, Finanzen, Kalender, etc.) und Priorisierung.
- **AI Reply Suggestions**: Generiert Antwortvorschläge basierend auf dem Inhalt der E-Mail.
- **SMTP Integration**: Sende E-Mails direkt aus der Anwendung.
- **Secure**: Passwort-Verschlüsselung (Fernet).

## API Endpunkte

- `POST /accounts`: E-Mail-Konto hinzufügen.
- `POST /accounts/{id}/sync`: E-Mails synchronisieren.
- `GET /accounts/{id}/threads`: Liste der E-Mail-Threads abrufen (sortiert nach Priorität).
- `GET /threads/{id}/messages`: Nachrichten eines Threads anzeigen.
- `GET /threads/{id}/suggest-reply`: KI-Antwortvorschlag generieren.
- `POST /accounts/{id}/send`: E-Mail senden.

## Setup

1. Abhängigkeiten installieren: `pip install -r requirements.txt`
2. `.env` Datei anlegen (siehe `.env.example`).
3. App starten: `uvicorn app.main:app --reload`