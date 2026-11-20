# Blockers

Local implementation is not blocked. GitHub publishing is blocked by invalid GitHub CLI authentication; the sync system records this failure and retains local commits. Production services are intentionally represented by local adapters until separately authorized and configured.

The current execution sandbox also denies local TCP socket binds with `EPERM`, and denies access to the systemd bus. HTTP/load verification and timer activation must be rerun in a session with local binding and service-manager access; no application workaround is appropriate.

This session also exposes `.git` as read-only: `git commit` cannot create `.git/index.lock`. All verified source and progress changes remain in the working tree and require a writable Git metadata mount before checkpoint commit/push.
