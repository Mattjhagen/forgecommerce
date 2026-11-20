import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    db_path: str = os.getenv("FORGECOMMERCE_DB", "forgecommerce.sqlite3")
    host: str = os.getenv("FORGECOMMERCE_HOST", "127.0.0.1")
    port: int = int(os.getenv("FORGECOMMERCE_PORT", "8080"))
    session_hours: int = int(os.getenv("FORGECOMMERCE_SESSION_HOURS", "24"))
    max_body_bytes: int = int(os.getenv("FORGECOMMERCE_MAX_BODY", "1048576"))
