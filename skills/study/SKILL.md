---
name: study
description: >-
  Run an appledore study session that builds the user's Obsidian vault, the Mind Palace, while they
  learn a topic: plan the topic together as a learning graph of subtopics, teach it one bite-sized
  subtopic at a time, file answers to their questions about it into the vault, expand any node on
  request, and wrap up by reviewing the MOC chains and committing the vault. Use when the user says
  "let's study X", "study X", "continue studying X", "resume X", or runs /appledore:study, and for
  the rest of that session whenever they say "next", ask about what they're reading, say "deep dive
  X", or say they're done.
---

# Study

You run a study session in the user's Obsidian vault. The user learns a topic one subtopic at a
time, asks questions as they read, and on their yes each answer about the subject lands in the
vault as linked notes. You keep the vault's structure sound while it grows. This file is the loop
and the rules every step follows. Each step has its own file in `steps/`, which you read when the
step starts (The loop, below), and `appledore` is the vault's script (Set up, below).

## Study rules

Every step follows these. The other files cite them as "study rule N".

1. **What needs the user's yes.** You may add links between notes, and set a note's `mocs`, which
   lists it in its MOC, without asking. Everything else that changes the vault waits for the
   user's yes: filing an answer, taking over an existing note, renaming, merging, and creating,
   splitting or moving a MOC. Put several changes in one numbered list, so the user can answer
   them in one message ("1 yes, 2 no, 3 call it X"), except an offer to file an answer, which is
   one line (`file` step 3).
2. **Reuse before writing.** Before you create any note, run `appledore find` on its name, its
   synonyms and its key words. If a note already covers the concept, link to it instead, because
   two notes on one idea split everything written about it.
3. **New concepts.** Link each concept that has a note as `writing-rules.md` rule 4 says. When
   `appledore check` warns that a note you wrote mentions another note but never links it, link
   that mention, unless the words mean something else there. When a concept has no note and no
   place in the learning graph, collect it, and at the end of the step ask the user once about all
   of them: add it to the graph as a stub, write it now, or leave it as plain text.
4. **Only the agreed sources.** Every claim in a note, and in an answer, comes from the topic's
   agreed sources (the topic note's Sources). Read them where they cover what you're writing, and
   state only what they say. Never fill a gap from memory, because a claim from memory can be out
   of date or about another product, and the user can't tell which sentence it is. When the
   sources don't cover something you need:
   1. Tell the user plainly: "The agreed sources don't cover X."
   2. Find 1–3 pages that do, official sources first, and propose them, or ask the user
      for one.
   3. On the user's yes, read the page and add it to the topic note's Sources, so it is agreed
      from then on. If the user would rather not, leave X out: name it under Left out on purpose,
      or say that the question stays open.

   Every note ends with `## Sources`, linking the pages it was built from. Never save a page into
   the vault, and never cite an AI chat. **When a helper agent, or a fetch tool that answers a
   prompt about a page, reads a source for you,** ask it to quote
   word for word, with the URL each quote came from, and to write "not on this page" instead of
   answering from memory, because a paraphrase can hide what came from memory.
5. **After every write,** run `appledore graph "<topic>" --write` if the learning graph changed,
   then `appledore check`, and fix every error before you go on. Never edit a Learning graph
   section by hand: `appledore` draws it from the notes' own `builds_on` and `mocs`, so it can't
   drift.
6. **Renames and moves** go through `appledore mv` only, because it rewrites every link to the
   note. A plain move breaks them. **To merge note B into note A:** fold B's text into A, add B's
   title to A's `aliases`, rewrite each link that `appledore backlinks "B"` lists so it points at A
   (a body link becomes `[[A|B]]`), delete B, and run `appledore check`.
7. **The user reads in Obsidian.** Never paste a note's text into the chat. After a step writes a
   note for the user to read, open it with `appledore open "<note>"`, and still give the
   `obsidian://` link it prints, because a host with no desktop can't open it. When a step writes
   several notes, open only the one to read first: `APPLEDORE_OPEN=0 appledore open "<note>"`
   prints another note's link without opening it.
8. **Git.** Commit and push the vault only in `wrap-up`. Never touch git history.

## Set up

Do this once per session, before anything else.

1. **The script.** `appledore` means `python3 "${CLAUDE_SKILL_DIR}/scripts/appledore.py"`. If the
   path in that line still reads `${CLAUDE_SKILL_DIR}`, your host didn't fill it in: the script is
   `scripts/appledore.py` in this skill's folder. Write the command out in full in each shell
   call, or define a shell function to run it several times in one (Gotchas, below).
   `appledore --help` lists the commands. It is the vault's only index: every call reads the
   notes themselves, so its answers always match the vault, including the user's own edits.
2. **The vault** is `~/work-space/Solenya/Mind palace`, or the folder in `APPLEDORE_VAULT` if that
   is set. `appledore` reads the same folder.
3. **Read the vault's `README.md`.** It holds every convention a note follows: the folders, the
   properties, MOCs, names, links and sources. Follow it exactly. These files don't repeat it,
   because two copies of a rule drift apart.

## Start

- **A topic was named:** run `appledore find "<topic>" --kind topic`.
  - **It exists:** read the topic note. Its Scope says the user's goal and starting point, and its
    Sources are the agreed sources. Run `appledore next "<topic>"`, tell the user in one line where
    it stands (how many subtopics are written and how many are planned), then route the rest of
    the message by The loop (`learn` when it only asks to go on). The line goes first, because
    `file` step 3 keeps its offer last.
  - **It doesn't:** use `plan`.
- **No topic was named:** `appledore find "" --kind topic` lists the topics. Ask the user which one
  to continue, or what to start.

## The loop

| The user | Use | Its file |
|---|---|---|
| names a topic that has no topic note yet | `plan` | `steps/plan.md` |
| says "next", or names a node of the learning graph | `learn` | `steps/learn.md` |
| says "cold read it" about a subtopic | `learn`, step 5 | `steps/learn.md`, which gives `cold-read.md` to a helper |
| asks a question about the topic's subject | `file` | `steps/file.md` |
| asks about the session, the plan, the vault, appledore or your own actions | answer it directly, and file nothing | |
| says "just answer" or "don't file" | `file`, step 3 | `steps/file.md` |
| says "deep dive X", "go deeper on X" or "expand X" | `plan`, Deep dive | `steps/plan.md` |
| says "wrap up" or "done for today", or wants to stop | `wrap-up` | `steps/wrap-up.md` |

**To use a step,** read its file in this skill's folder and follow it. **Before you write any text
into a note,** in any step, read `writing-rules.md` there too. Skip a read only when the file's
full text is already in your context, and read it again if your context has been summarized since,
because a summary can drop the text of files you read.

When a step finishes, wait for the user's next message and route it again. Anything that fits no
row, answer it and stay in the loop.

## Gotchas

- **A variable holding the command fails in zsh** ("no such file or directory"), because zsh
  doesn't split it into words. Define a function: `appledore() { python3 "<path>" "$@"; }`.
- **A rename that changes only letter case** is invisible to a disk that ignores case, as a
  Mac's does, and to the vault's git. Use `appledore mv`, which handles the disk; the commit in
  `wrap-up` handles git.
- **The Obsidian command line interface answers even when it is turned off** in Obsidian's
  settings, so its answer doesn't say whether a note opened. Open notes only with
  `appledore open`, which checks, and falls back to the `obsidian://` link.
- **A paywalled page looks whole:** a saved or fetched copy can stop after its first section.
  Check that it reaches the last section its contents list, which needs no full read. Read a page
  marked "(needs your login)" in the user's browser if your host can, or ask the user to paste
  the part you need.
- **Agreed sources can disagree:** `writing-rules.md` rule 1 says which to follow and how to
  name the disagreement.
