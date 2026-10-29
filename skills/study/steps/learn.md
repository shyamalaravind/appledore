# Learn

A subtopic is what the user reads in one sitting. It teaches at most 3 new concepts, using only
what the notes it builds on already taught, because a reader can only take in a little that is new
at once, and only on top of what they already hold.

## 1. Pick the node

Run `appledore next "<topic>"`.

- **The user said "next":**
  - One subtopic is ready: write it, and say so in one line ("Writing [[X]], which builds on
    [[Y]].").
  - Several are ready: list them, at most 5, with the one you recommend first, and ask.
  - None is planned: say the graph is written, give the topic's stubs to explore as
    `appledore next "<topic>" --left-out` prints them, and offer a deep dive on one, or `wrap-up`.
- **The user named a node:**
  - A ready one: write it.
  - A waiting one: name the prerequisites it waits for, and ask whether to write those first.
  - A stub a subtopic left out: that's a deep dive, so use `plan`'s Deep dive.

## 2. Gather

1. **Read the notes in its `builds_on`.** They set the words you may use without teaching them
   again: link each instead, as `writing-rules.md` rule 4 says.
2. **`appledore related`** on the stub and on those notes, for the notes nearby to link.
3. **Reuse check:** `appledore find` on the subtopic's concept and its synonyms. If an existing
   note already covers it, ask the user: take that note over, or write this one and link it.
   Taking it over merges the stub into the note (study rule 6), and the note becomes the subtopic:
   it keeps its name, and gets `type: subtopic`, `mocs` the topic and the stub's `builds_on`.
4. **Read the agreed sources** where they cover this node. If they don't cover part of it, stop
   before writing, and settle that part as study rule 4 says.

## 3. Write

Write to `writing-rules.md`. Its rule 7 sets the size, across every note the subtopic spans.

- **One note or several.** The subtopic is a node of the graph, not a file, so its words can sit
  in one note or in a note with child notes, and rule 14 says when a part gets a child note. A
  child gets `type: subtopic`, `mocs` the main note and an empty `builds_on`. Never make a
  subtopic a MOC: a node that needs a map of its own is a topic.
- **Left out on purpose:** 2–4 topics the sources raise here that this subtopic skips. Run
  `appledore find` on each. One that has a note gets a link. One that doesn't becomes a stub in
  `Stubs/`, from `__templates/Stub.md`, with a one-sentence `summary`, `mocs` this subtopic, and a
  `## Sources` line for the page that covers it. The user expands them later with a deep dive.

## 4. File it

1. `appledore mv "<title>" "_Main Notes/"` moves the stub out of `Stubs/`.
2. Rewrite the note in the shape of `__templates/Subtopic.md`. Keep its `mocs`, `builds_on`,
   `aliases` and `created`, add `type: subtopic`, and rewrite `summary` so it says what the note
   now says.
3. `appledore graph "<topic>" --write`, then `appledore check`. Don't leave a size or shape
   warning. Fix a size warning as `writing-rules.md` rule 7 says, and ask the user before you
   merge a node or make it a `type: note`. Fix a shape warning (a missing part, a Left out list
   outside 2–4, more than three bold terms, a summary over 25 words) in the note, because the
   reader looks for each part where every other subtopic has it.

## 5. Cold read, only when the user asks

Run this step only when the user asks for it ("cold read it", "check this one"), because a read
and its fixes roughly double the time a note takes, and the writing rules alone carry the
quality. Skip it if your host can't start a helper agent with no tools. In Claude Code, it is the
plugin's `cold-reader` agent.

1. **The brief:** run `appledore brief "<title>"`. It prints the text of `cold-read.md`, the reader
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

Do this straight after step 4. Step 5 runs only later, on request.

Open it with `appledore open "<title>"` (its main note, if it spans notes), then in a few lines:

- the note's `obsidian://` link (several, if it spans notes);
- the new concepts it teaches, in one line;
- the stubs it left out, as links. If `appledore next "<topic>"` now shows nothing planned, give
  the topic's whole list instead, as `appledore next "<topic>" --left-out` prints it, and how to
  pick one: "deep dive <stub>";
- the new-concept question (study rule 3), if any concepts are waiting.

Then wait. The user reads, and comes back with "next", a question, a deep dive, or a request for
a cold read (step 5), which you run on the note they just read.
