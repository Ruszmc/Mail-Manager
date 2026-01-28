import smtplib
from email.message import EmailMessage

class SmtpClient:
    def __init__(self, host: str, port: int = 587, tls: bool = True):
        self.host = host
        self.port = port
        self.tls = tls
        self.server = None

    def __enter__(self):
        if self.tls:
            self.server = smtplib.SMTP(self.host, self.port)
            self.server.starttls()
        else:
            self.server = smtplib.SMTP(self.host, self.port)
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.server:
            try:
                self.server.quit()
            except:
                pass

    def login(self, email_addr: str, password: str):
        if self.server:
            self.server.login(email_addr, password)

    def send_email(self, from_addr: str, to_addr: str, subject: str, body: str):
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to_addr

        if self.server:
            self.server.send_message(msg)
