from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from .db import Base

class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)

    imap_host: Mapped[str] = mapped_column(String(255), nullable=False)
    imap_port: Mapped[int] = mapped_column(Integer, nullable=False, default=993)
    imap_tls: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    smtp_host: Mapped[str] = mapped_column(String(255), nullable=True)
    smtp_port: Mapped[int] = mapped_column(Integer, nullable=True, default=587)
    smtp_tls: Mapped[bool] = mapped_column(Boolean, nullable=True, default=True)

    password_enc: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    threads: Mapped[list["Thread"]] = relationship(back_populates="account", cascade="all, delete-orphan")


class Thread(Base):
    __tablename__ = "threads"
    __table_args__ = (UniqueConstraint("account_id", "provider_thread_key", name="uq_thread"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)

    # For IMAP we create our own "thread key" initially: normalized subject + from-domain (MVP).
    provider_thread_key: Mapped[str] = mapped_column(String(512), nullable=False)

    subject: Mapped[str] = mapped_column(String(512), nullable=True)
    last_msg_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    category: Mapped[str] = mapped_column(String(64), nullable=False, default="unknown")
    priority_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_newsletter: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    account: Mapped["Account"] = relationship(back_populates="threads")
    messages: Mapped[list["Message"]] = relationship(back_populates="thread", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (UniqueConstraint("thread_id", "imap_uid", name="uq_msg_uid"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    thread_id: Mapped[int] = mapped_column(ForeignKey("threads.id"), nullable=False)

    imap_uid: Mapped[int] = mapped_column(Integer, nullable=False)

    date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    from_addr: Mapped[str] = mapped_column(String(512), nullable=True)
    to_addr: Mapped[str] = mapped_column(String(1024), nullable=True)
    subject: Mapped[str] = mapped_column(String(512), nullable=True)

    list_unsubscribe: Mapped[str] = mapped_column(Text, nullable=True)
    snippet: Mapped[str] = mapped_column(Text, nullable=True)

    thread: Mapped["Thread"] = relationship(back_populates="messages")
