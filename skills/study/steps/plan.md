# Plan

The plan is made with the user, because only they know what the topic is for and how far to go.
Nobody can learn all of a field, so the plan sets the edges before anything is written.

Two requests land here. Both propose nodes, wait for the user's yes and write stubs, which `learn`
then writes one sitting at a time:

- **A new topic,** one with no topic note yet: steps 1–5.
- **"Deep dive X":** X grows the subtopics that go under it (Deep dive, at the end).

## 1. Look in the vault

- One `appledore find` with the topic, its synonyms and its key words, each its own argument: it
  prints each matching note once, with its title, kind and the start of its summary. Then the
  same call with `--body`, for only the searches it lists after `no matches:`, because a body
  search prints every name match again. `appledore find '<title>'` gives one note's whole summary.
- `appledore tree --mocs` for the MOC chains: the MOCs and topics with their summaries, and the
  notes directly under a MOC. Then `appledore related` on the two or three likeliest parents.
  These stay their own calls, because placement needs the MOC chains, and both print titles and
  summaries, never a note's text.
- Read a note's own text only when its summary leaves open whether it covers part of the topic,
  because everything read here stays in your context for the whole session.

Note what the vault already has: notes on the topic or its parts, and where the topic could sit.

## 2. Ask about sources, goal and placement

Ask in one message, with your recommendation for each, so the user can reply "all fine":

1. **Sources:** 2–5 pages, courses or books, with official sources first: the standard or the
   vendor's own documentation, listed ahead of explainers and tutorials. Include any the user has
   named. For documentation published per version, name the version you recommend: the latest
   stable release you know of, unless the goal needs another. Propose them without fetching or
   checking any yet, because the user may swap a source or pick another version, which throws that
   work away. Step 3 checks the version, then the pages they agree to.
2. **Goal and starting point:** what the topic is for (an interview, work, curiosity), which sets
   how deep to go, and what the user already knows, which sets what the notes may take for
   granted. Propose as known only what the vault's notes show (step 1), and ask about the rest,
   because a guessed starting point skips what the user never learned.
3. **Placement:** the topic note's parent, which is an existing MOC or note, or a new MOC with its
   own parent. Follow the README's MOC rules: a MOC needs five or more notes under it, and at most
   two MOC levels sit above a topic.

## 3. Propose the learning graph

1. **Check the version first,** for documentation published per version, before any other read,
   because step 2's version came from memory, and outlines read for the wrong version are read
   again. Save and read the documentation's own list of versions, as study rule 4 says for any page.
   - **It lists a stable release newer than the agreed one:** switch to it, and say so in one line,
     because the user agreed to the latest stable release.
   - **Step 2 recommended an older release for the goal, or the documentation lists no
     versions:** keep the agreed one.
2. **Read the outlines,** the sources' contents pages and overview sections, not whole pages, so
   the graph follows how the material is built. Say first what you're reading ("Reading the
   outlines of 4 sources"), because a long read in silence looks stuck.
3. **Check that each source's text is really there,** as `SKILL.md`'s Gotchas say, once per
   page, on the copy you saved under study rule 4, and tell the user what a thin one can back.

Then propose:

- **The scope:** what's in and what's out, in 2–5 lines, set by the goal.
- **The graph:** 4–10 subtopics as an indented tree, simplest first. Each line gives the title
  (a canonical name, as the README says), a one-line summary, and what it builds on.
  - **One sitting each:** a 2–3 minute read, within `writing-rules.md` rule 7. A node that needs
    more becomes two nodes, and one too thin for a sitting folds into its neighbour.
  - **The goal decides what gets a node, then the sources:** a part the goal needs only in
    passing folds into the neighbour it serves, as a bullet or two named in that neighbour's stub
    `summary`, because a sitting of its own spends the user's time on it. A part the goal needs
    but the sources cover only briefly gets a shallow node of its own when what they cover fills
    a sitting, and its deeper parts become stubs under it now, for a deep dive. Don't fetch pages to deepen it, because the user
    decides what goes deeper.
  - **From the agreed sources only:** mark a node they don't cover "not in the sources", so you
    and the user can agree a source for it or cut it.
- **Known nodes:** notes already in the vault that a subtopic builds on. They go into `builds_on`
  as they are.
- **Take-overs:** a note whose concept *is* a planned subtopic. It becomes that subtopic instead of
  getting a second note beside it: it is rewritten to `writing-rules.md`, keeps its name and links, and its
  `mocs` moves to the topic. Mark each one.

Ask the user to change, add or cut nodes, and revise until they agree. In the first proposal, if
Set up's effort line went out, end it with: "Switch to effort `high` before your yes (`/effort`,
`high`, `s`): the writing starts on your yes."

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
   - **Sources:** the `source` lines, each a link with its title, followed by "(needs your
     login)" for a page behind a login.
3. **One stub per planned subtopic, and a mark on each take-over,** all in one shell call
   joined with `&&`, so the first refusal stops the rest, prerequisites first, since `new`
   refuses a link to a missing note. A stub: `appledore new stub '<title>'`, with a `summary`
   saying what it will teach, `mocs` the topic, and a `builds_on` for each prerequisite (a planned
   stub or a known note). The `builds_on` is what lets `appledore next` tell which subtopic is
   ready. A shallow node's deeper parts get stubs too, at most four, each with `mocs` that node's
   stub and no `builds_on`, so the graph draws them as left out under it. A take-over:
   `appledore promote '<note>' subtopic`, with `mocs` the topic, its planned `builds_on` and
   `status=planned`, which puts it in the graph unwritten; `learn` rewrites it when "next"
   reaches it.
4. `appledore check`.

## 5. Hand back

Use `learn` for the node `appledore next '<topic>'` recommends, a stub or a take-over, and hand
it to the user with its step 6, with the topic note's link and the graph as
`appledore graph '<topic>'` prints it. Write nothing else: each other take-over is rewritten when
"next" reaches it, like any note, because the user's yes to the plan isn't a "next".

Done when every planned subtopic has its stub, every take-over is marked `planned`,
`appledore check` shows no error, and the user has the first note, or its question, and the
graph.

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
   `writing-rules.md` rule 7. Look for each one first, as study rule 2 says: one the vault
   already has isn't proposed again. A written note or planned stub that a node needs goes into
   its `builds_on`, as step 4 does, but a stub a subtopic left out is only linked, or proposed to
   join the graph as X is (item 4), because `appledore next` never makes a node that builds on
   it ready. Step 3's folding never takes every part into X here: at least one new node stays,
   because the user asked to go past X.
3. **If the agreed sources run out at X,** with too little beyond what X's own sitting teaches to
   fill another, still propose the nodes: mark what the sources don't cover "not in the sources",
   as step 3 does, and follow study rule 4 for it.
4. **If X is a stub a subtopic left out,** propose that X itself joins the graph, as the first
   node `learn` writes, even when the agreed sources run out at X.
5. On the user's yes, move each left-out stub that joins (X, or one from item 2) into the graph
   with `appledore set`: `mocs` the topic and `builds_on` the subtopic that left it out. Create
   the new stubs as step 4 does, run `appledore check`, and offer to write the first ready one
   with `learn`.

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
