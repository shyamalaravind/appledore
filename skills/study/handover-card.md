# Handover card

A study session that hands over passes this card on with `appledore card`, which adds the vault
README's rules after it. In the new session the two stand in for `steps/learn.md`,
`writing-rules.md` and the README, which hold the full text.

## Learn (`steps/learn.md`)

- **1. Pick,** on "next": run `appledore next '<topic>'`.
  - `recommended:` names a note marked `(unopened)` that you haven't opened: open it with step 6,
    and write nothing.
  - A writing helper is still running (study rule 9): when it writes notes ahead, open the first
    note `unopened:` lists that you haven't opened, with step 6, or, with none, say the next note
    comes when the helper files it; when it does other work, say "next" is queued until it reports.
    Write nothing either way.
  - A node marked `(take-over)`: step 2 on it first, from its own text and the sources. With a
    question left, ask it and write nothing; else steps 3–4.
  - Else write the recommended stub. None ready: give its `waiting:` lines, and ask whether to write
    the prerequisite first or change the `builds_on`. None planned: say the graph is written, give
    `appledore next '<topic>' --left-out`, and offer a deep dive or `wrap-up`.
  - Named by the user: unopened, open it with step 6; any other while a writing helper runs, queued
    until it reports; a ready take-over, as above; ready, write it; waiting, name its prerequisites
    and ask whether to write those first; a left-out stub, `plan`'s Deep dive.
- **2. Gather:** read the notes in `builds_on`, and link them rather than teach them again.
  `appledore related` on the stub and on them. `appledore find` on the concept and its synonyms;
  on a hit, ask whether to take that note over (merge, then promote) or write this one and link
  it, with the report lines of `appledore merge '<stub>' '<note>' --dry-run`. Read the saved
  copies of the agreed sources where they cover the node, and stop on a gap (study rule 4).
- **3. Write:** into the stub, above `## Sources`, in the shape of `__templates/Subtopic.md`. A part
  other notes will use on its own is a child note (`appledore new child`). Left out on purpose:
  2–4, the stubs already under it first; `appledore find` each new one, and link it if it has a
  note, else `appledore new stub` with a one-sentence `summary`, `mocs` this subtopic and a `source`.
- **4. File:** `appledore promote '<title>' subtopic`, with a `summary` of what the note now says,
  and `status=` for a take-over, then `appledore check`. Leave no size or shape warning, and ask the
  user before you merge a node or make it a `type: note`.
- **5. Cold read:** only on request; read `steps/learn.md` step 5 then.
- **6. Hand it to the user:** `appledore open`; clear an `unopened` mark with
  `appledore set '<title>' status=` (while a writing helper runs, at its report); then the link, the
  new concepts in one line, what "next" brings, the left-out stubs as links, or the topic's whole
  `--left-out` list when nothing is planned, and the new-concept question (study rule 3). Then wait.
- **7. Write ahead:** only on request; read `steps/learn.md` step 7 then.

## Writing (`writing-rules.md`)

The reader knows the topic's Scope and what the `builds_on` notes taught, and nothing else. They
scan.

- **1.** Every number and "how it works" claim comes from an agreed page; when none states it,
  study rule 4 says what to do. Numbers exact, quotes of at most two sentences. Name a source in the line only for a
  judgment (a threshold, a "typical" value) or a disagreement: follow the official source (between
  equals, the newer), name the disagreement, and say which you followed and why. Link a volatile
  fact, such as a limit or a price, to its page.
- **2.** A comparison with what the reader knows may take one bullet, and says where it stops
  holding, in that bullet or the one under it.
- **3.** Define each term where it first appears, in words the reader has, or use plain words. One
  word for each thing, one meaning for each word; say when a familiar word means something new
  here. No undefined jargon: vendor phrases ("unstructured data", "scenarios") become plain words.
- **4.** Link a note at its first mention in every note, even when another note links it. For a
  term an earlier note taught, add a reminder of a few words instead of a definition.
- **5.** Every rule, limit and default gets its scope ("blob names", not "names") and its
  "because", in the bullet or under it: the sources' reason, else what follows from the rule,
  never an invented one.
- **6.** Under each `##`, bullets: one fact each, about 20 words, at most five a group, one level of
  sub-bullets for detail, reason or example. A fragment is fine when the bullet above gives its
  subject; name who acts when it isn't obvious. Keep because, so, unless and instead of; cut
  announcing lines, recaps, empty hedges, idioms and emoji. Code is complete (every import, field
  and method body, no `...`), commented on each step, and counts toward no limit, so it is never
  shortened to fit one.
- **7.** At most three new concepts in 150–450 words, usually 200–350, and only as many words as
  the subtopic needs, never padded. A new concept is a term the reader doesn't know and the note keeps using. Bold each
  once, as the label of the bullet that defines it, and bold nothing else but rule 8's labels. When
  the sources show it in a tool, say where it lives there (the class, method, built-in or setting).
  Cut what the subtopic doesn't need (name lengths, quotas, account limits), or make it a Left out
  item. Past 450 words, move a part into a new subtopic, never a child note, whose words still
  count; under 150, merge the node or make it a `type: note`, after asking the user.
- **8.** Open with two labelled lines. `**In short:**`, never "Answer", gives the point and the
  problem it solves, never a copy of the `summary`, and in a subtopic that changes an earlier flow,
  what the change fixes. `**Example:**` gives one case in real names and numbers, never placeholders
  like `<account>`, with each name's kind ("container `videos` of account `contosomedia`"), and
  later bullets reuse it. A case from an earlier note gets a short reminder, not its full setup.
- **9.** At most three `##` parts, each named for what it explains. When the concept gets around a
  constraint, `## Why it exists` comes first: the constraints in order, each with its because,
  ending with the concept as the way out. A mechanism with two or more actors: numbered steps on
  the Example, each a text arrow of who holds or does what
  (`2. Worker: wait() lets go of the lock → sleeps`). Any other flow of three or more steps: a text
  arrow or Mermaid of at most six nodes, in the note's own words. Nest the steps or the flow under the bullet they show. At most one
  callout: a `> [!warning]` titled with the correction, after its section's
  bullets, for a trap (a wrong belief the reader probably holds that would cause a real mistake).
- **10.** Close the body with `## In an interview`, or the goal's use: 1–3 bullets on what you'd
  say or decide and the mistake it prevents, never a recap.
- **11.** Left out on purpose: 2–4 links, each with the question its note will answer, in plain
  words.
- **12.** A topic's Overview: at most 100 words, the problem in one line in the reader's terms, then
  2–4 linked bullets on the one model the subtopics build on. Don't list the subtopics or restate
  the `summary`.
- **13.** Filing an answer: when the question shows that a bullet failed to define a term or give
  a reason, repair that bullet where it stands before adding anything.
- **14.** Then put the new text in the first place that fits, at about 60 words and one new
  concept, with the subtopic still within rule 7's 450. Add its pages to Sources, and never write
  "you asked", "Q:" or a date.
  - It extends a bullet: a bullet after that one, with its reason and one example as sub-bullets.
  - It is a new aspect of the note's concept: a new `##` before In an interview.
  - It is a concept other notes will use on their own: a child note, with the connecting
    explanation kept in the main note. A concept that already has a note gets a link, never a copy.
  - Anything else: a new subtopic, planned as a stub that builds on this note.
- **15.** An ordinary note keeps the owner's bullet style, under writing rules 1, 3 and 5. A rule or
  limit the note states has its reason in its bullet or the one below; headings are plain `##`,
  and no section is empty.
