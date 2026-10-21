---
name: plan
description: >-
  Step of the appledore study loop: plan a new topic with the user (its sources, its goal and
  depth, where it sits in the vault, and its learning graph of subtopics), then write the topic
  note and one stub per planned subtopic. Use only inside a study session that the appledore study
  skill started, when the topic has no topic note yet.
---

# Plan

This runs inside an appledore study session. If the `study` skill isn't loaded, load it first: it
sets up `palace` and holds the rules every step follows.

The plan is made with the user, because only they know what the topic is for and how far to go.
Nobody can learn all of a field, so the plan sets the edges before anything is written.

## 1. Look in the vault

- `palace find "<topic>"`, then its synonyms and key words, then the same with `--body`.
- `palace tree --summary` for the MOC chains, and `palace related` on the two or three likeliest
  parents.

Note what the vault already has: notes on the topic or its parts, and where the topic could sit.

## 2. Ask about sources, goal and placement

Ask in one message, with your recommendation for each, so the user can reply "all fine":

1. **Sources:** 2–5 pages, courses or books, with official documentation first. Include any the
   user has named.
2. **Goal and starting point:** what the topic is for (an interview, work, curiosity), which sets
   how deep to go, and what the user already knows nearby, which sets what the notes may take for
   granted.
3. **Placement:** the topic note's parent, which is an existing MOC or note, or a new MOC with its
   own parent. Follow the README's MOC rules: a MOC needs five or more notes under it, and at most
   two MOC levels sit above a topic.

## 3. Propose the learning graph

Read the sources' contents pages and overview pages first, so the graph follows how the material
is built. Then propose:

- **The scope:** what's in and what's out, in 2–5 lines, set by the goal.
- **The graph:** 4–10 subtopics as an indented tree, simplest first, each a part the agreed
  sources cover. Mark a node the sources don't cover "not in the sources", so you and the user
  can agree a source for it or cut it. Each line gives the title
  (a canonical name, as the README says), a one-line summary, and what it builds on. A subtopic is
  one sitting, a 2–3 minute read: 150–450 words with at most 3 new concepts. A node that needs
  more becomes two nodes, and one too thin for a sitting merges into a neighbour.
- **Known nodes:** notes already in the vault that a subtopic builds on. They go into `builds_on`
  as they are.
- **Take-overs:** a note whose concept *is* a planned subtopic. It becomes that subtopic instead of
  getting a second note beside it: it is rewritten to `writing-rules.md`, keeps its name and links, and its
  `mocs` moves to the topic. Mark each one.

Ask the user to change, add or cut nodes, and revise until they agree.

## 4. Write the plan into the vault

On the user's yes, writing every note from its template in `__templates/`:

1. **A new MOC,** if they chose one, in `_-MOCs/`.
2. **The topic note** in `_Main Notes/`, from `Topic.md`: `summary`, `type: topic`,
   `status: learning`, `mocs` the agreed parent, and `builds_on` any whole topic it needs first.
   - **Overview:** at most 100 words from the sources, written to `writing-rules.md`: one line on
     the problem, then 2–4 bullets.
   - **Scope:** `Goal:`, `Starting from:`, `In:` and `Out:`, one line each.
   - **Sources:** the agreed sources, each a link with its title.
3. **One stub per planned subtopic** in `Stubs/`, from `Stub.md`: a `summary` saying what the
   subtopic will teach, `mocs` the topic note, and `builds_on` its prerequisites (other planned
   stubs or known notes). The `builds_on` is what lets `palace next` tell which subtopic is ready.
4. **Each take-over** now, with the `learn` skill's steps 2–4, starting from the note's own content
   and the sources. It gets `type: subtopic`, `mocs` the topic, and its planned `builds_on`.
5. `palace graph "<topic>" --write`, then `palace check`.

## 5. Hand back

Give the user the topic note's link and the graph as `palace graph "<topic>"` prints it, then use
`learn` for the first ready subtopic.
