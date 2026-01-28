from __future__ import annotations

from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    imap_host: Mapped[str] = mapped_column(String(255), nullable=False)
    imap_port: Mapped[int] = mapped_column(Integer, nullable=False, default=993)
    imap_tls: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    smtp_host: Mapped[str] = mapped_column(String(255), nullable=False)
    smtp_port: Mapped[int] = mapped_column(Integer, nullable=False, default=587)
    smtp_tls: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    password_enc: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    threads: Mapped[list[Thread]] = relationship(back_populates="account", cascade="all, delete-orphan")


class Thread(Base):
    __tablename__ = "threads"
    __table_args__ = (UniqueConstraint("account_id", "thread_key", name="uq_thread_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    thread_key: Mapped[str] = mapped_column(String(512), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(512))
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime)
    category: Mapped[str] = mapped_column(String(64), default="general")
    priority_score: Mapped[int] = mapped_column(Integer, default=0)
    priority_reason: Mapped[str] = mapped_column(String(255), default="")
    is_newsletter: Mapped[bool] = mapped_column(Boolean, default=False)

    account: Mapped[Account] = relationship(back_populates="threads")
    messages: Mapped[list[Message]] = relationship(back_populates="thread", cascade="all, delete-orphan")
    labels: Mapped[list[ThreadLabel]] = relationship(back_populates="thread", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (UniqueConstraint("thread_id", "imap_uid", name="uq_imap_uid"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    thread_id: Mapped[int] = mapped_column(ForeignKey("threads.id"), nullable=False)
    imap_uid: Mapped[int] = mapped_column(Integer, nullable=False)
    message_id: Mapped[str | None] = mapped_column(String(512))
    in_reply_to: Mapped[str | None] = mapped_column(String(512))
    references: Mapped[str | None] = mapped_column(Text)
    from_addr: Mapped[str | None] = mapped_column(String(512))
    to_addr: Mapped[str | None] = mapped_column(String(1024))
    subject: Mapped[str | None] = mapped_column(String(512))
    date: Mapped[datetime | None] = mapped_column(DateTime)
    list_unsubscribe: Mapped[str | None] = mapped_column(Text)
    snippet: Mapped[str | None] = mapped_column(Text)

    thread: Mapped[Thread] = relationship(back_populates="messages")


class Label(Base):
    __tablename__ = "labels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)


class ThreadLabel(Base):
    __tablename__ = "thread_labels"
    __table_args__ = (UniqueConstraint("thread_id", "label_id", name="uq_thread_label"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    thread_id: Mapped[int] = mapped_column(ForeignKey("threads.id"), nullable=False)
    label_id: Mapped[int] = mapped_column(ForeignKey("labels.id"), nullable=False)

    thread: Mapped[Thread] = relationship(back_populates="labels")
    label: Mapped[Label] = relationship()


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    sender: Mapped[str] = mapped_column(String(512), nullable=False)
    list_unsubscribe: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class ActionItem(Base):
    __tablename__ = "action_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    thread_id: Mapped[int] = mapped_column(ForeignKey("threads.id"), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
