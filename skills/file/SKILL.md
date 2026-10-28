---
name: file
description: >-
  Step of the appledore study loop: answer a question the user asks about the subject they're
  learning, from the agreed sources, then offer in one line to file the answer where it belongs in
  the vault (inside one or more topic or subtopic notes, or a new subtopic when it fits none) and
  write it after their yes. Use only inside a study session that the appledore study skill
  started, whenever the user asks a question about the subject of the topic being studied. Not for
  questions about the session, the plan, the vault, appledore or the agent's own actions: answer
  those directly.
---

# File

This runs inside an appledore study session. If the `study` skill isn't loaded, load it first: it
sets up `palace` and holds the rules every step follows.

This step is only for a question about the subject of the topic being studied. Answer a question
about the session, the plan, the vault, appledore or your own last step directly, and file nothing.

An answer about the subject belongs in the vault, because an answer that stays in the chat is lost
when the session ends. There are no question notes: an answer goes inside the notes it extends, so
each note keeps everything known about its concept.

## 1. Answer

Answer in the chat, briefly, from the agreed sources, and name the page each claim comes from.
When the sources don't cover the question, say so ("The agreed sources don't cover this"), never
answer from memory, and agree a source with the user first, as the `study` skill's rule 4 says.

## 2. Look

- `palace find` on the question's concepts, because the vault may already answer it.
- `palace related` on the note the user is reading, for the notes around it.

## 3. Offer to file it

End the answer with one line the user can answer in a word, not a list:

- **It extends one or more topic or subtopic notes:** "File this into [[Note]], under `## Section`?
  yes / no / elsewhere". It becomes a passage in each note: a bullet after the bullet it
  extends, or a new `##` section. Name each note, and where.
- **It fits none of them:** "File this as a new subtopic, [[Title]], after [[Note]]? yes / no /
  elsewhere". It becomes a new subtopic in the learning graph, with `mocs` the topic and
  `builds_on` the note being read. `learn` writes it, around the question.
- **The vault already answers it:** make no offer. Give that note's link with the answer, and link
  the note from the line that raised the question, which needs no yes. If the user called the
  concept by another name, ask in one line whether to add that name to the note's `aliases`.

On "elsewhere", ask where, or list the other places as numbered items. On "no", file nothing.

**"Just answer" or "don't file":** once the user says either, with a question or on its own,
answer without the offer for the rest of the session, until they ask for it back. A "file this"
still files that one answer.

## 4. Write, on the user's yes

1. Write each passage to `writing-rules.md`'s rules for a filed passage, and add its pages to that
   note's Sources.
2. **Check the size.** If a subtopic goes past 450 words, propose moving a part out into a new
   subtopic in the learning graph: a planned stub with `mocs` the topic and `builds_on` this
   subtopic, which `learn` then writes. Never move it into a child note, because `palace check`
   counts a child note's words in its parent's group, so the group would stay over 450. Write it
   on the user's yes.
3. For a new subtopic, create its stub in `Stubs/` as `plan` does, run
   `palace graph "<topic>" --write`, and use `learn` to write it.
4. `palace check`.

Then give the links of the notes that changed, and wait for the user's next message.
