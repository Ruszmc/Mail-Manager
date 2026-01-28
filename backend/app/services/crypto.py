import os
from cryptography.fernet import Fernet


def get_fernet() -> Fernet:
    key = os.getenv("MAILPILOT_FERNET_KEY")
    if not key:
        raise RuntimeError("MAILPILOT_FERNET_KEY is missing. Generate one with `python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"`.")
    return Fernet(key.encode())


def encrypt(value: str) -> str:
    return get_fernet().encrypt(value.encode()).decode()


def decrypt(token: str) -> str:
    return get_fernet().decrypt(token.encode()).decode()
