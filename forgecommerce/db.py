import sqlite3
from pathlib import Path

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS tenants (id TEXT PRIMARY KEY, name TEXT NOT NULL, slug TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS tenant_controls (tenant_id TEXT PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE, status TEXT NOT NULL DEFAULT 'active', updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES tenants(id), email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'owner', created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sessions (token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE, tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, expires_at TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS products (id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, name TEXT NOT NULL, slug TEXT NOT NULL, price_cents INTEGER NOT NULL CHECK(price_cents >= 0), inventory INTEGER NOT NULL DEFAULT 0 CHECK(inventory >= 0), status TEXT NOT NULL DEFAULT 'active', created_at TEXT NOT NULL, UNIQUE(tenant_id, slug));
CREATE TABLE IF NOT EXISTS product_variants (id TEXT PRIMARY KEY, product_id TEXT NOT NULL REFERENCES products(id) ON DELETE CASCADE, tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, sku TEXT NOT NULL, name TEXT NOT NULL, price_cents INTEGER NOT NULL CHECK(price_cents >= 0), inventory INTEGER NOT NULL DEFAULT 0 CHECK(inventory >= 0), created_at TEXT NOT NULL, UNIQUE(tenant_id, sku));
CREATE TABLE IF NOT EXISTS collections (id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, name TEXT NOT NULL, slug TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(tenant_id, slug));
CREATE TABLE IF NOT EXISTS collection_products (collection_id TEXT NOT NULL REFERENCES collections(id) ON DELETE CASCADE, product_id TEXT NOT NULL REFERENCES products(id) ON DELETE CASCADE, tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, PRIMARY KEY(collection_id, product_id));
CREATE TABLE IF NOT EXISTS carts (id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, customer_email TEXT, status TEXT NOT NULL DEFAULT 'open', created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS cart_items (cart_id TEXT NOT NULL REFERENCES carts(id) ON DELETE CASCADE, product_id TEXT NOT NULL REFERENCES products(id), quantity INTEGER NOT NULL CHECK(quantity > 0), unit_price_cents INTEGER NOT NULL, PRIMARY KEY(cart_id, product_id));
CREATE TABLE IF NOT EXISTS orders (id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, cart_id TEXT NOT NULL, customer_email TEXT NOT NULL, total_cents INTEGER NOT NULL, payment_status TEXT NOT NULL, fulfillment_status TEXT NOT NULL DEFAULT 'unfulfilled', idempotency_key TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(tenant_id, idempotency_key));
CREATE TABLE IF NOT EXISTS customers (id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, email TEXT NOT NULL, name TEXT, order_count INTEGER NOT NULL DEFAULT 0, total_spend_cents INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, UNIQUE(tenant_id, email));
CREATE TABLE IF NOT EXISTS order_items (order_id TEXT NOT NULL REFERENCES orders(id) ON DELETE CASCADE, product_id TEXT NOT NULL, name TEXT NOT NULL, quantity INTEGER NOT NULL, unit_price_cents INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS audit_events (id TEXT PRIMARY KEY, tenant_id TEXT, user_id TEXT, action TEXT NOT NULL, resource_type TEXT, resource_id TEXT, metadata_json TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS feature_flags (tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, name TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(tenant_id, name));
CREATE TABLE IF NOT EXISTS tenant_limits (tenant_id TEXT PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE, plan TEXT NOT NULL DEFAULT 'starter', product_limit INTEGER NOT NULL DEFAULT 100, page_limit INTEGER NOT NULL DEFAULT 20, staff_limit INTEGER NOT NULL DEFAULT 5);
CREATE TABLE IF NOT EXISTS subscriptions (id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, plan TEXT NOT NULL, status TEXT NOT NULL, provider TEXT NOT NULL DEFAULT 'sandbox', provider_reference TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, UNIQUE(tenant_id));
CREATE TABLE IF NOT EXISTS domains (id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, hostname TEXT NOT NULL UNIQUE, verification_hash TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', created_at TEXT NOT NULL, verified_at TEXT);
CREATE TABLE IF NOT EXISTS blog_posts (id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, slug TEXT NOT NULL, title TEXT NOT NULL, excerpt TEXT NOT NULL, content TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'draft', created_at TEXT NOT NULL, published_at TEXT, UNIQUE(tenant_id, slug));
CREATE TABLE IF NOT EXISTS api_keys (id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE, name TEXT NOT NULL, key_hash TEXT NOT NULL UNIQUE, prefix TEXT NOT NULL, created_at TEXT NOT NULL, revoked_at TEXT);
CREATE TABLE IF NOT EXISTS webhooks (id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, url TEXT NOT NULL, secret TEXT NOT NULL, events_json TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS webhook_deliveries (id TEXT PRIMARY KEY, webhook_id TEXT NOT NULL REFERENCES webhooks(id) ON DELETE CASCADE, event_type TEXT NOT NULL, payload_json TEXT NOT NULL, signature TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'queued', created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS schema_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS pages (id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, slug TEXT NOT NULL, title TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'draft', published_version INTEGER, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, UNIQUE(tenant_id, slug));
CREATE TABLE IF NOT EXISTS page_versions (page_id TEXT NOT NULL REFERENCES pages(id) ON DELETE CASCADE, version INTEGER NOT NULL, content_json TEXT NOT NULL, seo_json TEXT NOT NULL, created_by TEXT NOT NULL, created_at TEXT NOT NULL, PRIMARY KEY(page_id, version));
CREATE TABLE IF NOT EXISTS page_translations (page_id TEXT NOT NULL REFERENCES pages(id) ON DELETE CASCADE, locale TEXT NOT NULL, content_json TEXT NOT NULL, seo_json TEXT NOT NULL, created_by TEXT NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY(page_id, locale));
CREATE INDEX IF NOT EXISTS idx_products_tenant ON products(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_tenant_time ON audit_events(tenant_id, created_at);
"""

def connect(path: str) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    # The HTTP server dispatches requests on worker threads. SQLite serializes
    # writes here; the service layer still uses short explicit transactions.
    conn = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.executescript(SCHEMA)
    conn.execute("INSERT OR IGNORE INTO schema_meta(key,value) VALUES ('schema_version','1')")
    return conn
