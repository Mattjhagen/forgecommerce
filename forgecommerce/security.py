import hashlib, hmac, secrets, threading, time

ITERATIONS = 210_000

def hash_password(password: str) -> str:
    if len(password) < 10:
        raise ValueError("password must be at least 10 characters")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}"

def verify_password(password: str, encoded: str) -> bool:
    try:
        _, iterations, salt, expected = encoded.split("$")
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(iterations)).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False

def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def api_key_hash(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()

def new_id() -> str:
    return secrets.token_urlsafe(16)

class RateLimiter:
    """Small process-local limiter for local staging; production should use a shared store."""
    def __init__(self, limit=120, window_seconds=60):
        self.limit, self.window = limit, window_seconds; self._hits={}; self._lock=threading.Lock()
    def allow(self, key, now=None):
        current=now if now is not None else time.monotonic()
        with self._lock:
            hits=[stamp for stamp in self._hits.get(key,[]) if current-stamp < self.window]
            if len(hits) >= self.limit: self._hits[key]=hits; return False
            hits.append(current); self._hits[key]=hits
            if len(self._hits)>10000: self._hits={k:v for k,v in self._hits.items() if v}
            return True
