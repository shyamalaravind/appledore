# appledore, for agents

appledore builds the user's Obsidian vault while they learn a topic. You plan the topic with them as a learning graph, teach it one bite-sized subtopic at a time, file the answers to their questions about it into the vault on their yes, and review and commit the vault at the end.

## Run a study session

When the user says "let's study X", "continue studying X" or anything like it, read `skills/study/SKILL.md` and follow it for the whole session. It holds the rules every step follows, and it says which file in `skills/study/steps/` to read for each request.

- `appledore` in the skill means `python3 skills/study/scripts/appledore.py`, run from this repo's root. It needs only Python 3.8 or later.
- The vault is `~/work-space/Solenya/Mind palace`, or the folder in `APPLEDORE_VAULT`.

## Work on the repo

The README's [repo table](README.md#the-repo) says what each folder holds. Run the tests with `python3 -m unittest discover -s tests`.

Keep the skill portable: its frontmatter holds only `name` and `description`, and an instruction says "ask the user", never the name of a tool only one host has, because other hosts reject other fields and lack that tool.
