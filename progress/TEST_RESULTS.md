# Test Results

## 2026-11-19 — Infrastructure checkpoint

- `python3 -m unittest discover -s tests -v`: PASS (2 tests).
- Current full suite `python3 -m unittest discover -s tests -v`: PASS (8 tests), including localhost HTTP integration.
- Expanded full suite `python3 -m unittest discover -s tests -v`: PASS (10 tests), including public storefront guest checkout and staff-role authorization.
- Current full suite: PASS (11 tests), including storefront and visual-editor HTML reachability.
- Current full suite: PASS (12 tests), including customer persistence, order search, and fulfillment status transitions.
- Current full suite: PASS (13 tests), including tenant-scoped product variants and SKU uniqueness.
- Current full suite: PASS (15 tests), including tenant-scoped collections and backup/restore verification.
- Current full suite: PASS (16 tests), including bounded rate-limiter behavior.
- Current full suite: PASS (16 tests), including explicit page rollback API and editor control reachability.
- Current full suite: PASS (17 tests), including tenant analytics and owner-only admin health authorization.
- Current full suite: PASS (17 tests), including owner-only usage reporting and tenant quota plumbing.
- Current full suite: PASS (18 tests), including API-key revocation and HMAC-signed webhook delivery.
- Current full suite: PASS (19 tests), including public search and sitemap generation.
- Current full suite: PASS (20 tests), including published-page SEO rendering.
- Current full suite: PASS (20 tests), including malicious SEO/heading escaping in published HTML.
- Current full suite: PASS (21 tests), including multilingual page locale override and fallback.
- Current full suite: PASS (22 tests), including tenant-scoped CSV product import/export.
- Current full suite: PASS (23 tests), including sandbox subscription transitions and quota updates.
- Current full suite: PASS (24 tests), including payment-provider idempotency/refund contract behavior.
- Current full suite: PASS (25 tests), including platform-admin provisioning/listing/suspension authorization.
- `python3 -m compileall -q forgecommerce scripts`: PASS.
- `bash -n scripts/*.sh`: PASS.
- `systemd-analyze verify systemd/*.service systemd/*.timer`: PASS.
- Controlled recovery with `restart_count=3`: PASS; exited non-zero and persisted `recovery_required` without restarting indefinitely.
- Secret-pattern scan for common AWS/GitHub/private-key markers: PASS.
- GitHub authentication: BLOCKED; `gh auth status` reports the stored token is invalid.
- Git checkpoint push: BLOCKED until GitHub authentication is repaired.
- Local checkpoint commit: PASS, `4a7f434` on `autonomous/development`.
