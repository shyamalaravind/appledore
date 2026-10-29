#!/usr/bin/env bash
# The shared fixture, with a second ready node: Vary header builds on the written HTTP cache
# instead of on Validation. Both are then ready, and Vary header is the recommended one,
# because it sits a level higher in the learning graph, though Validation comes first by name
# and in the graph's drawing order.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "$here/../_fixture/setup.sh"

python3 - "vault/Stubs/Vary header.md" <<'EOF'
import pathlib, sys
stub = pathlib.Path(sys.argv[1])
text = stub.read_text(encoding="utf-8")
moved = text.replace('builds_on:\n  - "[[Validation]]"', 'builds_on:\n  - "[[HTTP cache]]"')
if moved == text:
    sys.exit(f"{stub}: no builds_on [[Validation]] to change")
stub.write_text(moved, encoding="utf-8")
EOF

python3 "$here/../../skills/study/scripts/appledore.py" --vault vault graph "HTTP caching" --write > /dev/null
