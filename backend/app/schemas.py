from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class AccountCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)
    imap_host: str
    imap_port: int = 993
    imap_tls: bool = True
    smtp_host: str
    smtp_port: int = 587
    smtp_tls: bool = True


class AccountOut(BaseModel):
    id: int
    email: EmailStr
    imap_host: str
    imap_port: int
    imap_tls: bool
    smtp_host: str
    smtp_port: int
    smtp_tls: bool

    class Config:
        from_attributes = True


class SyncRequest(BaseModel):
    limit: int = 50


class ThreadOut(BaseModel):
    id: int
    subject: str | None
    last_message_at: datetime | None
    category: str
    priority_score: int
    priority_reason: str
    is_newsletter: bool

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    id: int
    imap_uid: int
    message_id: str | None
    in_reply_to: str | None
    references: str | None
    from_addr: str | None
    to_addr: str | None
    subject: str | None
    date: datetime | None
    list_unsubscribe: str | None
    snippet: str | None

    class Config:
        from_attributes = True


class SendEmailRequest(BaseModel):
    to_addr: EmailStr
    subject: str
    body: str


class TestConnectionRequest(BaseModel):
    email: EmailStr
    password: str
    imap_host: str
    imap_port: int = 993
    imap_tls: bool = True


class InsightsResponse(BaseModel):
    summary: str
    actions: list[str]
    labels: list[str]


class UnsubscribeOptions(BaseModel):
    mailto: list[str] = []
    urls: list[str] = []


class MessageBodyResponse(BaseModel):
    body: str


class AiRequest(BaseModel):
    subject: str | None = None
    snippet: str | None = None
    body: str | None = None
    language: str | None = None


class AiResponse(BaseModel):
    result: str
