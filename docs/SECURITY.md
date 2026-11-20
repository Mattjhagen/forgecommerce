# Security Notes

- Passwords are never stored directly; PBKDF2-HMAC-SHA256 with a per-user salt is used.
- Sessions are random opaque tokens stored hashed in the database and expire.
- Tenant-owned resources are scoped by the authenticated merchant's tenant id.
- JSON input is size-limited and validated. HTML is escaped in the shell response.
- Checkout requires an idempotency key and never accepts card data; the sandbox payment adapter records only a provider-neutral state.
- Local HTTP requests are bounded by a process-local rate limiter, and storefront product names are escaped before insertion into HTML.
- API keys are stored hashed and only returned once; webhook delivery records use HMAC-SHA256 signatures and remain queued in the local adapter.
- Published-page tests cover malicious SEO and section-heading content; escaping is verified in the HTTP response.
- Production requirements still include a TLS-terminating proxy, CSRF strategy for cookie sessions, dependency scanning, PostgreSQL row-level defense-in-depth, and a hosted/tokenized payment provider.
