# Feature Matrix

Statuses: `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `IMPLEMENTED`, `VERIFIED`. Only `VERIFIED` counts toward completion.

| Area | Capability | Status | Evidence |
|---|---|---|---|
| Foundation | Configuration, schema, migrations, auth, tenants, audit, flags | IN_PROGRESS | `forgecommerce/` and `tests/test_foundation.py` |
| Builder | Pages, sections, responsive preview, versions, publish, rollback | NOT_STARTED | |
| Commerce | Products, variants, inventory, carts, sandbox checkout, orders | IN_PROGRESS | `tests/test_commerce.py` |
| Operations | Analytics, customers, imports, staff roles, billing | NOT_STARTED | |
| Advanced | REST API, webhooks, domains, SEO, CMS, i18n, search | NOT_STARTED | |
| Administration | Super-admin, quotas, health, backups, migration controls | IN_PROGRESS | `forgecommerce/backup.py` |
| Security | Isolation, authz, validation, rate limits, XSS/CSRF, idempotency | IN_PROGRESS | `tests/test_security.py` |

The matrix is intentionally conservative while the first foundation checkpoint is being built.
