from dataclasses import dataclass


@dataclass(frozen=True)
class MailProviderConfig:
    imap_host: str
    imap_port: int = 993
    imap_tls: bool = True
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_tls: bool = True


PROVIDERS: dict[str, MailProviderConfig] = {
    "gmail.com": MailProviderConfig(imap_host="imap.gmail.com", smtp_host="smtp.gmail.com"),
    "googlemail.com": MailProviderConfig(imap_host="imap.gmail.com", smtp_host="smtp.gmail.com"),
    "outlook.com": MailProviderConfig(imap_host="imap-mail.outlook.com", smtp_host="smtp-mail.outlook.com"),
    "hotmail.com": MailProviderConfig(imap_host="imap-mail.outlook.com", smtp_host="smtp-mail.outlook.com"),
    "live.com": MailProviderConfig(imap_host="imap-mail.outlook.com", smtp_host="smtp-mail.outlook.com"),
    "office365.com": MailProviderConfig(imap_host="outlook.office365.com", smtp_host="smtp.office365.com"),
    "yahoo.com": MailProviderConfig(imap_host="imap.mail.yahoo.com", smtp_host="smtp.mail.yahoo.com"),
    "yahoo.de": MailProviderConfig(imap_host="imap.mail.yahoo.com", smtp_host="smtp.mail.yahoo.com"),
    "icloud.com": MailProviderConfig(imap_host="imap.mail.me.com", smtp_host="smtp.mail.me.com"),
    "me.com": MailProviderConfig(imap_host="imap.mail.me.com", smtp_host="smtp.mail.me.com"),
    "gmx.de": MailProviderConfig(imap_host="imap.gmx.net", smtp_host="smtp.gmx.net"),
    "gmx.net": MailProviderConfig(imap_host="imap.gmx.net", smtp_host="smtp.gmx.net"),
    "web.de": MailProviderConfig(imap_host="imap.web.de", smtp_host="smtp.web.de"),
    "t-online.de": MailProviderConfig(imap_host="imap.t-online.de", smtp_host="smtp.t-online.de"),
}


def discover_provider(email_addr: str) -> MailProviderConfig | None:
    domain = email_addr.split("@")[-1].lower() if "@" in email_addr else ""
    return PROVIDERS.get(domain)


def guess_imap_host(email_addr: str) -> str | None:
    domain = email_addr.split("@")[-1].lower() if "@" in email_addr else ""
    if not domain:
        return None
    return f"imap.{domain}"


def guess_smtp_host(email_addr: str, imap_host: str | None) -> str | None:
    if imap_host and imap_host.startswith("imap."):
        return "smtp." + imap_host[len("imap."):]
    domain = email_addr.split("@")[-1].lower() if "@" in email_addr else ""
    if not domain:
        return None
    return f"smtp.{domain}"
