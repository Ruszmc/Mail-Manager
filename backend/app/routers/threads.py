from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Thread, Message, Subscription
from ..schemas import ThreadOut, MessageOut, InsightsResponse, UnsubscribeOptions, MessageBodyResponse
from ..services.imap_client import ImapClient
from ..services.crypto import decrypt
from ..services.classifier import guess_category
from ..services.ai import summarize as ai_summarize, extract_actions as ai_actions, draft_reply as ai_draft
from ..services.unsubscribe import parse_list_unsubscribe

router = APIRouter(prefix="/threads", tags=["threads"])


@router.get("/account/{account_id}", response_model=list[ThreadOut])
def list_threads(account_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Thread)
        .filter(Thread.account_id == account_id)
        .order_by(Thread.priority_score.desc(), Thread.last_message_at.desc().nullslast())
        .limit(200)
        .all()
    )


@router.get("/{thread_id}/messages", response_model=list[MessageOut])
def thread_messages(thread_id: int, db: Session = Depends(get_db)):
    thread = db.query(Thread).filter(Thread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return (
        db.query(Message)
        .filter(Message.thread_id == thread_id)
        .order_by(Message.date.desc().nullslast())
        .all()
    )


@router.get("/messages/{message_id}/body", response_model=MessageBodyResponse)
def message_body(message_id: int, db: Session = Depends(get_db)):
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    account = message.thread.account
    password = decrypt(account.password_enc)
    try:
        with ImapClient(account.imap_host, account.imap_port, account.imap_tls) as imap:
            imap.login(account.email, password)
            imap.select_inbox()
            body = imap.fetch_body(message.imap_uid)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch body: {exc}")
    return MessageBodyResponse(body=body)


@router.get("/{thread_id}/insights", response_model=InsightsResponse)
def thread_insights(thread_id: int, db: Session = Depends(get_db)):
    thread = db.query(Thread).filter(Thread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    last_msg = (
        db.query(Message)
        .filter(Message.thread_id == thread_id)
        .order_by(Message.date.desc().nullslast())
        .first()
    )
    subject = thread.subject
    snippet = last_msg.snippet if last_msg else None
    summary = f"Zusammenfassung: {subject or 'Ohne Betreff'}"
    actions = ["Antwort vorbereiten", "Falls nötig archivieren"]
    labels = [guess_category(subject, snippet, thread.is_newsletter)]
    return InsightsResponse(summary=summary, actions=actions, labels=labels)


@router.get("/newsletters/{account_id}")
def newsletters(account_id: int, db: Session = Depends(get_db)):
    subs = db.query(Subscription).filter(Subscription.account_id == account_id).all()
    return [{"id": sub.id, "sender": sub.sender, "list_unsubscribe": sub.list_unsubscribe} for sub in subs]


@router.get("/newsletters/{subscription_id}/unsubscribe", response_model=UnsubscribeOptions)
def unsubscribe_options(subscription_id: int, db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    links = parse_list_unsubscribe(sub.list_unsubscribe)
    return UnsubscribeOptions(mailto=links.mailto, urls=links.urls)


@router.post("/{thread_id}/ai/summarize")
def ai_summary(thread_id: int, db: Session = Depends(get_db)):
    thread = db.query(Thread).filter(Thread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    last_msg = db.query(Message).filter(Message.thread_id == thread_id).order_by(Message.date.desc().nullslast()).first()
    result = ai_summarize(thread.subject, last_msg.snippet if last_msg else None, None)
    return {"result": result}


@router.post("/{thread_id}/ai/actions")
def ai_actions_endpoint(thread_id: int, db: Session = Depends(get_db)):
    thread = db.query(Thread).filter(Thread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    last_msg = db.query(Message).filter(Message.thread_id == thread_id).order_by(Message.date.desc().nullslast()).first()
    result = ai_actions(thread.subject, last_msg.snippet if last_msg else None, None)
    return {"result": result}


@router.post("/{thread_id}/ai/draft")
def ai_draft_endpoint(thread_id: int, payload: dict, db: Session = Depends(get_db)):
    thread = db.query(Thread).filter(Thread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    last_msg = db.query(Message).filter(Message.thread_id == thread_id).order_by(Message.date.desc().nullslast()).first()
    result = ai_draft(thread.subject, last_msg.snippet if last_msg else None, None, payload.get("language"))
    return {"result": result}
