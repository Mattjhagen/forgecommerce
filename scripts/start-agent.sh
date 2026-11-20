#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "$0")/agent-common.sh"
init_state; require_lock
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then echo "agent already running in tmux:$SESSION_NAME"; exit 0; fi
if [[ "$(safe_branch)" != "autonomous/development" ]]; then echo "refusing to run on $(safe_branch); checkout autonomous/development first" >&2; exit 2; fi
run_id="$(date -u +%Y%m%dT%H%M%SZ)-$$"
task="${1:-Resume ForgeCommerce from progress/CURRENT_STATE.json; implement the next verified task, run tests, update persistent progress, and stop on authentication or budget limits.}"
json_set status starting; json_set active_task "$task"; json_set run_id "$run_id"; json_set started_at "$(now_utc)"; json_set last_exit_code ""
log="$LOG_DIR/$run_id.log"
tmux new-session -d -s "$SESSION_NAME" "cd '$ROOT_DIR' && scripts/run-agent.sh '$run_id' '$task' >> '$log' 2>&1"
echo "started tmux:$SESSION_NAME run:$run_id log:$log"
