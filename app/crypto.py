import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()

key = os.getenv("MP_FERNET_KEY")
if not key:
    raise RuntimeError("MP_FERNET_KEY missing. Put it in your .env")

fernet = Fernet(key.encode() if isinstance(key, str) else key)

def encrypt(s: str) -> str:
    return fernet.encrypt(s.encode("utf-8")).decode("utf-8")

def decrypt(token: str) -> str:
    return fernet.decrypt(token.encode("utf-8")).decode("utf-8")
