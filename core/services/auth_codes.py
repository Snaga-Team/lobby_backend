import secrets, hashlib
from django.core.cache import caches
from django.conf import settings

CACHE = caches["auth_codes"]
CODE_TTL = 600
THROTTLE_TTL = 60
MAX_ATTEMPTS = 5
SALT = (settings.SECRET_KEY[:32] if settings.SECRET_KEY else "salt")

def gen_code() -> str:
    return str(secrets.randbelow(10**6)).zfill(6)

def _key_code(user_id: int) -> str:
    return f"auth:pr:code:{user_id}"

def _key_throttle(email: str) -> str:
    return f"auth:pr:throttle:{email.lower()}"

def _key_attempts(user_id: int) -> str:
    return f"auth:pr:attempts:{user_id}"

def _hash(code: str) -> str:
    return hashlib.sha256((SALT + code).encode()).hexdigest()

def can_send(email: str) -> bool:
    return CACHE.add(_key_throttle(email), "1", timeout=THROTTLE_TTL)

def store_code(user_id: int, code: str) -> None:
    CACHE.set(_key_code(user_id), _hash(code), timeout=CODE_TTL)
    CACHE.delete(_key_attempts(user_id))

def verify_code(user_id: int, code: str) -> bool:
    attempts_key = _key_attempts(user_id)
    attempts = CACHE.incr(attempts_key) if CACHE.get(attempts_key) else (CACHE.set(attempts_key, 1, CODE_TTL) or 1)
    if attempts > MAX_ATTEMPTS:
        return False
    stored = CACHE.get(_key_code(user_id))
    if not stored:
        return False
    ok = secrets.compare_digest(stored, _hash(code))
    if ok:
        CACHE.delete_many([_key_code(user_id), attempts_key])
    return ok

def peek_code(user_id: int, code: str) -> bool:
    stored = CACHE.get(_key_code(user_id))
    if not stored:
        return False
    return secrets.compare_digest(stored, _hash(code))
