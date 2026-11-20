#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "$0")/agent-common.sh"
init_state; require_lock
status="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("status", ""))' "$STATE_FILE")"
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then echo "runner is live; no recovery needed"; exit 0; fi
if [[ "$status" == "running" || "$status" == "starting" ]]; then
  json_set status interrupted; json_set finished_at "$(now_utc)"; json_set restart_count "$(python3 -c 'import json,sys; print(int(json.load(open(sys.argv[1])).get("restart_count",0))+1)' "$STATE_FILE")"
  count="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("restart_count",0))' "$STATE_FILE")"
  if (( count <= 3 )); then exec "$ROOT_DIR/scripts/start-agent.sh" "Recover interrupted run from the persisted checkpoint; inspect logs before continuing."; fi
  json_set status recovery_required; echo "bounded recovery limit reached; manual intervention required" >&2; exit 1
fi
echo "no interrupted run detected"
