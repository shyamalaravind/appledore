---
summary: "The vault's conventions, for you and for any agent that writes here."
---
## The rules

1. **Folders say what kind of file something is, never what it's about.** `_Main Notes/` holds every written note, `Stubs/` the stubs (the backlog of what isn't written yet), `_-MOCs/` the MOCs and the Bases, `DSA Problems/` the problems, `_attachments/` images and PDFs, and `__templates/` the templates. The root holds only `Home` and this file.
2. **Every note in `_Main Notes/` has a `type`:** `topic` (the root of a learning graph), `subtopic` (one node of a learning graph: what you read in one sitting, as one note or a few) or `note` (everything else).
3. **`mocs` is the only record of where a note sits.** It is a list of links that points up only. Nobody writes child lists by hand: a MOC shows its children by embedding `Children.base`.
4. **`builds_on` is the only record of reading order.** It lists direct prerequisites only, never the note's own `mocs` parent. A topic's *Learning graph* section is drawn from it by `appledore graph` and never edited by hand.
5. **A subtopic's `mocs` is its topic note.** A child note that holds part of a subtopic points to that subtopic, and a stub points to the note that left it out, so a learning graph's depth never stretches the MOC chains. A stub for a subtopic that is planned but not written yet points to the topic note and carries its `builds_on`, so the graph is drawn in full before anything is written.
6. **A MOC never teaches.** It holds a `summary`, an optional "Start here" link and its embedded Bases. A definition or a table makes a hub into a note, which can still have children.
7. **MOC sizes:** create a MOC when five or more notes would sit under it, dissolve it at two or fewer children, and split it past about 30. MOC titles end in " MOC". At most two MOC levels sit above a topic, and root MOCs have no `mocs`.
8. **A note has at most two parents:** one concept parent and one context parent (a vendor or a company), the concept parent first. Subtopics and stubs have exactly one.
9. **Every note has a one-sentence `summary`** of at most 25 words that says what the note says, never "This note is about…". It is the note's summary line, a stub's one line, the index entry and the duplicate check. The body never copies it word for word; a subtopic's In short line may say the same in the problem's terms.
10. **There are no tags.** Anything that is or could be a note is a link; facets such as difficulty and status are plain property values.
11. **Titles are unique, singular, canonical names in sentence case;** product names keep their official spelling. Every other name goes in `aliases`. Search titles, aliases and summaries (⌘P, or `appledore find`) before creating anything.
12. **Sideways links go in the body, at the first mention,** and the line says what the relation is. There are no Related or See also sections.
13. **Each note ends with `## Sources`:** links to the pages it was built from. Nothing is pasted, and an AI chat is never a source.
14. **There are no empty files.** The smallest note is a stub: a `summary` plus `mocs`. Flows are written as text arrows or Mermaid; there are no handwritten drawings.
15. **An answer filed while learning goes inside one or more topic or subtopic notes.** When it fits none of them, it becomes a new subtopic. There are no question notes.
16. **DSA problems point through `mocs` to their pattern notes.** A problem's takeaway is its `summary` and its page is its `url`; the statement isn't copied.
17. **Company notes get a context parent, a `<Company> MOC`,** created with the first company note.

## Properties

R is required, O optional, and — not used.

| Property | Type | Meaning | topic | subtopic | note | stub | MOC | problem |
|---|---|---|---|---|---|---|---|---|
| `summary` | text | One sentence, at most 25 words | R | R | R | R (the definition) | R (the area) | R (the takeaway) |
| `type` | text | `topic`, `subtopic` or `note`; only in `_Main Notes/`, where the folder can't tell | R | R | R | — | — | — |
| `status` | text | Topics: `learning` or `done`. Problems: `solved` or `revisit`. | R | — | — | — | — | R |
| `url` | text | The problem's page, and its duplicate check | — | — | — | — | — | R |
| `difficulty` | text | `easy`, `medium` or `hard` | — | — | — | — | — | R |
| `mocs` | list of links | Parents, primary first | R | R (the topic) | R | R (one) | R, except roots | R (its patterns) |
| `builds_on` | list of links | Direct prerequisites only | O | R (may be empty) | O | O (planned subtopics only) | — | — |
| `aliases` | list | Other names for the concept | O | O | O | O | — | — |
| `created` | date | `YYYY-MM-DD`, filled in by the template | R | R | R | R | R | R |

Lists stay lists even with one value, and links in properties are quoted: `- "[[Azure MOC]]"`.

## Templates

*Templates: Insert template* inserts one. `Topic`, `Subtopic`, `Note`, `Stub`, `MOC` and `Problem` match the note kinds above. `Child` is Note composer's template for splitting a note: select the part, run *Note composer: Extract current selection* and name it, and the new note arrives with `mocs` pointing at the note it came from. When the part comes off a subtopic, change its `type` to `subtopic`.

- **New stub:** click the missing link (new notes land in `Stubs/`), insert the `Stub` template and write the summary.
- **Promote a stub:** move it to `_Main Notes/`, then insert the `Topic`, `Subtopic` or `Note` template.

## Invariants

`appledore check` checks these; Obsidian's own orphan and unresolved-link views cover the first two.

1. Every note except `Home`, `README` and the root MOCs has `mocs`, and every chain ends at a root MOC.
2. There are no unresolved links and no empty files, and every note has a `summary`.
3. Note names are unique, ignoring case, and no alias equals another note's title or alias.
4. A MOC under a parent has more than two children, no hub has more than about 30, and a MOC holds no prose.
5. A subtopic is 150–450 words across the notes it spans. `builds_on` targets exist and form no cycle, and each topic's drawn learning graph matches `appledore graph`.
6. Stubs live only in `Stubs/`, each with one parent and no body beyond an optional Sources section.
7. No note links its parent in its body or lists that parent in `builds_on`.
8. No two problems share a `url`.
9. Search, the graph, Bases and agents ignore `__templates/`.
