# Learn

A subtopic is what the user reads in one sitting. It teaches at most 3 new concepts, using only
what the notes it builds on already taught, because a reader can only take in a little that is new
at once, and only on top of what they already hold.

## 1. Pick the node

Run `appledore next '<topic>'`.

- **The user said "next":**
  - It prints `recommended:` with a note marked `(unopened)` that you haven't opened: open it with
    step 6, and write nothing, because it is already written and the user reads in order.
  - A writing helper is still running (study rule 9): when it writes notes ahead, open the first
    note `unopened:` lists that you haven't opened, with step 6; with none, say in one line that
    the next note comes when the helper files it. When it does other work, say that "next" is
    queued until it reports. Write nothing either way.
  - It recommends a node marked `(take-over)`: run step 2 on it first, from the note's own content
    and the sources. With a question left, ask it and write nothing, because the note stays
    planned and what builds on it waits. Else go on with steps 3–4.
  - A node is ready: write the one it prints as `recommended:`, the shallowest ready one, and
    say so in one line that names the others ready ("Writing [[X]], which builds on [[Y]]; also
    ready: [[Z]]."). Don't ask when several are ready, because "next" already says to go on, and
    one word from the user redirects it.
  - Planned, but none ready: give the `waiting:` lines, and ask whether to write the missing
    prerequisite first or change the `builds_on`.
  - None is planned: say the graph is written, give the topic's stubs to explore as
    `appledore next '<topic>' --left-out` prints them, and offer a deep dive on one, or `wrap-up`.
- **The user named a node:**
  - One marked unopened: open it with step 6.
  - Any other while a writing helper runs: say in one line that it is queued until the helper
    reports, and write nothing.
  - A take-over that is ready: as for "next" above.
  - A ready one: write it.
  - A waiting one: name the prerequisites it waits for, and ask whether to write those first.
  - A stub a subtopic left out: that's a deep dive, so use `plan`'s Deep dive.

## 2. Gather

1. **Read the notes in its `builds_on`.** They set the words you may use without teaching them
   again: link each instead, as `writing-rules.md` rule 4 says.
2. **`appledore related`** on the stub and on those notes, for the notes nearby to link.
3. **Reuse check:** `appledore find` on the subtopic's concept and its synonyms. If an existing
   note already covers it, ask the user, with the report lines of
   `appledore merge '<stub>' '<note>' --dry-run` (study rule 6): take that note over, or write
   this one and link it. To take it over, run that merge, then
   `appledore promote '<note>' subtopic`, with `mocs` the topic.
4. **Read the agreed sources** where they cover this node, from the copy you saved under study
   rule 4. If they don't cover part of it, stop before writing, and settle that part as study
   rule 4 says.

## 3. Write

Write to `writing-rules.md`. Its rule 7 sets the size, across every note the subtopic spans.
Write the text into the stub itself, above its `## Sources`, in the shape of
`__templates/Subtopic.md`. It stays a stub until step 4, so a session that stops halfway never
leaves `next` counting it as written. A note taken over (step 2, or `plan`'s take-overs) is
already a subtopic: rewrite it in place, and step 4's `promote` then only updates its summary and
clears its `planned` mark.

- **One note or several.** The subtopic is a node of the graph, not a file, so its words can sit
  in one note or in a note with child notes, and rule 14 says when a part gets a child note. A
  child is `appledore new child '<child>'`, with its `summary` and `mocs` the main note. Never
  make a subtopic a MOC: a node that needs a map of its own is a topic.
- **Left out on purpose:** 2–4 topics the sources raise here that this subtopic skips. Start
  with the stubs already under it, the children `appledore related` lists, then add others up to
  four. Run `appledore find` on each new one. One that has a note gets a link. One that doesn't
  becomes a stub: `appledore new stub '<title>'`, with a one-sentence `summary`, `mocs` this
  subtopic, and a `source` for the page that covers it. The user expands them later with a deep
  dive.

## 4. File it

1. `appledore promote '<title>' subtopic`, with a `summary` that says what the note now says,
   moves it to `_Main Notes/` as a subtopic. For a take-over, add `status=`, which clears its
   `planned` mark, so it counts as written.
2. `appledore check`. Don't leave a size or shape warning. Fix a size warning as
   `writing-rules.md` rule 7 says, and ask the user before you merge a node or make it a
   `type: note`. Fix a shape warning (a missing part, a Left out list outside 2–4, more than
   three bold terms, a summary over 25 words) in the note, because the reader looks for each part
   where every other subtopic has it.

## 5. Cold read, only when the user asks

Run this step only when the user asks for it ("cold read it", "check this one"), because a read
and its fixes roughly double the time a note takes, and the writing rules alone carry the
quality. Skip it if your host can't start a helper agent with no tools. In Claude Code, it is the
plugin's `cold-reader` agent.

1. **The brief:** run `appledore brief '<title>'`. It prints the text of `cold-read.md`, the reader
   (the topic's `Starting from:` line, and the title and `summary` of each note in `builds_on`)
   and the note's text with line numbers. Add nothing to it, not even the writing rules: the read
   tests what the text gives a newcomer, not whether the text follows rules.
2. **Start a fresh helper** with that output, word for word, as its prompt. It sees nothing else,
   which is what makes the read cold.
3. **Fix** what it reports where the text is at fault: a term used before it's defined, a concept
   whose reason to exist it couldn't find, a rule without its reason, a bare fact, too much new at
   once, a part it couldn't paraphrase, a place it read twice. Find the writing rule each finding
   breaks, and fix the line where the reader met
   it. Ignore a finding the cited lines already answer, and a question only someone putting the
   note to use would ask, because those are what the user's own questions are for. Keep the size
   limits.
4. **One round, two at most.** Start a second fresh helper only if the fixes changed more than a
   few sentences, because a helper that has seen the note once already knows what it meant.

## 6. Hand it to the user

Do this straight after step 4, or, for a note written ahead, when "next" reaches it (step 1).
Step 5 runs only later, on request.

Open it with `appledore open '<title>'` (its main note, if it spans notes). If it is marked
`status: unopened`, clear the mark with `appledore set '<title>' status=`, because
`appledore next` offers it until then; while a writing helper runs, that `set` waits for its
report (study rule 9). Then in a few lines:

- the note's `obsidian://` link (several, if it spans notes);
- the new concepts it teaches, in one line;
- what "next" brings: while a writing helper runs, the next note `unopened:` lists after this one,
  or "the next note, when the helper files it"; else what `appledore next '<topic>'` now prints
  after `recommended:`, if it prints one: a note marked unopened opens, a take-over is rewritten,
  and a stub is written;
- the stubs it left out, as links. If `appledore next '<topic>'` now shows nothing planned and no
  note after `unopened:`, give the topic's whole list instead, as
  `appledore next '<topic>' --left-out` prints it, and how to pick one: "deep dive <stub>";
- the new-concept question (study rule 3), if any concepts are waiting. For a note the helper
  wrote, they are in its report; one you open before the report gets its question then (study
  rule 9).

Then wait. The user reads, and comes back with "next", a question, a deep dive, or a request for
a cold read (step 5), which you run on the note they just read.

## 7. Write ahead, only when the user asks

When the user asks for notes written ahead ("write the next 3 while I read"), a writing helper
writes them, as study rule 9 says. Write ahead only on that request, because notes the user hasn't
read pile up, and they read in order.

1. Tell the user in one line how many notes are being written ahead, starting with the node
   `appledore next '<topic>'` prints after `write next:`, or after `recommended:` when that names
   a stub or a take-over.
2. The helper writes them one at a time, each with steps 2–4, on the node item 1's rule gives each
   time. A node it leaves with a question doesn't count toward the number; it takes the first
   other node `ready:` lists instead. Its step 4 marks the note only once `check` shows no size or
   shape warning on it: `appledore set '<title>' status=unopened` after the fixes, so the note
   waits for the user's "next" (step 1) only when it is finished. A size warning that needs the
   user's yes (step 4) leaves the note unmarked, with that question in its report (study rule 9).
   It stops at the number asked for
   (when the user names none, up to three) or when no node is ready, and opens none of them,
   because the user is reading another note.
3. Its report gives, for each note in reading order: the link as
   `APPLEDORE_OPEN=0 appledore open '<note>'` prints it, the new concepts in one line, the stubs it
   left out, any question it couldn't ask, and each page it saved, with its path. Give the user the
   links, one line each, and the questions that left a note unwritten; keep the rest for step 6.

Done when each note is filed and marked unopened, or reported back with its question, and the user
has the links.
