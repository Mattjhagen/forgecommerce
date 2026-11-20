#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "$0")/agent-common.sh"
run_id="$1"; task="$2"; init_state; json_set status running
set +e
session="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("codex_session_id", ""))' "$STATE_FILE")"
output_file="$LOG_DIR/$run_id.codex.jsonl"
if [[ -n "$session" ]]; then
  codex exec resume "$session" -C "$ROOT_DIR" -s workspace-write --ask-for-approval never --no-alt-screen --json "Continue the active ForgeCommerce task. $task" >"$output_file" 2>&1
else
  codex exec -C "$ROOT_DIR" -s workspace-write --ask-for-approval never --no-alt-screen --json "Work autonomously on ForgeCommerce. $task. Read MASTER_PLAN.md and progress/CURRENT_STATE.json first. Run tests and persist a checkpoint. Do not use credentials or publish unverified changes." >"$output_file" 2>&1
fi
code=$?
cat "$output_file"
if [[ "$code" == 0 ]]; then
  new_session="$(python3 - "$output_file" <<'PY'
import json, sys
for line in open(sys.argv[1], encoding="utf-8", errors="replace"):
    try:
        event=json.loads(line)
    except json.JSONDecodeError:
        continue
    value=event.get("thread_id") or event.get("session_id")
    if value:
        print(value)
        break
PY
  )"
  if [[ -n "$new_session" ]]; then json_set codex_session_id "$new_session"; fi
fi
set -e
json_set last_exit_code "$code"; json_set finished_at "$(now_utc)"
if [[ "$code" == 0 ]]; then json_set status completed; else json_set status failed; fi
exit "$code"
