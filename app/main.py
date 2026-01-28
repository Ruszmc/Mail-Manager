from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, EmailStr, ConfigDict
from sqlalchemy.orm import Session
from datetime import datetime
from dotenv import load_dotenv

from .db import Base, engine, get_db
from .models import Account, Thread, Message
from .crypto import encrypt, decrypt
from .imap_client import ImapClient
from .classifier import thread_key, is_newsletter, category_guess, priority_score

load_dotenv()
Base.metadata.create_all(bind=engine)

app = FastAPI(title="MailPilot Skeleton", version="0.1.0")

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

    with ImapClient(acc.imap_host, acc.imap_port, acc.imap_tls) as imap:
        imap.login(acc.email, password)
        imap.select_inbox()
        msgs = imap.fetch_latest(limit=payload.limit)

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
