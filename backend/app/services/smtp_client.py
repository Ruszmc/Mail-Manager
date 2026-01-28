import smtplib
from email.message import EmailMessage


class SmtpClient:
    def __init__(self, host: str, port: int = 587, tls: bool = True):
        self.host = host
        self.port = port
        self.tls = tls
        self.server: smtplib.SMTP | None = None

    def __enter__(self):
        self.server = smtplib.SMTP(self.host, self.port, timeout=10)
        if self.tls:
            self.server.starttls()
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.server:
            try:
                self.server.quit()
            except Exception:
                pass

    def login(self, email_addr: str, password: str) -> None:
        if not self.server:
            raise RuntimeError("SMTP connection not initialized")
        self.server.login(email_addr, password)

    def send_email(self, from_addr: str, to_addr: str, subject: str, body: str) -> None:
        if not self.server:
            raise RuntimeError("SMTP connection not initialized")
        msg = EmailMessage()
        msg["From"] = from_addr
        msg["To"] = to_addr
        msg["Subject"] = subject
        msg.set_content(body)
        self.server.send_message(msg)
