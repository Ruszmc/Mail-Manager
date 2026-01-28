import email
import imaplib
import re
from datetime import datetime, timezone
from email.header import decode_header
from typing import Any


class ImapAuthenticationError(Exception):
    pass


class ImapClient:
    def __init__(self, host: str, port: int = 993, tls: bool = True):
        self.host = host
        self.port = port
        self.tls = tls
        self.conn: imaplib.IMAP4 | imaplib.IMAP4_SSL | None = None

    def __enter__(self):
        self.conn = imaplib.IMAP4_SSL(self.host, self.port) if self.tls else imaplib.IMAP4(self.host, self.port)
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.conn:
            try:
                self.conn.logout()
            except Exception:
                pass

    def login(self, email_addr: str, password: str) -> None:
        if not self.conn:
            raise RuntimeError("IMAP connection not initialized")
        try:
            self.conn.login(email_addr, password)
        except imaplib.IMAP4.error as exc:
            if "AUTH" in str(exc).upper():
                raise ImapAuthenticationError(str(exc))
            raise

    def select_inbox(self) -> None:
        if not self.conn:
            raise RuntimeError("IMAP connection not initialized")
        status, _ = self.conn.select("INBOX")
        if status != "OK":
            raise RuntimeError("Failed to select INBOX")

    def test_connection(self, email_addr: str, password: str) -> None:
        self.login(email_addr, password)
        self.select_inbox()

    def fetch_latest(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self.conn:
            raise RuntimeError("IMAP connection not initialized")
        status, data = self.conn.uid("search", None, "ALL")
        if status != "OK":
            return []
        uids = data[0].split() if data and data[0] else []
        if limit and len(uids) > limit:
            uids = uids[-limit:]
        results: list[dict[str, Any]] = []
        for uid_bytes in reversed(uids):
            status, msg_data = self.conn.uid("fetch", uid_bytes, "(RFC822.HEADER RFC822.TEXT)")
            if status != "OK" or not msg_data:
                continue
            raw = b"".join(part[1] for part in msg_data if isinstance(part, tuple) and isinstance(part[1], (bytes, bytearray)))
            if not raw:
                continue
            msg = email.message_from_bytes(raw)
            results.append(_extract_headers(msg, int(uid_bytes)))
        return results

    def fetch_body(self, uid: int) -> str:
        if not self.conn:
            raise RuntimeError("IMAP connection not initialized")
        status, msg_data = self.conn.uid("fetch", str(uid).encode(), "(RFC822)")
        if status != "OK" or not msg_data:
            raise RuntimeError("Failed to fetch message")
        raw = b"".join(part[1] for part in msg_data if isinstance(part, tuple) and isinstance(part[1], (bytes, bytearray)))
        msg = email.message_from_bytes(raw)
        return _extract_body(msg)


def _decode_header(value: str | None) -> str | None:
    if not value:
        return None
    parts = decode_header(value)
    decoded: list[str] = []
    for part, enc in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return "".join(decoded)


def _parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    try:
        dt = email.utils.parsedate_to_datetime(date_str)
        if dt and dt.tzinfo:
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except Exception:
        return None


def _extract_snippet(msg: email.message.Message, max_len: int = 240) -> str | None:
    text = _extract_body(msg)
    if not text:
        return None
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len]


def _extract_body(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_disposition() == "attachment":
                continue
            ctype = part.get_content_type()
            if ctype == "text/plain":
                payload = part.get_payload(decode=True) or b""
                return payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True) or b""
                html = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                text = re.sub(r"<[^>]+>", " ", html)
                return re.sub(r"\s+", " ", text).strip()
        return ""
    payload = msg.get_payload(decode=True) or b""
    return payload.decode(msg.get_content_charset() or "utf-8", errors="replace")


def _extract_headers(msg: email.message.Message, uid: int) -> dict[str, Any]:
    return {
        "uid": uid,
        "subject": _decode_header(msg.get("Subject")),
        "from": _decode_header(msg.get("From")),
        "to": _decode_header(msg.get("To")),
        "date": _parse_date(msg.get("Date")),
        "message_id": msg.get("Message-ID"),
        "in_reply_to": msg.get("In-Reply-To"),
        "references": msg.get("References"),
        "list_unsubscribe": msg.get("List-Unsubscribe"),
        "snippet": _extract_snippet(msg),
    }
