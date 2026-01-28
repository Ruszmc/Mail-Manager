import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()

def _load_or_create_key() -> bytes:
    env_key = os.getenv("MP_FERNET_KEY")
    if env_key:
        return env_key.encode() if isinstance(env_key, str) else env_key

    key_file = os.getenv("MP_FERNET_KEY_FILE", ".mp_fernet_key")
    if os.path.exists(key_file):
        with open(key_file, "rb") as handle:
            return handle.read().strip()

    key = Fernet.generate_key()
    with open(key_file, "wb") as handle:
        handle.write(key)
    return key


fernet = Fernet(_load_or_create_key())

def encrypt(s: str) -> str:
    return fernet.encrypt(s.encode("utf-8")).decode("utf-8")

def decrypt(token: str) -> str:
    return fernet.decrypt(token.encode("utf-8")).decode("utf-8")
