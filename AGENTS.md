# appledore, for agents

appledore builds the user's Obsidian vault while they learn a topic. You plan the topic with them as a learning graph, teach it one bite-sized subtopic at a time, file the answers to their questions about it into the vault on their yes, and review and commit the vault at the end.

## Run a study session

When the user says "let's study X", "continue studying X" or anything like it:

1. Read `skills/study/SKILL.md` and follow it for the whole session. It is the loop, and it holds the rules every step follows.
2. When it says to use a step (`plan`, `learn`, `file`, `deep-dive`, `wrap-up`), read `skills/<step>/SKILL.md` and follow it.
3. `palace` in the skills means `python3 scripts/palace.py`, run from this repo's root. It needs only Python 3.8 or later.
4. The vault is `~/work-space/Solenya/Mind palace`, or the folder in `PALACE_VAULT`.
5. `palace open "<note>"` opens a note in the running Obsidian app, through Obsidian's command line interface when it is turned on (Settings → General → Advanced) and the note's `obsidian://` link otherwise, and prints the link. On a host with no desktop, or with `PALACE_OPEN=0`, it only prints the link, and nothing fails.

The cold read in `skills/learn/SKILL.md` step 5 needs a helper agent with no tools. Skip that step if you can't start one.

## The repo

| Path | What it is |
|---|---|
| `skills/` | The six skills, in the Agent Skills format: `study` is the loop, the other five are its steps. `study/writing-rules.md` is shared by every step that writes. |
| `scripts/palace.py` | The vault's index. Every command reads the notes themselves, so it never drifts. |
| `agents/` | Claude Code only: `study`, the main agent, which loads the `study` skill, and `cold-reader`, the helper with no tools. |
| `.claude-plugin/` | The Claude Code plugin manifest, and the marketplace (this repo is its own marketplace). |
| `tests/` | `python3 -m unittest discover -s tests` |
| `docs/` | `research.md`, the evidence behind the writing rules, and `vault-conventions.md`, the layout the vault follows. |

Keep the skills portable: frontmatter holds only `name` and `description`, and an instruction says "ask the user", never the name of a tool only one host has.
