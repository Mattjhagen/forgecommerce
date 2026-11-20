#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="$ROOT_DIR/progress/runtime"
STATE_FILE="$STATE_DIR/agent-state.json"
LOG_DIR="$STATE_DIR/logs"
LOCK_FILE="$STATE_DIR/agent.lock"
SESSION_NAME="forgecommerce-agent"
mkdir -p "$STATE_DIR" "$LOG_DIR"
now_utc() { date -u +%Y-%m-%dT%H:%M:%SZ; }
json_set() {
  local key="$1" value="$2"
  python3 - "$STATE_FILE" "$key" "$value" <<'PY'
import json, pathlib, sys
p, key, value = sys.argv[1:]
pathlib.Path(p).parent.mkdir(parents=True, exist_ok=True)
try: data=json.loads(pathlib.Path(p).read_text())
except (FileNotFoundError, json.JSONDecodeError): data={}
data[key]=value
tmp=pathlib.Path(p).with_suffix('.tmp'); tmp.write_text(json.dumps(data, indent=2, sort_keys=True)+'\n'); tmp.replace(p)
PY
}
init_state() {
  [[ -f "$STATE_FILE" ]] || cat > "$STATE_FILE" <<'JSON'
{
  "status": "idle",
  "active_task": "",
  "last_successful_checkpoint": "",
  "codex_session_id": "",
  "run_id": "",
  "started_at": "",
  "finished_at": "",
  "last_exit_code": null,
  "last_test_result": "",
  "last_sync": {},
  "restart_count": 0
}
JSON
}
require_lock() { exec 9>"$LOCK_FILE"; flock -n 9 || { echo "agent lock is held" >&2; exit 75; }; }
safe_branch() { git -C "$ROOT_DIR" symbolic-ref --short HEAD; }
