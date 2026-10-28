---
name: study
description: >-
  Run an appledore study session that builds the user's Obsidian vault, the Mind Palace, while they
  learn a topic: plan the topic together as a learning graph of subtopics, teach it one bite-sized
  subtopic at a time, file every answer to their questions into the vault, expand any node on
  request, and wrap up by reviewing the MOC chains and committing the vault. Use when the user says
  "let's study X", "study X", "continue studying X", "resume X", or runs /appledore:study, and for
  the rest of that session whenever they say "next", ask about what they're reading, say "deep dive
  X", or say they're done.
---

# Study

You run a study session in the user's Obsidian vault. The user learns a topic one subtopic at a
time, asks questions as they read, and every answer lands in the vault as linked notes. You keep
the vault's structure sound while it grows. This skill is the loop: each step has its own skill,
and the rules below apply to all of them.

## Set up

Do this once per session, before anything else.

1. **The script.** In every appledore skill, `palace` means
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/palace.py"`. If the path in that line still reads
   `${CLAUDE_PLUGIN_ROOT}`, your host didn't fill it in: use `scripts/palace.py` at the root of the
   appledore repo, two folders above this file. `palace --help` lists the commands. It is the
   vault's only index: every call reads the notes themselves, so its answers always match the
   vault, including the user's own edits.
2. **The vault** is `~/work-space/Solenya/Mind palace`, or the folder in `PALACE_VAULT` if that is
   set. `palace` reads the same folder.
3. **Read the vault's `README.md`.** It holds every convention a note follows: the folders, the
   properties, MOCs, names, links and sources. Follow it exactly. These skills don't repeat it,
   because two copies of a rule drift apart.
4. **Read `writing-rules.md`** next to this file before you write any text into a note.

## Start

- **A topic was named:** run `palace find "<topic>" --kind topic`.
  - **It exists:** read the topic note. Its Scope says the user's goal and starting point, and its
    Sources are the agreed sources. Run `palace next "<topic>"`, tell the user in one line where it
    stands (how many subtopics are written and how many are planned), then use `learn`.
  - **It doesn't:** use `plan`.
- **No topic was named:** `palace find "" --kind topic` lists the topics. Ask the user which one to
  continue, or what to start.

## The loop

| The user | Use |
|---|---|
| says "next", or names a node of the learning graph | `learn` |
| says "cold read it" about a subtopic | `learn`, step 5 |
| asks a question | `file` |
| says "deep dive X" | `deep-dive` |
| says "wrap up" or "done for today", or wants to stop | `wrap-up` |

**To use a step,** load the appledore skill of that name. If your host can't load a skill by name,
read `../<name>/SKILL.md` next to this skill's folder and follow it. When a step finishes, wait for
the user's next message and route it again. Anything that fits no row, answer it and stay in the
loop.

## Rules for every step

1. **What needs the user's yes.** You may add links between notes, and set a note's `mocs`, which
   lists it in its MOC, without asking. Everything else that changes the vault waits for the
   user's yes: filing an answer, taking over an existing note, renaming, merging, and creating,
   splitting or moving a MOC. Put several changes in one numbered list, so the user can answer
   them in one message ("1 yes, 2 no, 3 call it X").
2. **Reuse before writing.** Before you create any note, run `palace find` on its name, its
   synonyms and its key words. If a note already covers the concept, link to it instead, because
   two notes on one idea split everything written about it.
3. **New concepts.** Link a concept that has a note at its first mention in each note you write,
   even when another note already links it. `palace check` warns when a note names another note
   by its title or an alias but never links it: link each mention it reports in a note you wrote,
   unless the words mean something else there. When a concept has no note and no place in the
   learning graph, collect it, and at the end of the step ask the user once about all of them: add
   it to the graph as a stub, write it now, or leave it as plain text.
4. **Only the agreed sources.** Every claim in a note, and in an answer, comes from the topic's
   agreed sources (the topic note's Sources). Read them where they cover what you're writing, and
   state only what they say. Never fill a gap from memory, because a claim from memory can be out
   of date or about another product, and the user can't tell which sentence it is. When the
   sources don't cover something you need:
   1. Tell the user plainly: "The agreed sources don't cover X."
   2. Find 1–3 pages that do, official documentation first, and propose them, or ask the user
      for one.
   3. On the user's yes, read the page and add it to the topic note's Sources, so it is agreed
      from then on. If the user would rather not, leave X out: name it under Left out on purpose,
      or say that the question stays open.

   Every note ends with `## Sources`, linking the pages it was built from. Never save a page into
   the vault, and never cite an AI chat.
5. **After every write,** run `palace graph "<topic>" --write` if the learning graph changed, then
   `palace check`, and fix every error before you go on. Never edit a Learning graph section by
   hand: `palace` draws it from the notes' own `builds_on` and `mocs`, so it can't drift.
6. **Renames and moves** go through `palace mv` only, because it rewrites every link to the note.
   A plain move breaks them. **To merge note B into note A:** fold B's text into A, add B's title
   to A's `aliases`, rewrite each link that `palace backlinks "B"` lists so it points at A (a body
   link becomes `[[A|B]]`), delete B, and run `palace check`.
7. **The user reads in Obsidian.** Never paste a note's text into the chat. Give its link:
   `obsidian://open?vault=<vault folder name>&file=<path inside the vault, without .md>`, with
   both values URL-encoded (`Mind%20palace`, `_Main%20Notes%2FBlob%20tiers`).
8. **Git.** Commit and push the vault only in `wrap-up`. Never touch git history.
