from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel, EmailStr, ConfigDict
from sqlalchemy.orm import Session
from datetime import datetime
from dotenv import load_dotenv

from .db import Base, engine, get_db
from .models import Account, Thread, Message
from .crypto import encrypt, decrypt
from .imap_client import ImapClient, ImapAuthenticationError
from .classifier import thread_key, is_newsletter, category_guess, priority_score, generate_reply_suggestion
from .smtp_client import SmtpClient

load_dotenv()
Base.metadata.create_all(bind=engine)

app = FastAPI(title="MailPilot Skeleton", version="0.1.0")

@app.get("/", response_class=HTMLResponse)
def root(db: Session = Depends(get_db)):
    accounts = db.query(Account).all()
    
    html_content = """
    <html>
        <head>
            <title>MailPilot - Dashboard</title>
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; background-color: #f0f2f5; color: #1c1e21; }
                .navbar { background-color: #2c3e50; color: white; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; }
                .container { max-width: 1200px; margin: 2rem auto; padding: 0 1rem; display: grid; grid-template-columns: 350px 1fr; gap: 2rem; }
                .card { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 1.5rem; }
                h1, h2, h3 { margin-top: 0; color: #2c3e50; }
                .btn { display: inline-block; background: #3498db; color: white; padding: 0.5rem 1rem; border-radius: 4px; border: none; cursor: pointer; text-decoration: none; font-size: 0.9rem; }
                .btn:hover { background: #2980b9; }
                .btn-secondary { background: #95a5a6; }
                .btn-secondary:hover { background: #7f8c8d; }
                .account-item { display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 1rem; border-bottom: 1px solid #eee; cursor: pointer; margin: 0 -1.5rem; }
                .account-item:hover { background: #f8f9fa; }
                .thread-item { padding: 1rem; border-bottom: 1px solid #eee; cursor: pointer; transition: background 0.2s; position: relative; }
                .thread-item:hover { background: #f8f9fa; }
                .thread-priority { position: absolute; right: 1rem; top: 1rem; font-weight: bold; padding: 2px 6px; border-radius: 4px; font-size: 0.8rem; }
                .priority-high { background: #e74c3c; color: white; }
                .priority-med { background: #f39c12; color: white; }
                .priority-low { background: #27ae60; color: white; }
                .msg-bubble { background: #f1f0f0; padding: 0.75rem; border-radius: 12px; margin-bottom: 0.5rem; max-width: 85%; }
                .msg-meta { font-size: 0.75rem; color: #606770; margin-bottom: 0.25rem; }
                #thread-detail { position: sticky; top: 2rem; }
                input, select, textarea { width: 100%; padding: 0.5rem; margin: 0.5rem 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
                .hidden { display: none; }
                .badge { font-size: 0.7rem; padding: 2px 5px; border-radius: 10px; margin-left: 5px; text-transform: uppercase; }
                .badge-newsletter { background: #d1d8e0; color: #4b6584; }
                .badge-finance { background: #fed330; color: #7f8c8d; }
                .badge-calendar { background: #45aaf2; color: white; }
            </style>
        </head>
        <body>
            <div class="navbar">
                <div style="font-size: 1.5rem; font-weight: bold;">MailPilot 🚀</div>
                <a href="/docs" style="color: #bdc3c7; font-size: 0.8rem;">API Docs</a>
            </div>
            
            <div class="container">
                <div id="sidebar">
                    <div class="card">
                        <h3>Accounts</h3>
                        <div id="accounts-list">
    """
    
    for acc in accounts:
        html_content += f"""
                            <div class="account-item" onclick="loadThreads({acc.id})">
                                <span style="cursor: pointer; flex-grow: 1;">{acc.email}</span>
                                <button class="btn btn-secondary" onclick="event.stopPropagation(); syncAccount({acc.id})">Sync</button>
                            </div>
        """
        
    html_content += """
                            <button class="btn" style="margin-top: 1rem; width: 100%;" onclick="showAddAccount()">+ Account hinzufügen</button>
                        </div>
                        
                        <div id="add-account-form" class="hidden">
                            <h3>Neuer Account</h3>
                            <input type="email" id="acc-email" placeholder="Email">
                            <input type="password" id="acc-pass" placeholder="Passwort / App-Passwort">
                            <input type="text" id="acc-imap" placeholder="IMAP Host (z.B. imap.gmail.com)">
                            <div style="display: flex; gap: 10px;">
                                <button class="btn" onclick="saveAccount()">Speichern</button>
                                <button class="btn btn-secondary" onclick="hideAddAccount()">Abbrechen</button>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>Threads</h3>
                        <div id="threads-list">
                            <p style="color: #7f8c8d;">Wähle einen Account aus oder synchronisiere, um Threads zu sehen.</p>
                        </div>
                    </div>
                </div>
                
                <div id="main-content">
                    <div id="thread-detail" class="card">
                        <h2>Willkommen</h2>
                        <p>Wähle einen Thread aus, um Nachrichten anzuzeigen und KI-Antwortvorschläge zu erhalten.</p>
                    </div>
                </div>
            </div>

            <script>
                async function syncAccount(id) {
                    const btn = event.target;
                    btn.disabled = true;
                    btn.innerText = "Syncing...";
                    try {
                        const res = await fetch(`/accounts/${id}/sync`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({limit: 20}) });
                        const data = await res.json();
                        if (!res.ok) {
                            alert(`Sync fehlgeschlagen: ${data.detail || "Unbekannter Fehler"}`);
                        } else {
                            alert(`Synchronisiert: ${data.messages_new} neue Nachrichten.`);
                            loadThreads(id);
                        }
                    } catch (e) {
                        alert("Netzwerkfehler beim Sync.");
                    } finally {
                        btn.disabled = false;
                        btn.innerText = "Sync";
                    }
                }

                async function loadThreads(accountId) {
                    const list = document.getElementById('threads-list');
                    list.innerHTML = '<p>Lade Threads...</p>';
                    const res = await fetch(`/accounts/${accountId}/threads`);
                    const threads = await res.json();
                    list.innerHTML = '';
                    
                    threads.forEach(t => {
                        const priorityClass = t.priority_score > 70 ? 'priority-high' : (t.priority_score > 30 ? 'priority-med' : 'priority-low');
                        const badgeClass = `badge-${t.category}`;
                        const div = document.createElement('div');
                        div.className = 'thread-item';
                        div.onclick = () => loadMessages(t.id, accountId);
                        div.innerHTML = `
                            <div class="thread-priority ${priorityClass}">${t.priority_score}</div>
                            <div style="font-weight: bold; margin-right: 40px;">${t.subject || '(Kein Betreff)'}</div>
                            <div style="font-size: 0.8rem; color: #7f8c8d;">
                                ${new Date(t.last_msg_at).toLocaleString()}
                                <span class="badge ${badgeClass}">${t.category}</span>
                            </div>
                        `;
                        list.appendChild(div);
                    });
                }

                async function loadMessages(threadId, accountId) {
                    const res = await fetch(`/threads/${threadId}/messages`);
                    const msgs = await res.json();
                    
                    const detail = document.getElementById('thread-detail');
                    detail.innerHTML = `<h3>${msgs[0]?.subject || 'Thread'}</h3><div id="msgs-container"></div><hr><div id="reply-section"><h4>KI-Antwortvorschlag</h4><p id="suggestion-text">Lade Vorschlag...</p><button class="btn" id="send-btn">Antwort senden</button></div>`;
                    
                    const container = document.getElementById('msgs-container');
                    msgs.forEach(m => {
                        const mDiv = document.createElement('div');
                        mDiv.className = 'msg-bubble';
                        mDiv.innerHTML = `
                            <div class="msg-meta">Von: ${m.from_addr} | ${new Date(m.date).toLocaleString()}</div>
                            <div>${m.snippet || ''}...</div>
                        `;
                        container.appendChild(mDiv);
                    });

                    // Suggestion laden
                    const sRes = await fetch(`/threads/${threadId}/suggest-reply`);
                    const sData = await sRes.json();
                    document.getElementById('suggestion-text').innerText = sData.suggestion;
                    
                    document.getElementById('send-btn').onclick = async () => {
                        const body = sData.suggestion;
                        const to = msgs[0].from_addr; // Simplifiziert
                        const subj = "Re: " + msgs[0].subject;
                        
                        if(confirm(`Soll dieser Vorschlag an ${to} gesendet werden?`)) {
                            const sendRes = await fetch(`/accounts/${accountId}/send`, {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({ to_addr: to.match(/<(.+)>/)?.[1] || to, subject: subj, body: body })
                            });
                            if(sendRes.ok) alert("Gesendet!"); else alert("Fehler beim Senden.");
                        }
                    };
                }

                function showAddAccount() {
                    document.getElementById('accounts-list').classList.add('hidden');
                    document.getElementById('add-account-form').classList.remove('hidden');
                }

                function hideAddAccount() {
                    document.getElementById('accounts-list').classList.remove('hidden');
                    document.getElementById('add-account-form').classList.add('hidden');
                }

                async function saveAccount() {
                    const email = document.getElementById('acc-email').value;
                    const pass = document.getElementById('acc-pass').value;
                    const imap = document.getElementById('acc-imap').value;
                    
                    const res = await fetch('/accounts', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ email, password: pass, imap_host: imap })
                    });
                    
                    if(res.ok) {
                        location.reload();
                    } else {
                        const data = await res.json();
                        alert("Fehler: " + (data.detail || "Unbekannt"));
                    }
                }
                
                // Initiale Threads laden für den ersten Account falls vorhanden
                window.onload = () => {
                    const firstAcc = document.querySelector('.account-item');
                    if (firstAcc) {
                        firstAcc.click();
                    }
                };
            </script>
        </body>
    </html>
    """
    return html_content

class AccountCreate(BaseModel):
    email: EmailStr
    password: str  # For IMAP/SMTP: use app-password whenever possible.
    imap_host: str
    imap_port: int = 993
    imap_tls: bool = True
    smtp_host: str | None = None
    smtp_port: int | None = 587
    smtp_tls: bool | None = True

class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    imap_host: str
    imap_port: int
    imap_tls: bool

class SyncRequest(BaseModel):
    limit: int = 50

@app.get("/health")
def health():
    return {"ok": True, "ts": datetime.utcnow().isoformat()}

@app.post("/accounts", response_model=AccountOut)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)):
    existing = db.query(Account).filter(Account.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Account already exists")

    acc = Account(
        email=str(payload.email),
        imap_host=payload.imap_host,
        imap_port=payload.imap_port,
        imap_tls=payload.imap_tls,
        smtp_host=payload.smtp_host,
        smtp_port=payload.smtp_port or 587,
        smtp_tls=payload.smtp_tls if payload.smtp_tls is not None else True,
        password_enc=encrypt(payload.password),
    )
    db.add(acc)
    db.commit()
    db.refresh(acc)
    return acc

@app.get("/accounts", response_model=list[AccountOut])
def list_accounts(db: Session = Depends(get_db)):
    return db.query(Account).order_by(Account.id.desc()).all()

@app.post("/accounts/{account_id}/sync")
def sync_account(account_id: int, payload: SyncRequest, db: Session = Depends(get_db)):
    acc = db.query(Account).filter(Account.id == account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")

    password = decrypt(acc.password_enc)

    try:
        with ImapClient(acc.imap_host, acc.imap_port, acc.imap_tls) as imap:
            imap.login(acc.email, password)
            imap.select_inbox()
            msgs = imap.fetch_latest(limit=payload.limit)
    except ImapAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

    upserted_msgs = 0
    upserted_threads = 0

    for m in msgs:
        tkey = thread_key(m.get("subject"), m.get("from"))
        th = db.query(Thread).filter(Thread.account_id == acc.id, Thread.provider_thread_key == tkey).first()
        if not th:
            th = Thread(
                account_id=acc.id,
                provider_thread_key=tkey,
                subject=m.get("subject"),
                last_msg_at=m.get("date"),
            )
            db.add(th)
            db.flush()
            upserted_threads += 1

        newsletter = is_newsletter(m.get("list_unsubscribe"), m.get("snippet"))
        th.is_newsletter = newsletter
        th.category = category_guess(m.get("subject"), m.get("snippet"), newsletter)
        th.priority_score = priority_score(m.get("subject"), m.get("snippet"), newsletter)

        if m.get("date") and (th.last_msg_at is None or m["date"] > th.last_msg_at):
            th.last_msg_at = m["date"]
            th.subject = m.get("subject") or th.subject

        msg = db.query(Message).filter(Message.thread_id == th.id, Message.imap_uid == m["uid"]).first()
        if not msg:
            msg = Message(
                thread_id=th.id,
                imap_uid=m["uid"],
                date=m.get("date"),
                from_addr=m.get("from"),
                to_addr=m.get("to"),
                subject=m.get("subject"),
                list_unsubscribe=m.get("list_unsubscribe"),
                snippet=m.get("snippet"),
            )
            db.add(msg)
            upserted_msgs += 1

    db.commit()
    return {"threads_new": upserted_threads, "messages_new": upserted_msgs, "fetched": len(msgs)}

class ThreadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject: str | None
    last_msg_at: datetime | None
    category: str
    priority_score: int
    is_newsletter: bool

@app.get("/accounts/{account_id}/threads", response_model=list[ThreadOut])
def list_threads(account_id: int, db: Session = Depends(get_db)):
    acc = db.query(Account).filter(Account.id == account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    return (
        db.query(Thread)
        .filter(Thread.account_id == account_id)
        .order_by(Thread.priority_score.desc(), Thread.last_msg_at.desc().nullslast())
        .limit(200)
        .all()
    )

class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    imap_uid: int
    date: datetime | None
    from_addr: str | None
    to_addr: str | None
    subject: str | None
    list_unsubscribe: str | None
    snippet: str | None

@app.get("/threads/{thread_id}/messages", response_model=list[MessageOut])
def thread_messages(thread_id: int, db: Session = Depends(get_db)):
    th = db.query(Thread).filter(Thread.id == thread_id).first()
    if not th:
        raise HTTPException(status_code=404, detail="Thread not found")
    return db.query(Message).filter(Message.thread_id == thread_id).order_by(Message.date.desc().nullslast()).all()

class SendEmailRequest(BaseModel):
    to_addr: EmailStr
    subject: str
    body: str

@app.post("/accounts/{account_id}/send")
def send_email(account_id: int, payload: SendEmailRequest, db: Session = Depends(get_db)):
    acc = db.query(Account).filter(Account.id == account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    
    if not acc.smtp_host:
        raise HTTPException(status_code=400, detail="SMTP not configured for this account")

    password = decrypt(acc.password_enc)
    try:
        with SmtpClient(acc.smtp_host, acc.smtp_port, acc.smtp_tls) as smtp:
            smtp.login(acc.email, password)
            smtp.send_email(acc.email, str(payload.to_addr), payload.subject, payload.body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

    return {"ok": True}

@app.get("/threads/{thread_id}/suggest-reply")
def suggest_reply(thread_id: int, db: Session = Depends(get_db)):
    th = db.query(Thread).filter(Thread.id == thread_id).first()
    if not th:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Letzte Nachricht holen
    last_msg = db.query(Message).filter(Message.thread_id == thread_id).order_by(Message.date.desc().nullslast()).first()
    
    suggestion = generate_reply_suggestion(
        th.subject, 
        last_msg.snippet if last_msg else None
    )
    
    return {"suggestion": suggestion}
