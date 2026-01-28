from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Account, Subscription
from ..schemas import AccountCreate, AccountOut, SendEmailRequest, SyncRequest, TestConnectionRequest
from ..services.crypto import encrypt, decrypt
from ..services.imap_client import ImapClient, ImapAuthenticationError
from ..services.smtp_client import SmtpClient
from ..services.classifier import is_newsletter, guess_category, priority, thread_key

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=list[AccountOut])
def list_accounts(db: Session = Depends(get_db)):
    return db.query(Account).order_by(Account.id.desc()).all()


@router.post("", response_model=AccountOut)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)):
    existing = db.query(Account).filter(Account.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Account already exists")
    account = Account(
        email=str(payload.email),
        imap_host=payload.imap_host,
        imap_port=payload.imap_port,
        imap_tls=payload.imap_tls,
        smtp_host=payload.smtp_host,
        smtp_port=payload.smtp_port,
        smtp_tls=payload.smtp_tls,
        password_enc=encrypt(payload.password),
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.post("/test")
def test_connection(payload: TestConnectionRequest):
    try:
        with ImapClient(payload.imap_host, payload.imap_port, payload.imap_tls) as imap:
            imap.test_connection(str(payload.email), payload.password)
    except ImapAuthenticationError:
        raise HTTPException(status_code=401, detail="Invalid IMAP credentials")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"IMAP connection failed: {exc}")
    return {"ok": True}


@router.post("/{account_id}/sync")
def sync_account(account_id: int, payload: SyncRequest, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    password = decrypt(account.password_enc)
    try:
        with ImapClient(account.imap_host, account.imap_port, account.imap_tls) as imap:
            imap.login(account.email, password)
            imap.select_inbox()
            messages = imap.fetch_latest(limit=payload.limit)
    except ImapAuthenticationError:
        raise HTTPException(status_code=401, detail="IMAP authentication failed")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Sync failed: {exc}")

    from ..models import Thread, Message

    new_messages = 0
    new_threads = 0

    for msg in messages:
        t_key = thread_key(msg.get("message_id"), msg.get("in_reply_to"), msg.get("references"), msg.get("subject"), msg.get("from"))
        thread = (
            db.query(Thread)
            .filter(Thread.account_id == account.id, Thread.thread_key == t_key)
            .first()
        )
        if not thread:
            thread = Thread(account_id=account.id, thread_key=t_key, subject=msg.get("subject"))
            db.add(thread)
            db.flush()
            new_threads += 1
        newsletter = is_newsletter(msg.get("list_unsubscribe"), msg.get("snippet"))
        category = guess_category(msg.get("subject"), msg.get("snippet"), newsletter)
        score, reason = priority(msg.get("subject"), msg.get("snippet"), newsletter)
        thread.category = category
        thread.priority_score = score
        thread.priority_reason = reason
        thread.is_newsletter = newsletter
        if msg.get("date") and (thread.last_message_at is None or msg["date"] > thread.last_message_at):
            thread.last_message_at = msg["date"]
            thread.subject = msg.get("subject") or thread.subject

        existing_msg = db.query(Message).filter(Message.thread_id == thread.id, Message.imap_uid == msg["uid"]).first()
        if existing_msg:
            continue
        message = Message(
            thread_id=thread.id,
            imap_uid=msg["uid"],
            message_id=msg.get("message_id"),
            in_reply_to=msg.get("in_reply_to"),
            references=msg.get("references"),
            from_addr=msg.get("from"),
            to_addr=msg.get("to"),
            subject=msg.get("subject"),
            date=msg.get("date"),
            list_unsubscribe=msg.get("list_unsubscribe"),
            snippet=msg.get("snippet"),
        )
        db.add(message)
        new_messages += 1

        if newsletter and msg.get("from"):
            sender = msg.get("from")
            if not db.query(Subscription).filter(Subscription.account_id == account.id, Subscription.sender == sender).first():
                db.add(Subscription(account_id=account.id, sender=sender, list_unsubscribe=msg.get("list_unsubscribe")))

    db.commit()
    return {"threads_new": new_threads, "messages_new": new_messages}


@router.post("/{account_id}/send")
def send_email(account_id: int, payload: SendEmailRequest, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    password = decrypt(account.password_enc)
    try:
        with SmtpClient(account.smtp_host, account.smtp_port, account.smtp_tls) as smtp:
            smtp.login(account.email, password)
            smtp.send_email(account.email, str(payload.to_addr), payload.subject, payload.body)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"SMTP failed: {exc}")
    return {"ok": True}
