---
name: learn
description: >-
  Step of the appledore study loop: write the next subtopic of a topic's learning graph into the
  vault (one bite-sized note, or a note with a child or two), from the agreed sources and using
  only what its prerequisites taught, ending with the topics it left out on purpose. Use only
  inside a study session that the appledore study skill started, when the user says "next" or
  names a planned node.
---

# Learn

This runs inside an appledore study session. If the `study` skill isn't loaded, load it first: it
sets up `palace` and holds the rules every step follows.

A subtopic is what the user reads in one sitting. It teaches at most 3 new concepts, using only
what the notes it builds on already taught, because a reader can only take in a little that is new
at once, and only on top of what they already hold.

## 1. Pick the node

Run `palace next "<topic>"`.

- **The user said "next":**
  - One subtopic is ready: write it, and say so in one line ("Writing [[X]], which builds on
    [[Y]].").
  - Several are ready: list them, at most 5, with the one you recommend first, and ask.
  - None is planned: say the graph is written, and offer a deep dive on one of the stubs left out,
    or `wrap-up`.
- **The user named a node:**
  - A ready one: write it.
  - A waiting one: name the prerequisites it waits for, and ask whether to write those first.
  - A stub a subtopic left out: that's a deep dive, so use `deep-dive`.

## 2. Gather

1. **Read the notes in its `builds_on`.** They set the words you may use without teaching them
   again: link each at its first mention instead.
2. **`palace related`** on the stub and on those notes, for the notes nearby to link.
3. **Reuse check:** `palace find` on the subtopic's concept and its synonyms. If an existing note
   already covers it, ask the user: take that note over, or write this one and link it. Taking it
   over merges the stub into the note (the `study` skill's rule 6), and the note becomes the
   subtopic: it keeps its name, and gets `type: subtopic`, `mocs` the topic and the stub's
   `builds_on`.
4. **Read the agreed sources** where they cover this node. If they don't cover part of it, stop
   before writing: tell the user which part, and agree a source or leave that part out (the
   `study` skill's rule 4).

## 3. Write

Write to `writing-rules.md`:

- **Size:** 150–450 words in total, usually 200–350, however many notes it spans, with at most 3
  new concepts. Use as few as the node needs, and never pad.
- **One note or several, whichever fits the palace best.** The subtopic is a node of the graph,
  not a file, so its words can sit in one note or in a note with child notes. Give a part a child
  note of its own when it is a concept the palace will use on its own: other notes will link to
  it, it will gather questions of its own, or it already exists as a note (then link it, never
  copy it). The connecting explanation stays in the subtopic's main note. A child gets
  `type: subtopic`, `mocs` the main note and an empty `builds_on`. Never make a subtopic a MOC: a
  node that needs a map of its own is a topic.
- **Left out on purpose:** 2–4 topics the sources raise here that this subtopic skips. Run
  `palace find` on each. One that has a note gets a link. One that doesn't becomes a stub in
  `Stubs/`, from `__templates/Stub.md`, with a one-sentence `summary`, `mocs` this subtopic, and a
  `## Sources` line for the page that covers it. The user expands them later with a deep dive.

## 4. File it

1. `palace mv "<title>" "_Main Notes/"` moves the stub out of `Stubs/`.
2. Rewrite the note in the shape of `__templates/Subtopic.md`. Keep its `mocs`, `builds_on`,
   `aliases` and `created`, add `type: subtopic`, and rewrite `summary` so it says what the note
   now says.
3. `palace graph "<topic>" --write`, then `palace check`. Don't leave a size warning:
   - **Over 450 words:** cut what the note's question doesn't need, or split the node.
   - **Under 150 words:** the node is too thin for a sitting. Never pad it: ask the user whether to
     merge it into a neighbouring node or make it a `type: note`.

## 5. Cold read, only when the user asks

Run this step only when the user asks for it ("cold read it", "check this one"), because a read
and its fixes roughly double the time a note takes, and the writing rules alone carry the
quality. Skip it if your host can't start a helper agent with no tools. In Claude Code, it is the
plugin's `cold-reader` agent.

1. **The brief:** the text of `cold-read.md` next to this file, then the reader, then the note.
   - **The reader:** the topic note's `Starting from:` line, plus the title and `summary` of each
     note in `builds_on`. That is all the cold reader may assume.
   - **The note:** its text with line numbers, frontmatter included, because the body doesn't
     repeat the `summary`. For a subtopic with children, each note's title, then its numbered text.

   Never give it the writing rules: it tests what the text gives a newcomer, not whether the text
   follows rules.
2. **Start a fresh helper** with the brief as its prompt. It sees nothing else, which is what
   makes the read cold.
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

In a few lines:

- the note's `obsidian://` link (several, if it spans notes);
- the new concepts it teaches, in one line;
- the stubs it left out, as links;
- the new-concept question (the `study` skill's rule 3), if any concepts are waiting.

Then wait. The user reads, and comes back with "next", a question, a deep dive, or a request for
a cold read (step 5), which you run on the note they just read.
