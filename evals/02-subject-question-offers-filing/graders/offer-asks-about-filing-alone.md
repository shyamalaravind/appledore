---
type: llm
---
The user asked a question about the subject they are studying. The reply answers it, and its
last line offers to file the answer into one of the user's notes, in a form such as:
File this into [[HTTP cache]], under `## What it stores`? yes / no / elsewhere

Judge only that last line: it is the offer. Every line before it, such as why the note fits,
the note's word count or where the study session stands, is context, not part of the offer.
"yes / no / elsewhere" are the answers to that one question, not a menu.

PASS if the last line names a note to file the answer into, with a section or as a new
subtopic, and asks only whether to file it there, so the user can answer in one word.

FAIL if the last line is no offer to file, lists several places, also asks about something
else ("Should I add it, or go on to the next subtopic?"), or says the answer is already filed
or written.
