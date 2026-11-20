"""Explicit local migration control surface."""
CURRENT_SCHEMA_VERSION=1

def status(conn):
    row=conn.execute("SELECT value FROM schema_meta WHERE key='schema_version'").fetchone()
    current=int(row[0]) if row else 0
    return {"current":current,"latest":CURRENT_SCHEMA_VERSION,"pending":max(CURRENT_SCHEMA_VERSION-current,0)}

def apply(conn):
    state=status(conn)
    if state["current"] > CURRENT_SCHEMA_VERSION: raise RuntimeError("database schema is newer than this application")
    if state["current"] < CURRENT_SCHEMA_VERSION:
        conn.execute("INSERT INTO schema_meta(key,value) VALUES ('schema_version',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(str(CURRENT_SCHEMA_VERSION),))
    return status(conn)
