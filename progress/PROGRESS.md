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
