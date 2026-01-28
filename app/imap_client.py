import imaplib
import email
from email.header import decode_header
from datetime import datetime, timezone
import re

def _decode_header(value: str | None) -> str | None:
    if not value:
        return None
    parts = decode_header(value)
    out = []
    for p, enc in parts:
        if isinstance(p, bytes):
            out.append(p.decode(enc or "utf-8", errors="replace"))
        else:
            out.append(p)
    return "".join(out)

def _parse_date(date_str: str | None):
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
    # MVP: try text/plain first, fallback to stripped html.
    text = None
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = (part.get("Content-Disposition") or "").lower()
            if "attachment" in disp:
                continue
            if ctype == "text/plain":
                payload = part.get_payload(decode=True) or b""
                text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                break
        if text is None:
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    payload = part.get_payload(decode=True) or b""
                    html = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                    text = re.sub(r"<[^>]+>", " ", html)
                    text = re.sub(r"\s+", " ", text).strip()
                    break
    else:
        payload = msg.get_payload(decode=True) or b""
        text = payload.decode(msg.get_content_charset() or "utf-8", errors="replace")

    if not text:
        return None
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len]

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
        try:
            if self.conn:
                self.conn.logout()
        except Exception:
            pass

    def login(self, email_addr: str, password: str):
        assert self.conn is not None
        try:
            self.conn.login(email_addr, password)
        except imaplib.IMAP4.error as e:
            if "AUTHENTICATIONFAILED" in str(e).upper():
                raise ImapAuthenticationError(f"IMAP authentication failed: {str(e)}")
            raise Exception(f"IMAP login failed: {str(e)}")
        except Exception as e:
            raise Exception(f"IMAP login failed: {str(e)}")

    def select_inbox(self):
        assert self.conn is not None
        try:
            self.conn.select("INBOX")
        except Exception as e:
            raise Exception(f"Failed to select INBOX: {str(e)}")

    def fetch_latest(self, limit: int = 50):
        """
        Returns list of dict:
        {uid:int, subject, from, to, date, list_unsubscribe, snippet}
        """
        assert self.conn is not None
        typ, data = self.conn.uid("search", None, "ALL")
        if typ != "OK":
            return []

        uids = data[0].split()
        uids = uids[-limit:] if limit and len(uids) > limit else uids

        results = []
        for uid_b in reversed(uids):
            uid = int(uid_b)
            typ, msg_data = self.conn.uid("fetch", uid_b, "(RFC822.HEADER RFC822.TEXT)")
            if typ != "OK" or not msg_data or not msg_data[0]:
                continue

            # msg_data is list like [(b'UID ...', header_bytes), (b'...', text_bytes)]
            # imaplib formats vary; simplest: fetch full RFC822 would be heavier.
            header_bytes = msg_data[0][1] if isinstance(msg_data[0], tuple) else None
            # Some servers include TEXT separately; we reconstruct via email parser:
            full_bytes = b""
            for item in msg_data:
                if isinstance(item, tuple) and isinstance(item[1], (bytes, bytearray)):
                    full_bytes += item[1]
            if not full_bytes and header_bytes:
                full_bytes = header_bytes

            try:
                msg = email.message_from_bytes(full_bytes)
            except Exception:
                continue

            subject = _decode_header(msg.get("Subject"))
            from_addr = _decode_header(msg.get("From"))
            to_addr = _decode_header(msg.get("To"))
            date = _parse_date(msg.get("Date"))
            list_unsub = msg.get("List-Unsubscribe")

            snippet = _extract_snippet(msg)

            results.append({
                "uid": uid,
                "subject": subject,
                "from": from_addr,
                "to": to_addr,
                "date": date,
                "list_unsubscribe": list_unsub,
                "snippet": snippet,
            })
        return results
