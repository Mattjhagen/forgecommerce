# Feature Matrix

Statuses: `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `IMPLEMENTED`, `VERIFIED`. Only `VERIFIED` counts toward completion.

| Area | Capability | Status | Evidence |
|---|---|---|---|
| Foundation | Configuration, schema, migrations, auth, tenants, audit, flags | VERIFIED | `tests/test_commerce.py`, `tests/test_api.py` |
| Builder | Pages, sections, responsive preview, versions, publish, rollback | IN_PROGRESS | `/editor`, `/store/{slug}`, `tests/test_api.py`, `tests/test_commerce.py` (rollback verified; richer component library remains) |
| Commerce | Products, variants, inventory, carts, sandbox checkout, orders | IN_PROGRESS | `tests/test_commerce.py`, `tests/test_api.py`, `tests/test_payments.py` (sandbox provider contract verified; live provider remains) |
| Operations | Analytics, customers, imports, staff roles, billing | IN_PROGRESS | CSV import/export, analytics/customers/order search/staff roles, and sandbox subscriptions verified; live billing remains |
| Advanced | REST API, webhooks, domains, SEO, CMS, i18n, search | IN_PROGRESS | API keys, signed webhooks, public search, sitemap, published-page SEO, and locale fallback verified in tests; domains/CMS remain |
| Administration | Super-admin, quotas, health, backups, migration controls | IN_PROGRESS | Platform-admin tenant provisioning/listing/suspension, `/api/admin/health`, `/api/admin/usage`, and backup/restore verified; migration controls remain |
| Security | Isolation, authz, validation, rate limits, XSS/CSRF, idempotency | IN_PROGRESS | `tests/test_commerce.py` (isolation, auth, validation, idempotency) |

The matrix is intentionally conservative while the first foundation checkpoint is being built.
