# Architecture Decisions

## 2026-11-19 — Standard-library local staging foundation

Use Python 3.12 standard-library components for the first verified slice. This keeps the staging environment reproducible on the target host and avoids making network access or a package registry a prerequisite. The domain layer remains adapter-oriented so PostgreSQL, Redis, and a production web framework can be introduced deliberately.

## 2026-11-19 — SQLite for local persistence

Use SQLite with foreign keys and WAL for local staging and tests. Production PostgreSQL remains an explicit deployment dependency and is not claimed as complete until its adapter and migration path are verified.
