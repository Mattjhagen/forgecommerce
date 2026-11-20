# Feature Matrix

Statuses: `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `IMPLEMENTED`, `VERIFIED`. Only `VERIFIED` counts toward completion.

| Area | Capability | Status | Evidence |
|---|---|---|---|
| Foundation | Configuration, schema, migrations, auth, tenants, audit, flags | VERIFIED | `tests/test_commerce.py`, `tests/test_api.py` |
| Builder | Pages, sections, responsive preview, versions, publish, rollback | IN_PROGRESS | `/editor`, `/store/{slug}`, `tests/test_api.py`, `tests/test_commerce.py` (rollback verified; richer component library remains) |
| Commerce | Products, variants, inventory, carts, sandbox checkout, orders | IN_PROGRESS | `tests/test_commerce.py`, `tests/test_api.py` (variants/SKUs/collections verified; provider integrations remain) |
| Operations | Analytics, customers, imports, staff roles, billing | IN_PROGRESS | `tests/test_commerce.py` (customers/order search/staff roles; analytics/imports/billing remain) |
| Advanced | REST API, webhooks, domains, SEO, CMS, i18n, search | NOT_STARTED | |
| Administration | Super-admin, quotas, health, backups, migration controls | IN_PROGRESS | `forgecommerce/backup.py`, `tests/test_backup.py` (backup/restore verified; super-admin/quotas remain) |
| Security | Isolation, authz, validation, rate limits, XSS/CSRF, idempotency | IN_PROGRESS | `tests/test_commerce.py` (isolation, auth, validation, idempotency) |

The matrix is intentionally conservative while the first foundation checkpoint is being built.
