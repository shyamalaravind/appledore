---
name: file
description: >-
  Step of the appledore study loop: answer a question the user asks about the subject they're
  learning, from the agreed sources, then offer in one line to file the answer where it belongs in
  the vault (inside one or more topic or subtopic notes, or a new subtopic when it fits none) and
  write it after their yes. Use only inside a study session that the appledore study skill
  started, whenever the user asks such a question. Not for questions about the session, the plan,
  the vault, appledore or the agent's own actions: answer those directly.
---

# File

This runs inside an appledore study session. If the `study` skill isn't loaded, load it first: it
sets up `palace` and holds the rules every step follows.

This step is only for a question about the topic's subject: answer any other question directly,
and file nothing.

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

If the vault already answers the question, make no offer: give that note's link with the answer,
and link the note from the line that raised the question. If the user called the concept by
another name, ask in one line whether to add that name to the note's `aliases`.

Otherwise, end the answer with one line the user can answer in a word, even when it names several
notes, because a list to work through after every answer slows the loop:

- **It extends one or more topic or subtopic notes:** "File this into [[Note]], under `## Section`?
  yes / no / elsewhere", naming each note and its section, existing or new.
- **It fits none of them:** "File this as a new subtopic, [[Title]], after [[Note]]? yes / no /
  elsewhere". It becomes a new subtopic in the learning graph, with `mocs` the topic and
  `builds_on` the note being read. `learn` writes it, around the question.

On "elsewhere", ask where, or list the other places as numbered items. On "no", file nothing.

**"Just answer" or "don't file":** once the user says either, answer without the offer for the
rest of the session, until they ask for it back. A "file this" still files that one answer.

## 4. Write, on the user's yes

1. Write each passage to `writing-rules.md`'s rules for a filed passage, and add its pages to that
   note's Sources.
2. **Check the size.** If a subtopic goes past 450 words, propose moving a part into a new
   planned subtopic that builds on it, never into a child note, whose words still count toward
   the 450. Write it on the user's yes.
3. For a new subtopic, create its stub in `Stubs/` as `plan` does, run
   `palace graph "<topic>" --write`, and use `learn` to write it.
4. `palace check`.

Then give the links of the notes that changed, and wait for the user's next message.
