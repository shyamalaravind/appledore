# File

This step is only for a question about the topic's subject: answer any other question directly,
and file nothing.

An answer about the subject belongs in the vault, because an answer that stays in the chat is lost
when the session ends. There are no question notes: an answer goes inside the notes it extends, so
each note keeps everything known about its concept.

## 1. Answer

Answer in the chat, briefly, from the agreed sources, and name the page each claim comes from.
When they don't cover the question, answer nothing from memory: study rule 4 says what to do.

## 2. Look

- `appledore find` on the question's concepts, because the vault may already answer it.
- `appledore related` on the note the user is reading, for the notes around it.

## 3. Offer to file it

If the vault already answers the question, make no offer: give that note's link with the answer,
and link the note from the line that raised the question. If the user called the concept by
another name, ask in one line whether to add that name to the note's `aliases`.

Otherwise, pick the place as `writing-rules.md` rule 14 says, and end the answer with one line the
user can answer in a word, even when it names several places, because a list to work through
after every answer slows the loop: "File this into [[Note]], under `## Section`? yes / no /
elsewhere". Name each place: a note and its section, a child note, or a new subtopic after the
note being read.

On "elsewhere", ask where, or list the other places as numbered items. On "no", file nothing.

**"Just answer" or "don't file":** once the user says either, answer without the offer for the
rest of the session, until they ask for it back. A "file this" still files that one answer.

## 4. Write, on the user's yes

1. Write each passage to `writing-rules.md` rules 13 and 14.
2. **Check the size.** If a subtopic goes past 450 words, propose the fix `writing-rules.md`
   rule 7 gives, and make it on the user's yes.
3. For a new subtopic, create its stub in `Stubs/` as `plan` step 4 does, run
   `appledore graph "<topic>" --write`, and use `learn` to write it, around the question.
4. `appledore check`.

Then open the note to read first with `appledore open`, unless `learn` already opened one in
step 4, give the links of the notes that changed, and wait for the user's next message.
