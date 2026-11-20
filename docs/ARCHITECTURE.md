# Architecture

ForgeCommerce starts as a modular monolith: a standard-library Python HTTP API, SQLite persistence with foreign keys and WAL mode, and a small server-rendered storefront/admin shell. Modules are separated into configuration, database, security, services, and HTTP routing so the storage and payment adapters can later be replaced without changing domain behavior.

The API uses bearer sessions backed by SQLite. Every merchant-owned query receives a tenant identifier from the authenticated session; the database schema carries tenant keys and service methods reject mismatches. Passwords use PBKDF2-HMAC-SHA256. Checkout is sandbox-only and records an idempotency key.
