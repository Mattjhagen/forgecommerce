#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "$0")/agent-common.sh"
run_id="$1"; task="$2"; init_state; json_set status running
set +e
session="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("codex_session_id", ""))' "$STATE_FILE")"
if [[ -n "$session" ]]; then
  codex exec resume "$session" -C "$ROOT_DIR" -s workspace-write --ask-for-approval never --no-alt-screen "Continue the active ForgeCommerce task. $task"
else
  codex exec -C "$ROOT_DIR" -s workspace-write --ask-for-approval never --no-alt-screen --json "Work autonomously on ForgeCommerce. $task. Read MASTER_PLAN.md and progress/CURRENT_STATE.json first. Run tests and persist a checkpoint. Do not use credentials or publish unverified changes."
fi
code=$?; set -e
json_set last_exit_code "$code"; json_set finished_at "$(now_utc)"
if [[ "$code" == 0 ]]; then json_set status completed; else json_set status failed; fi
exit "$code"
