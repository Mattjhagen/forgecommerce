#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "$0")/agent-common.sh"
init_state
day="$(TZ=America/Chicago date +%F)"; report="$ROOT_DIR/progress/DAILY/$day.md"; mkdir -p "$(dirname "$report")"
python3 - "$report" "$STATE_FILE" "$ROOT_DIR/progress/TEST_RESULTS.md" <<'PY'
from pathlib import Path
import json, sys
report,state_file,tests=sys.argv[1:]; state=json.loads(Path(state_file).read_text()); test_text=Path(tests).read_text() if Path(tests).exists() else 'No test results recorded.'
Path(report).write_text(f'''# Daily Report — {report.rsplit('/',1)[-1][:-3]}\n\n## Executive summary\n\nAutonomous runner checkpoint report.\n\n## Runner state\n\n```json\n{json.dumps(state, indent=2, sort_keys=True)}\n```\n\n## Tests\n\n{test_text}\n\n## GitHub synchronization\n\n{json.dumps(state.get("last_sync", {}), indent=2, sort_keys=True)}\n\n## Next action\n\nResume the active task from `progress/CURRENT_STATE.json`; external authentication or budget failures remain blockers and are not bypassed.\n''')
PY
echo "wrote $report"
