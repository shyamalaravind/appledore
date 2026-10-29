# Plan

The plan is made with the user, because only they know what the topic is for and how far to go.
Nobody can learn all of a field, so the plan sets the edges before anything is written.

Two requests land here. Both propose nodes, wait for the user's yes and write stubs, which `learn`
then writes one sitting at a time:

- **A new topic,** one with no topic note yet: steps 1–5.
- **"Deep dive X":** X grows the subtopics that go under it (Deep dive, at the end).

## 1. Look in the vault

- `appledore find '<topic>'`, then its synonyms and key words, then the same with `--body`.
- `appledore tree --mocs` for the MOC chains: the MOCs and topics with their summaries, and the
  notes directly under a MOC, which is all placement needs. Then `appledore related` on the two or
  three likeliest parents.

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
  one sitting, a 2–3 minute read, within `writing-rules.md` rule 7. A node that needs more
  becomes two nodes, and one too thin for a sitting merges into a neighbour.
- **Known nodes:** notes already in the vault that a subtopic builds on. They go into `builds_on`
  as they are.
- **Take-overs:** a note whose concept *is* a planned subtopic. It becomes that subtopic instead of
  getting a second note beside it: it is rewritten to `writing-rules.md`, keeps its name and links, and its
  `mocs` moves to the topic. Mark each one.

Ask the user to change, add or cut nodes, and revise until they agree.

## 4. Write the plan into the vault

On the user's yes, create each note with `appledore new`, from its kind's template, passing its
values as study rule 6 says:

1. **A new MOC,** if they chose one: `appledore new moc '<title>'`, with its `summary` and `mocs`.
2. **The topic note:** `appledore new topic '<topic>'`, with its `summary`, `mocs` the agreed
   parent, a `builds_on` for any whole topic it needs first, and a `source` for each agreed
   source. Then write its body:
   - **Overview:** at most 100 words from the sources, written to `writing-rules.md`: one line on
     the problem, then 2–4 bullets.
   - **Scope:** `Goal:`, `Starting from:`, `In:` and `Out:`, one line each.
3. **One stub per planned subtopic,** prerequisites first, since `new` refuses a link to a missing
   note: `appledore new stub '<title>'`, with a `summary` saying what it will teach, `mocs` the
   topic, and a `builds_on` for each prerequisite (a planned stub or a known note). The
   `builds_on` is what lets `appledore next` tell which subtopic is ready.
4. **Each take-over** now: `appledore promote '<note>' subtopic`, with `mocs` the topic and its
   planned `builds_on`, then `learn`'s steps 2–4, starting from the note's own content and the
   sources.
5. `appledore check`.

## 5. Hand back

Give the user the topic note's link and the graph as `appledore graph '<topic>'` prints it, then
use `learn` for the first ready subtopic.

## Deep dive

The user decides what gets a deep dive, because only they know which gaps matter for their goal. A
deep dive plans and `learn` writes, so every subtopic is still written one sitting at a time, from
what its prerequisites taught.

Run `appledore related 'X'`. Its chain says where X sits:

- **In a topic's learning graph:** X is a subtopic, or a stub whose `mocs` is a subtopic (one it
  left out). Expand it in the graph, below.
- **Outside every graph:** X is an ordinary note, or a stub under one. Go to Outside every graph,
  below.

### In a graph

1. Read the topic note's Scope and Sources, and the agreed sources' pages on X. If they don't
   cover X, follow study rule 4 first.
2. Propose 1–4 new nodes under X, as step 3 proposes a graph: each with a title, a one-line
   summary and what it builds on (X, or another node). Each stays one sitting, within
   `writing-rules.md` rule 7.
3. **If X is a stub a subtopic left out,** propose that X itself joins the graph, as the first
   node `learn` writes.
4. On the user's yes, put such an X in the graph with `appledore set 'X'`, `mocs` the topic and
   `builds_on` the subtopic that left it out. Create the new stubs as step 4 does, run
   `appledore check`, and offer to write the first ready one with `learn`.

### Outside every graph

Ask the user which they want:

- **Write X now** as an ordinary note, in their bullet style (a `summary`, then bullets, then
  Sources), written to `writing-rules.md`'s rules for ordinary notes. A stub becomes one first,
  with `appledore promote 'X' note`. Once it's written, open it with `appledore open 'X'`, and give
  its link.
- **Make X a topic** of its own, in place: X keeps its name and links. Plan it with steps 1–5, X
  being the topic. The topic note is X itself, made one with `appledore promote 'X' topic` instead
  of `new`, and an ordinary note's content is cut down to the Overview, with the rest becoming
  planned subtopics.

Then wait for the user's next message.
