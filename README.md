# MailPilot – AI-assisted Email Client MVP

MailPilot is a cross-provider email client that works with **any email address** via IMAP (read/sync) + SMTP (send). It helps you prioritize, categorize, manage newsletters, and draft replies with **explicit AI actions only**.

## Features (MVP)
- **Account setup** with IMAP/SMTP, encrypted credentials.
- **Manual sync** (no background cron) for latest messages.
- **Threading** using Message-ID / In-Reply-To / References with subject fallback.
- **Deterministic classification** (newsletter detection + categories + priority score + explanation).
- **Newsletters tab** with safe unsubscribe options (mailto/URL only on user action).
- **AI-assisted actions**: Summarize, Extract Actions, Draft Reply (stub unless AI key provided).
- **Privacy by default**: store only headers + snippet; full body fetched on demand.

## Repo Structure
```
backend/   FastAPI + SQLite + Alembic
frontend/  Next.js + TypeScript + Tailwind UI
```

## Backend Setup (FastAPI)
1. Create a virtualenv and install dependencies:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Create `.env` from sample:
   ```bash
   cp .env.sample .env
   ```
3. Generate a Fernet key and set it in `.env`:
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
4. Run migrations:
   ```bash
   alembic upgrade head
   ```
5. Start the API:
   ```bash
   uvicorn app.main:app --reload
   ```

### Backend Environment Variables
- `MAILPILOT_DB_URL` (default: `sqlite:///./mailpilot.db`)
- `MAILPILOT_FERNET_KEY` (**required**) – encryption key for credentials
- `MAILPILOT_AI_KEY` (optional) – wire up a real LLM later

## Frontend Setup (Next.js)
1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```
2. Create `.env.local`:
   ```bash
   cp .env.sample .env.local
   ```
3. Run the app:
   ```bash
   npm run dev
   ```

Open http://localhost:3000

## Usage Flow
1. Add an account (IMAP/SMTP + app password).
2. Click **Sync Now** to fetch latest messages.
3. Select a thread to view insights and snippets.
4. Use **Summarize** or **Draft Reply** for AI actions.
5. Manage newsletters via the **Newsletters** tab.

## Notes
- MailPilot never auto-sends replies.
- Unsubscribe links are presented safely; external URLs are not auto-opened.
