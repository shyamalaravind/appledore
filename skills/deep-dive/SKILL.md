---
name: deep-dive
description: >-
  Step of the appledore study loop: expand one node the user picks (a subtopic, a topic a subtopic
  left out, or a note outside every learning graph) into the subtopics that go under it, which
  join the learning graph as planned stubs. Use only inside a study session that the appledore
  study skill started, when the user says "deep dive X", "go deeper on X" or "expand X".
---

# Deep dive

This runs inside an appledore study session. If the `study` skill isn't loaded, load it first: it
sets up `palace` and holds the rules every step follows.

The user decides what gets a deep dive, because only they know which gaps matter for their goal. A
deep dive plans; `learn` writes. So every subtopic is still written one sitting at a time, from
what its prerequisites taught.

## 1. Locate the node

Run `palace related "X"`. Its chain says where X sits:

- **In a topic's learning graph:** X is a subtopic, or a stub whose `mocs` is a subtopic (one it
  left out). Go to 2.
- **Outside every graph:** X is an ordinary note, or a stub under one. Go to 3.

## 2. Expand a node in a graph

1. Read the topic note's Scope and Sources, and the agreed sources' pages on X. If they don't
   cover X, say so and agree a source with the user first (the `study` skill's rule 4).
2. Propose 1–4 new nodes under X, as `plan` proposes a graph: each with a title, a one-line
   summary and what it builds on (X, or another node). Each stays one sitting, within
   `writing-rules.md` rule 7.
3. **If X is a stub a subtopic left out,** X itself joins the graph first: its `mocs` moves from
   that subtopic to the topic note, and that subtopic goes into its `builds_on`. Then X is the
   first node `learn` writes.
4. On the user's yes, write the new stubs in `Stubs/` as `plan` does (`mocs` the topic note,
   `builds_on` set), run `palace graph "<topic>" --write` and `palace check`, and offer to write
   the first ready one with `learn`.

## 3. Expand a node outside every graph

Ask the user which they want:

- **Write X now** as an ordinary note: `type: note`, in their bullet style (a `summary`, then
  bullets, then Sources), written to `writing-rules.md`'s rules for ordinary notes. A stub moves to
  `_Main Notes/` first, with `palace mv "X" "_Main Notes/"`.
- **Make X a topic** of its own, in place: X keeps its name and links. Use `plan` with X as the
  topic. The topic note is X itself: a stub moves to `_Main Notes/` first, and an ordinary note's
  content is cut down to the Overview, with the rest becoming planned subtopics.

Then wait for the user's next message.
