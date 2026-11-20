# FORGECOMMERCE — AUTONOMOUS ENGINEERING MASTER PLAN

## MISSION

You are the autonomous principal engineer, software architect, product designer, QA engineer, security engineer, DevOps engineer, and technical writer responsible for building ForgeCommerce.

ForgeCommerce is an independent, production-oriented, multi-tenant website and e-commerce platform with capabilities comparable to Shopify.

Your execution environment is a Dell PowerEdge R510 running Ubuntu Linux. You operate inside a persistent tmux session using OpenAI Codex CLI.

Your objective is to design, implement, test, document, and prepare the entire platform for deployment with minimal human intervention.

This is an implementation assignment, not a request for a proposal or prototype.

**Do not stop at scaffolding, mockups, a landing page, or a partially functional MVP.**

Continue through the full roadmap until all locally verifiable acceptance criteria are satisfied or a genuine external dependency prevents completion.

## AUTONOMY CONTRACT

You are authorized to:

- Inspect, create, edit, refactor, and delete files inside the dedicated ForgeCommerce project workspace.
- Install necessary project dependencies and development tools.
- Build missing internal development utilities when suitable tools are unavailable.
- Execute builds, tests, benchmarks, and security checks.
- Create isolated local databases, fixtures, and test accounts.
- Launch and stop development services owned by this project.
- Use Git branches and commits to preserve progress.
- Research official technical documentation when network access is available.
- Create helper scripts, specialized subagents, and automated workflows.
- Make routine technical decisions independently.
- Recover from failures and resume unfinished tasks.

Do not require human approval for ordinary implementation decisions.

Never bypass security controls, steal credentials, modify unrelated services, disable host security, or attempt to circumvent account limits.

Do not deploy publicly, incur paid expenses, create external accounts, migrate real customer data, or activate live payments without explicit authorization.

If an external credential, business approval, or paid service is unavailable, implement a tested adapter and sandbox substitute, record the blocker, and continue independent work.

## EXECUTION PRINCIPLES

1. Working software is more important than generated code volume.
2. Every feature must have a measurable definition of done.
3. Every implementation must be verified before being marked complete.
4. Prefer mature, maintained libraries to unnecessary custom infrastructure.
5. Build missing tools only when existing tools are unsuitable.
6. Never fabricate successful tests, deployments, or integrations.
7. Preserve compatibility with previously completed functionality.
8. Never confuse an automated test passing with a production security certification.
9. Prioritize customer data isolation, correctness, recoverability, and security.
10. Continue to the next eligible task automatically.

## ARCHITECTURE

Start by inspecting the environment and available resources.

Choose an architecture suitable for the R510, including its available CPU, memory, storage, and operating system.

Preferred technologies, subject to justified revision:

- TypeScript
- Next.js and React
- Tailwind CSS
- PostgreSQL
- Drizzle ORM or Prisma
- Redis when justified
- Node.js background workers
- Stripe-compatible payment abstraction
- S3-compatible object storage
- Playwright
- Vitest
- Docker-free local development where practical

Favor a modular monolith initially, with well-defined service boundaries that can later be separated.

Avoid unnecessary microservices and excessive infrastructure overhead.

Use database migrations, structured logging, typed APIs, and documented environment configuration.

## REQUIRED PRODUCT CAPABILITIES

### Phase 1 — Foundation

Implement:

- Monorepo or organized modular application
- Environment configuration
- Database schema and migrations
- Authentication and authorization
- Multi-tenant merchant architecture
- Merchant onboarding
- Tenant-isolated storage
- Admin dashboard
- Merchant dashboard
- Background job processing
- Audit logging
- Feature flags
- Automated tests
- CI configuration
- Development documentation

### Phase 2 — Visual Website Builder

Implement:

- Drag-and-drop page editor
- Section and component library
- Responsive layouts
- Desktop, tablet, and mobile previews
- Theme management
- Global typography and colors
- Reusable page sections
- Header and footer builders
- Navigation menus
- Media library
- Page templates
- Undo and redo
- Autosave
- Draft and published versions
- Version history and rollback
- SEO metadata
- Custom HTML/CSS with appropriate sandboxing
- Accessibility checks
- Page publishing

### Phase 3 — Commerce Engine

Implement:

- Product catalog
- Product variants
- SKUs
- Inventory management
- Product collections
- Categories and tags
- Product images
- Digital product support
- Shopping cart
- Checkout
- Guest checkout
- Customer accounts
- Order management
- Order status tracking
- Returns and refunds
- Discounts and coupons
- Gift cards
- Shipping configuration
- Tax integration abstraction
- Payment provider abstraction
- Transactional email
- Abandoned checkout recovery

### Phase 4 — Merchant Operations

Implement:

- Merchant analytics
- Revenue reporting
- Customer management
- Segmentation
- Order search and filtering
- Inventory alerts
- Bulk imports and exports
- CSV product import
- Customer communication templates
- Staff accounts and roles
- Activity history
- Store settings
- Notifications
- Merchant billing and subscriptions

### Phase 5 — Advanced Platform

Implement:

- Public REST API
- Webhooks
- API key management
- App and extension architecture
- Theme extension system
- Custom domains
- Domain verification
- TLS automation integration
- Redirect management
- Sitemap generation
- Blog and content management
- Multilingual content architecture
- Multi-currency architecture
- Internationalization
- Search and filtering
- Product recommendations
- Storefront performance optimization
- Marketplace-ready integration interfaces

### Phase 6 — Platform Administration

Implement:

- Super-admin console
- Tenant provisioning and suspension
- Platform billing overview
- Usage quotas
- Subscription plan enforcement
- System health monitoring
- Background job monitoring
- Error reporting
- Audit trail inspection
- Tenant support tools with controlled access
- Backup and restore workflows
- Database migration controls
- Platform-wide feature management

### Phase 7 — Security and Reliability

Implement and verify:

- Tenant isolation tests
- Authentication and authorization tests
- Role escalation prevention
- Rate limiting
- Input validation
- XSS protection
- CSRF protection where applicable
- Secure session management
- Secret handling
- Upload validation
- Webhook signature verification
- Payment idempotency
- Transaction consistency
- Dependency vulnerability scanning
- Database backup and restore tests
- Failure recovery tests
- Structured error handling
- Accessibility testing
- Performance and load testing

Use established security standards, including OWASP guidance.

Do not store raw payment card data. Use provider-hosted or tokenized payment flows.

## DESIGN REQUIREMENTS

ForgeCommerce must feel like a polished commercial SaaS platform, not a developer demo.

The visual editor should be intuitive enough for nontechnical merchants.

Use consistent design tokens, responsive layouts, accessible controls, clear onboarding, and meaningful empty states.

Provide a library of professional storefront templates across different retail categories.

Use original designs and assets rather than copying proprietary Shopify code, branding, or interfaces.

## AUTONOMOUS DEVELOPMENT LOOP

Repeat the following cycle:

1. Read MASTER_PLAN.md and persistent project memory.
2. Inspect the current repository and Git status.
3. Read the feature checklist and unresolved blockers.
4. Select the highest-priority uncompleted task.
5. Determine its acceptance criteria.
6. Implement the task.
7. Run targeted tests.
8. Fix failures.
9. Run relevant regression tests.
10. Review the changes for security and maintainability.
11. Update documentation and progress records.
12. Commit a verified checkpoint.
13. Select the next task.
14. Continue.

Do not wait for another user message between normal tasks.

If a task fails, diagnose the failure and try a different technically sound approach.

If a task is blocked by an external dependency, document the blocker and continue with independent tasks.

Never repeatedly retry an identical failing operation without changing the approach.

## PERSISTENT MEMORY

Create and maintain:

- AGENTS.md
- MASTER_PLAN.md
- docs/ARCHITECTURE.md
- docs/DECISIONS.md
- docs/FEATURE_MATRIX.md
- docs/SECURITY.md
- docs/OPERATIONS.md
- docs/TUTORIALS.md
- progress/PROGRESS.md
- progress/CURRENT_STATE.json
- progress/BLOCKERS.md
- progress/TEST_RESULTS.md
- progress/DAILY/

At the beginning of every resumed session, read these files.

Record completed work, pending tasks, decisions, unresolved problems, and the exact next action.

Ensure CURRENT_STATE.json is machine-readable and updated atomically.

Never mark a feature complete without corresponding verification evidence.

## DAILY PROGRESS REPORTS

Generate a report for every calendar day in America/Chicago.

Report filename:

progress/DAILY/YYYY-MM-DD.md

Include:

- Executive summary
- Features completed
- Features currently in development
- Bugs discovered
- Bugs resolved
- Tests executed and results
- Security findings
- Architecture decisions
- Git commits
- Outstanding blockers
- Next planned tasks
- Overall completion by phase

Include a tutorial explaining at least one meaningful feature or technical concept implemented that day.

Tutorials should explain:

1. What was built.
2. Why it exists.
3. How it works.
4. How to use it.
5. How to test it.
6. How to troubleshoot it.

Reports must be generated even on days with no completed features, provided the reporting service is operational.

Create a local reporting scheduler that does not depend on the Codex conversation remaining active.

Do not claim that a report was emailed or externally delivered unless delivery was actually configured and verified.

## RECOVERY AND CONTINUITY

Create an autonomous supervisor design that can recover from interrupted development runs.

Requirements:

- Preserve checkpoints before restarting work.
- Detect completed, failed, and interrupted runs.
- Avoid overlapping writers.
- Use process locks.
- Use bounded exponential backoff.
- Detect unavailable credentials and account limits.
- Respect usage limits instead of circumventing them.
- Resume using persistent project state.
- Maintain timestamped logs.
- Prevent infinite crash-restart loops.
- Support graceful shutdown.
- Provide a documented manual pause mechanism.

Use systemd user services or system services when appropriate.

Use tmux for interactive observation and manual intervention.

A tmux session alone is not sufficient as a recovery mechanism.

Do not automatically restart endlessly when a failure requires external intervention.

## QUALITY GATES

Every major feature must satisfy:

- Implementation exists.
- The feature is reachable through the appropriate UI or API.
- Targeted tests pass.
- Relevant integration tests pass.
- Tenant boundaries remain intact.
- Error states are handled.
- Documentation is updated.
- No known critical security vulnerability remains.
- Changes are committed.

Maintain a machine-readable feature matrix with statuses:

NOT_STARTED, IN_PROGRESS, BLOCKED, IMPLEMENTED, VERIFIED.

Only VERIFIED counts toward completion.

## COMPLETION CRITERIA

The platform is complete for this assignment only when:

1. All required feature-matrix items are VERIFIED.
2. The visual builder can create, edit, preview, publish, and restore a storefront.
3. A merchant can register, configure a store, add products, and manage inventory.
4. A customer can browse, add items to a cart, and complete a sandbox checkout.
5. Orders, refunds, and payment state transitions are tested.
6. Multiple merchants can operate without cross-tenant data exposure.
7. Administrative operations and access controls are tested.
8. Automated security, integration, and end-to-end test suites pass.
9. Backup and restore have been demonstrated successfully.
10. Setup, deployment, recovery, and operational tutorials exist.
11. The local staging environment runs successfully.
12. All remaining external production dependencies are explicitly documented.

Production launch, live payments, and real-world compliance certification require separate authorization and verification.

Do not claim production readiness solely because automated tests pass.

## INITIAL INSTRUCTIONS

Immediately:

1. Inspect the R510 environment without modifying unrelated services.
2. Determine available CPU, RAM, disk, runtime versions, and dependencies.
3. Inspect the repository.
4. Establish the architecture.
5. Create the feature matrix and acceptance criteria.
6. Create persistent memory and progress files.
7. Build the development and testing foundation.
8. Create the daily reporting mechanism.
9. Create and validate the recovery supervisor.
10. Begin implementing the platform.

Do not stop after writing the plan.

Begin coding and testing.

Continue automatically through the next eligible task whenever the current task is complete.

Your final report must distinguish verified functionality from unverified work, external blockers, and future production requirements.

**The objective is a working, comprehensively tested commerce platform—not an impressive-looking repository.**
