#!/usr/bin/env bash
# ABOUTME: Weekly commit-health metrics: revert rate, fix-up rate, median time-to-next-touch
# ABOUTME: Run from a git repo to gauge whether the enforcement hooks are reducing drift

set -u

SINCE="${1:-7 days ago}"
PROJECT=$(basename "$(pwd)")

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: not inside a git repository"
  exit 1
fi

echo "Commit-health metrics for $PROJECT (since \"$SINCE\")"
echo "=================================================="

total=$(git log --since="$SINCE" --oneline | wc -l | tr -d ' ')
echo "Total commits: $total"
if [[ "$total" == "0" ]]; then
  echo "(no commits in range; skipping metrics)"
  exit 0
fi

# 1. Revert rate
reverts=$(git log --since="$SINCE" --grep='^[Rr]evert' --oneline | wc -l | tr -d ' ')
rev_pct=0
(( total > 0 )) && rev_pct=$(( reverts * 100 / total ))
echo ""
echo "[1] Revert rate: $reverts / $total ($rev_pct%)"

# 2. Fix-up rate
fixups=$(git log --since="$SINCE" --oneline | grep -cE '^[a-f0-9]+ (fix|hotfix)(\(|:)' || true)
fix_pct=0
(( total > 0 )) && fix_pct=$(( fixups * 100 / total ))
echo ""
echo "[2] Fix-up rate: $fixups / $total ($fix_pct%)"

# 3. Time-to-next-touch
echo ""
echo "[3] Time-to-next-touch (median seconds between consecutive commits on the same file)"
uv run --no-project python3 - "$SINCE" <<'PY'
import subprocess
import sys
import statistics
from collections import defaultdict

since = sys.argv[1]
out = subprocess.run(
    ["git", "log", f"--since={since}", "--name-only", "--pretty=format:%H|%ct"],
    capture_output=True, text=True
).stdout

commits_per_file = defaultdict(list)
current_hash, current_ts = None, None
for line in out.splitlines():
    if "|" in line and line.count("|") == 1 and line.split("|")[1].isdigit():
        current_hash, ts = line.split("|")
        current_ts = int(ts)
    elif line.strip() and current_ts is not None:
        commits_per_file[line.strip()].append((current_ts, current_hash))

gaps = []
for path, entries in commits_per_file.items():
    entries.sort()
    for i in range(1, len(entries)):
        gaps.append(entries[i][0] - entries[i - 1][0])

if not gaps:
    print("    (no file touched in more than one commit)")
else:
    median_s = statistics.median(gaps)
    p90_s = sorted(gaps)[int(len(gaps) * 0.9)] if len(gaps) > 1 else gaps[0]
    def fmt(s):
        if s < 3600: return f"{int(s) // 60}m"
        if s < 86400: return f"{int(s) // 3600}h"
        return f"{int(s) // 86400}d"
    print(f"    Samples: {len(gaps)} consecutive-touch pairs")
    print(f"    Median:  {fmt(median_s)}")
    print(f"    P90:     {fmt(p90_s)}")
    if median_s < 86400:
        print(f"    [!] Short median ({fmt(median_s)}) suggests rework / drift.")
PY

echo ""
echo "Thresholds (guide, not dogma):"
echo "  revert_rate + fix_up_rate > 15% = yellow flag; > 25% = red flag."
echo "  median time-to-next-touch < 24h = drift warning."
echo "  Re-run this baseline every 2 weeks to see if the enforcement hooks help."
