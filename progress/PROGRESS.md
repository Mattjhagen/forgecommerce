# Progress

## 2026-11-19

Started from an empty repository. Established the architecture, persistent project memory, local staging approach, and acceptance matrix. Implemented the first commerce foundation checkpoint: configuration, SQLite schema, tenant registration, sessions, product catalog, inventory, carts, sandbox checkout, audit events, health endpoint, backup utility, and a recovery supervisor design.

Next: run the targeted and full test suites, repair failures, then extend the verified API with merchant roles, feature flags, page versions, and admin operations.

## 2026-11-19 — Foundation and commerce checkpoint

Added tenant-scoped inventory updates, order listing and sandbox refunds, page drafts/versioning/publishing, feature flags, audit-event listing, and API routes. Fixed SQLite worker-thread handling and verified the complete HTTP checkout path. Full suite: 8 tests passing.

Next: implement staff roles and customer/order operations, then build the storefront page editor UI and public storefront routes.

## 2026-11-19 — Public storefront checkpoint

Added public tenant storefront product browsing, guest carts and sandbox checkout, owner-managed staff roles, and role enforcement. The full HTTP/domain suite now passes 10 tests, including guest checkout and staff authorization.

Next: add customer records/order search and begin the visual editor shell with responsive preview and publish/rollback UI.

## 2026-11-19 — Editor/storefront UI checkpoint

Added a CSP-protected storefront HTML shell with responsive product grid and guest-cart interaction, plus a browser-reachable visual editor surface for creating and publishing versioned pages. The full suite now passes 11 tests.

Next: add customer records, order search/status operations, editor rollback and richer sections, then expand security and accessibility coverage.

## 2026-11-19 — Merchant operations checkpoint

Added tenant-scoped customer records updated transactionally at checkout, order search, fulfillment status transitions, and customer listing. The full suite passes 12 tests.

Next: add product variants/collections and editor rollback controls, then implement broader security validation and backup/restore tests.

## 2026-11-19 — Variant catalog checkpoint

Added tenant-scoped product variants with unique SKUs, prices, and inventory, including catalog retrieval and duplicate-SKU rejection. Full suite: 13 tests passing.

Next: add collections, editor rollback controls, and backup/restore verification.

## 2026-11-19 — Collections and recovery checkpoint

Added tenant-scoped product collections with public collection browsing and verified the SQLite backup/restore utility against tenant and catalog data. Full suite: 15 tests passing.

Next: add editor rollback controls, rate limiting, stricter input/security tests, and platform administration surfaces.

## 2026-11-19 — Security hardening checkpoint

Added process-local HTTP rate limiting and escaped merchant-controlled product names in the storefront renderer. The full suite passes 16 tests, including limiter behavior.

Next: add editor rollback controls, security regression tests for malicious content, and platform administration surfaces.

## 2026-11-19 — Editor rollback checkpoint

Added explicit page rollback semantics and a browser editor rollback control selecting a prior immutable version. Full suite remains green at 16 tests.

Next: add malicious-content regression coverage and platform administration/health surfaces.

## 2026-11-19 — Analytics and admin health checkpoint

Added tenant-scoped revenue/order/customer/inventory analytics and owner-only database health with table counts. Staff access is denied. Full suite: 17 tests passing.

Next: add malicious-content regression coverage, usage quotas, and platform-wide administration controls.

## 2026-11-20 — Tenant quotas checkpoint

Added starter-plan tenant limits, owner-only usage reporting, and product/page quota enforcement. Full suite remains green at 17 tests.

Next: add malicious-content regression coverage, platform-wide administration, webhooks, and public API key management.

## 2026-11-20 — API integration checkpoint

Added hashed API-key authentication with revocation, webhook registration, signed order-created delivery records, and delivery inspection. Full suite: 18 tests passing.

Next: add malicious-content regression coverage, public search/SEO metadata, and platform-wide administration controls.

## 2026-11-20 — Search and SEO checkpoint

Added public tenant-scoped product search and standards-compatible sitemap XML generation. Full suite: 19 tests passing.

Next: add page SEO rendering, malicious-content regression coverage, and platform-wide administration controls.
