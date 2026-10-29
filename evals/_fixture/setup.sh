#!/usr/bin/env bash
# Sets up one eval run: copies the fixture vault and its source pages into the run's empty
# workspace, and points appledore at that vault. `claude plugin eval --scaffold` runs it before
# each case, as the operator and outside the agent's sandbox, with the workspace as the current
# folder and a temporary HOME. It never touches the operator's real vault.
set -euo pipefail

fixture="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd "$fixture/../.." && pwd)"
workspace="$PWD"
vault="$workspace/vault"

cp -R "$fixture/vault" "$fixture/sources" "$workspace/"

# The topic's agreed sources are local pages beside the vault, never inside it, linked by
# absolute path so the agent can read them without network access.
python3 - "$vault" "file://$workspace/sources" <<'EOF'
import pathlib, sys
vault, sources = pathlib.Path(sys.argv[1]), sys.argv[2]
for note in vault.rglob("*.md"):
    text = note.read_text(encoding="utf-8")
    if "@@SOURCES@@" in text:
        note.write_text(text.replace("file://@@SOURCES@@", sources), encoding="utf-8")
EOF

# The runner passes the session no variables but EVAL_* ones, so the vault's path reaches the
# agent's shell through the temporary HOME's profile files instead. Opening notes is turned off,
# because a run must never open Obsidian on the operator's desktop.
cat > "$HOME/.appledore-eval-env" <<EOF
export APPLEDORE_VAULT="$vault"
export APPLEDORE_OPEN=0
EOF
for profile in .zshenv .zshrc .bashrc .bash_profile .profile; do
    echo '. "$HOME/.appledore-eval-env"' >> "$HOME/$profile"
done

# Draw the topic's learning graph with the script under test, so the fixture matches whatever
# drawing rules the script has now.
python3 "$repo/skills/study/scripts/appledore.py" --vault "$vault" graph "HTTP caching" --write > /dev/null
