#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "$0")/agent-common.sh"
init_state; require_lock
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then tmux send-keys -t "$SESSION_NAME" C-c; tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true; fi
json_set status stopped; json_set finished_at "$(now_utc)"
echo "stopped $SESSION_NAME"
