#!/usr/bin/env bash
# Runs the main test: the whole corpus and one question per request, through the Responses API.
# Usage: VAST_API_KEY=... ./run.sh CHOCK_CHECKOUT [QUESTION...]
#   QUESTION is a name such as q2-callers; with none, all five run one after the other.
# The answers go to runs/<UTC time>/. Then score them: python3 -I score.py runs/<UTC time>
# Our run sent two sequences at the same time (see the README); one at a time is the safer choice,
# because the demo endpoint returned HTTP 408 once while two long requests were open.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
chock=$1
shift
questions=("$@")
[ ${#questions[@]} -gt 0 ] || questions=(q1-docs q2-callers q3-keys q4-dead q5-bloat)
: "${VAST_API_KEY:?set VAST_API_KEY}"
out="$here/runs/$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$out"
echo "answers go to $out"
[ -f "$here/corpus/repo.txt" ] || python3 -I "$here/corpus/build.py" "$chock" "$here/corpus/repo.txt"
for q in "${questions[@]}"; do
  printf '%s %s ' "$(date -u +%H:%M:%S)" "$q"
  python3 -I "$here/ask.py" "$here/corpus/repo.txt" "$here/questions/$q.md" "$out/$q" 131072
done
