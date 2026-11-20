# Operations

## Local staging

```bash
python3 -m forgecommerce.app
curl http://127.0.0.1:8080/health
```

Set `FORGECOMMERCE_DB` to choose a database path and `FORGECOMMERCE_PORT` to choose a port. `python3 -m forgecommerce.backup DB_PATH OUTPUT_PATH` creates a consistent SQLite backup.

The supervisor is `scripts/forgecommerce-supervisor.py`; it uses a lock file, bounded restart attempts, and graceful SIGTERM handling. It is a local design and is not installed as a system service automatically.
