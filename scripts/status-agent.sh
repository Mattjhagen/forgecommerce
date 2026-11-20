#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "$0")/agent-common.sh"
init_state; cat "$STATE_FILE"
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then echo 'tmux_session: running'; else echo 'tmux_session: stopped'; fi
