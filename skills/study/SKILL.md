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

1. **What needs the user's yes.** You may add links between notes, set a note's `mocs`, which
   lists it in its MOC, and set or clear a subtopic's `status` mark (`unopened`, `planned`) where a
   step says (`plan` step 4, `learn` steps 4, 6 and 7), without asking. Files you make outside the
   vault, such as a page saved in your scratch folder, need no yes either. Everything else that
   changes the vault waits for the user's yes: filing an answer, taking over an existing note,
   renaming, merging, and creating, splitting or moving a MOC. Put several changes in one numbered
   list, so the user can answer them in one message ("1 yes, 2 no, 3 call it X"), except an offer
   to file an answer, which is one line (`file` step 3).
2. **Reuse before writing.** `appledore new` refuses only a name that is already taken, so before
   you create a note, run `appledore find` on its synonyms and key words. If a note already covers
   the concept, link to it instead, because two notes on one idea split everything written about
   it.
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

   **Read each page from a saved copy.** The first time the session needs a page, read
   `sources.md` in this skill's folder and save the page as it says. From then on, read the part
   you need from the saved file, because a page read whole stays in your context for the rest of
   the session.

   Every note ends with `## Sources`, linking the pages it was built from. Never save a page into
   the vault, and never cite an AI chat. **When a helper agent, or a fetch tool that answers a
   prompt about a page, reads a source for you,** ask it to quote
   word for word, with the URL each quote came from, and to write "not on this page" instead of
   answering from memory, because a paraphrase can hide what came from memory.
5. **After every write,** run `appledore check`, and fix every error before you go on. Never edit
   a Learning graph section by hand: `appledore` draws it from the notes' own `builds_on` and
   `mocs`, so it can't drift. A write command redraws the graphs it touches; when `check` says
   one is out of date, `appledore graph '<topic>' --write` redraws it.
6. **`appledore` writes properties and moves files; you write text.** Never edit frontmatter by
   hand, because hand-written YAML is where quoting and list mistakes come from. `appledore new`
   creates a note, `promote` turns a stub or a note into another kind, `set` changes properties,
   `mv` renames or moves a note and `merge` folds one note into another. Each rewrites the links
   it affects, which a plain move breaks, and refuses a change that would add a `check` error.
   - **Pass values on standard input,** one `key=value` a line in a quoted heredoc, because
     inside double quotes the shell runs backticks and expands `$`. Put note names in single
     quotes, writing an apostrophe as `'\''`. `key+=value` adds to a list, `key-=value` takes out
     of one, and a key given twice lists both values:
     ```sh
     appledore set 'Freshness' - <<'EOF'
     summary=A stored response is fresh until its `max-age` runs out.
     aliases+=Freshness lifetime
     EOF
     ```
   - **Before you ask to merge note B into A,** show the user the report lines that
     `appledore merge 'B' 'A' --dry-run` prints above its diff (what now points at A, what is
     deleted, what isn't kept), because a merge deletes B. Leave the diff out, because it holds
     B's text (rule 7). The merge leaves B's summary and text under `## Merged from B` in A, for
     you to fold in.
7. **The user reads in Obsidian.** Never paste a note's text into the chat. After a step writes a
   note for the user to read, open it with `appledore open '<note>'`, and still give the
   `obsidian://` link it prints, because a host with no desktop can't open it. When a step writes
   several notes, open only the one to read first: `APPLEDORE_OPEN=0 appledore open '<note>'`
   prints another note's link without opening it.
8. **Git.** Commit and push the vault only in `wrap-up`. Never touch git history.
9. **A writing helper, one at a time.** Notes written ahead (`learn` step 7), and vault work the
   user asks a helper for, go to a background helper that shares this conversation (in Claude
   Code, a fork), because a question the user types while the tab is busy waits until the work
   ends. Its brief is one line: "You are study rule 9's helper for <the work>: do only that, ask the
   user nothing, open nothing, and end with the report the step gives, or else a link to each note
   you changed and any question you couldn't ask."
   - **While it runs, you write nothing to the vault:** no filing, no added line, no merge, no
     `appledore` write command, and no second writing helper, because two writers on one vault
     lose each other's edits. Answer questions in chat, and say in one line that a write the user
     asks for is queued until the helper reports. The cold reader writes nothing, so it can run.
   - **A message that also asks a question:** answer the question first, saying in the answer's
     first line that a helper is starting, then start the helper and write nothing after the tool
     call, because the user waits on the answer, not on the helper.
   - **Keep a waiting filing offer last:** when your turn goes on after it (a report, inline work),
     end the turn with that offer again, word for word, because `file` step 3 needs it last.
   - **It can't ask the user.** A question a step asks before it writes (a yes under rule 1, a
     reuse choice under rule 2, a gap under rule 4) leaves that note unwritten. One asked after the
     write goes in its report, with the note filed: new concepts under rule 3, or the yes a size
     warning needs to merge a note or make it a `type: note` (`learn` step 4). Such a warning also
     leaves the note without its `unopened` mark.
   - **When it reports,** run `appledore check`, fix what it left, and give the report the step
     says. Ask at once each question that left a note unwritten, and each yes a size warning waits
     for. Before anything that waited on the helper, mark each note it wrote that
     `appledore next '<topic>'` doesn't list after `unopened:`, with
     `appledore set '<title>' status=unopened`, because `next` counts an unmarked subtopic as
     written, so it would skip that note and offer the notes that build on it. For each note the
     user opened while it ran, clear its mark and ask its new-concept question now; keep the
     others' for step 6. Then do what waited on it, each from its step's first item, because the helper's notes
     change what `appledore next` and `appledore find` print: the queued writes, a "next" you told
     to wait (`learn` step 1), `wrap-up`, or the handover, which lists the report's questions under
     Open questions.
   - **`wrap-up` or a handover while it runs:** say in one line that it starts when the helper
     reports, and end your turn, because the commit and the handover take whatever is on disk.
   - **Without such a helper,** answer first, then do the work inline, and say in one line that the
     tab is busy until it's done.

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
   properties, MOCs, names, links and sources. Follow it exactly. The property values these files
   add are a subtopic's `status` marks: `unopened` for a note written ahead and not yet opened, and
   `planned` for a take-over not yet rewritten (study rule 1). Set them where a step says, even
   where the README's table gives subtopics no `status`, because `appledore check` accepts them
   either way. These files don't repeat the README otherwise, because two copies of a rule drift
   apart. After a handover that holds the output of `appledore card` or says to run it, skip this
   read, because that output holds the README's rules word for word.
4. **Effort.** Your host fills in this session's reasoning effort here: `${CLAUDE_EFFORT}`. When it
   reads `xhigh` or `max`, put one line in your first reply, after Start's status line if there is
   one: "Notes and answers come faster at effort `high`: run `/effort`, pick `high`, and press `s`
   to keep it to this session." For a new topic, end that line with: "Keep this level for
   planning, and switch before you say yes to the plan." Do this because at `xhigh` or `max` most
   of a session's waiting is the model thinking, and only planning gains from it. For any other
   value, or the placeholder itself, say nothing about effort.

## Start

- **A topic was named:** run `appledore find '<topic>' --kind topic`.
  - **It exists:** read the topic note. Its Scope says the user's goal and starting point, and its
    Sources are the agreed sources. Run `appledore next '<topic>'`, and tell the user in one line
    where it stands: how many subtopics are written, how many are planned, and the first note it
    lists after `unopened:`, if any. Then route the rest of the message by The loop. A message that
    only names the topic or asks to continue gets that line (with Set up's effort line, if it goes
    out). Then wait for "next" or a node's name, because a note is written only when the user asks
    for it. The line goes first, because `file` step 3 keeps its offer last.
  - **It doesn't:** use `plan`.
- **No topic was named:** `appledore find '' --kind topic` lists the topics. Ask the user which one
  to continue, or what to start.

## The loop

| The user | Use | Its file |
|---|---|---|
| names a topic that has no topic note yet | `plan` | `steps/plan.md` |
| asks for notes written ahead ("write the next 3 while I read") | `learn`, step 7 | `steps/learn.md` |
| says "next", or names a node of the learning graph | `learn` | `steps/learn.md` |
| says "cold read it" about a subtopic | `learn`, step 5 | `steps/learn.md`, which gives `cold-read.md` to a helper |
| asks a question about the topic's subject | `file` | `steps/file.md` |
| asks about the session, the plan, the vault, appledore or your own actions | answer it directly, and file nothing | |
| says "just answer" or "don't file" | `file`, step 3 | `steps/file.md` |
| says "deep dive X", "go deeper on X" or "expand X" | `plan`, Deep dive | `steps/plan.md` |
| says "wrap up" or "done for today", or wants to stop | `wrap-up` | `steps/wrap-up.md` |

**To use a step,** read its file in this skill's folder and follow it. **Before you write any text
into a note,** in any step, read `writing-rules.md` there too. Skip a read only when the file's
full text is already in your context, or, for `steps/learn.md` and `writing-rules.md`, when the
handover you started from holds the output of `appledore card` or says to run it (Handing over,
below). Read again after your context is summarized: the handover's card, or a fresh
`appledore card`, if you were working from it, else the file, because a summary can drop the
text of files you read. Before you fix an `appledore check` error, or a warning the card doesn't
say how to fix, on a note you wrote from the card, read `steps/learn.md` and `writing-rules.md` in
full, because the card leaves out their detail.

When a step finishes, wait for the user's next message and route it again. Anything that fits no
row, answer it and stay in the loop.

## Handing over

When the session moves to a new one, after study rule 9's wait, the handover carries, besides its
own sections:

- **The card:** in a handover file, append it with `appledore card >> '<handover file>'`, the
  file's absolute path in the quotes (`/Users/…`, never `~/…`, which the shell doesn't expand
  there), then check that the file now ends with the README's last rule. In a handover message,
  write "Start the study skill on <topic>, then run `appledore card` and work from its output, in
  place of `steps/learn.md`, `writing-rules.md` and the vault's README." It prints this skill's
  `handover-card.md`, then the vault README's rules word for word.
- **Saved sources:** each saved copy of a source (study rule 4), with its path and the page it
  holds.

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
