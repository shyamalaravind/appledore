---
name: file
description: >-
  Step of the appledore study loop: answer a question the user asks while reading, from the agreed
  sources, then propose where the answer belongs in the vault (inside one or more topic or
  subtopic notes, or a new subtopic when it fits none) and write it after their yes. Use only
  inside a study session that the appledore study skill started, whenever the user asks a
  question about what they're learning.
---

# File

This runs inside an appledore study session. If the `study` skill isn't loaded, load it first: it
sets up `palace` and holds the rules every step follows.

Every answer ends up in the vault, because an answer that stays in the chat is lost when the
session ends. There are no question notes: an answer goes inside the notes it extends, so each
note keeps everything known about its concept.

## 1. Answer

Answer in the chat, briefly, from the agreed sources, and name the page each claim comes from.
When the sources don't cover the question, say so ("The agreed sources don't cover this"), never
answer from memory, and agree a source with the user first, as the `study` skill's rule 4 says.

## 2. Look

- `palace find` on the question's concepts, because the vault may already answer it.
- `palace related` on the note the user is reading, for the notes around it.

## 3. Propose where it goes

Give a numbered list the user can answer per item:

- **Already in the vault:** link the note that answers it from the line that raised the
  question, and add the user's wording to that note's `aliases` if they called the concept by
  another name.
- **It extends one or more topic or subtopic notes:** a passage in each: a bullet after the bullet
  it extends, or a new `##` section. Say which note, and where.
- **It fits none of them:** a new subtopic in the learning graph, with `mocs` the topic and
  `builds_on` the note being read. `learn` writes it, around the question.

## 4. Write, on the user's yes

1. Write each passage to `writing-rules.md`'s rules for a filed passage, and add its pages to that
   note's Sources.
2. **Check the size.** If a subtopic goes past 450 words, propose a split: a part that becomes a
   child note (`type: subtopic`, `mocs` this subtopic), or a new subtopic of its own. Write it on
   the user's yes.
3. For a new subtopic, create its stub in `Stubs/` as `plan` does, run
   `palace graph "<topic>" --write`, and use `learn` to write it.
4. `palace check`.

Then open the note to read first with `palace open`, unless `learn` already opened one in step 4,
give the links of the notes that changed, and wait for the user's next message.
