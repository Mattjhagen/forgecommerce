#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "$0")/agent-common.sh"
init_state; require_lock; cd "$ROOT_DIR"
[[ "$(safe_branch)" == "autonomous/development" ]] || { echo "not on autonomous/development; refusing sync" >&2; exit 2; }
if ! git diff --quiet || [[ -n "$(git ls-files --others --exclude-standard)" ]]; then echo "uncommitted changes present; safe handoff required"; exit 0; fi
git update-index -q --refresh
if git show-ref --verify --quiet refs/remotes/origin/autonomous/development; then
  [[ -n "$(git log origin/autonomous/development..HEAD --oneline)" ]] || { echo "no unpushed commits"; exit 0; }
fi
for delay in 1 2 4; do
  if git push origin autonomous/development; then
    sha="$(git rev-parse HEAD)"
    python3 - "$STATE_FILE" "$sha" <<'PY'
import json,sys
from datetime import datetime,timezone
p,sha=sys.argv[1:]; d=json.load(open(p)); d['last_sync']={'status':'confirmed','branch':'autonomous/development','commit':sha,'timestamp':datetime.now(timezone.utc).isoformat()}; open(p,'w').write(json.dumps(d,indent=2,sort_keys=True)+'\n')
PY
    exit 0
  fi
  sleep "$delay"
done
python3 - "$STATE_FILE" <<'PY'
import json,sys
from datetime import datetime,timezone
p=sys.argv[1]; d=json.load(open(p)); d['last_sync']={'status':'failed','reason':'remote unavailable or authentication failed','timestamp':datetime.now(timezone.utc).isoformat()}; open(p,'w').write(json.dumps(d,indent=2,sort_keys=True)+'\n')
PY
exit 1
