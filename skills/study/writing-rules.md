# Writing rules

For a learning graph's notes (topic notes, subtopics and passages filed into them) and, last, ordinary notes. The reader knows what the topic's Scope says and what the notes in `builds_on` taught, and nothing else about the topic. They want each note terse and easy to scan: the answer first, then indented bullets, and no word that doesn't teach.

## Every note

1. **State only what the agreed sources say.** Trace every number and "how it works" claim to one of the pages. Never fill in a claim none of them states, from memory or anywhere else: leave it out, and tell the user what's missing so the two of you can agree a source for it. Keep numbers exact, and quote at most two sentences. Name a source in the line only for a judgment, such as a threshold or a "typical" value, or where sources disagree; any other claim needs only its page in Sources. Link a volatile fact, such as a limit or price, to its page. Because: memory mixes up versions and products, and the reader can't tell which line is wrong.

2. **Build on what the reader knows.** A comparison with something they know may take one bullet, with where it stops holding in the same bullet or the one under it. Because: a comparison that silently breaks teaches the wrong model.

3. **Define every term where it first appears, or replace it with plain words.** Define it in words the reader already has. Keep one word for each thing, and one meaning for each word. Where the topic gives a familiar word a new meaning, say so in a few words ("not a Docker container"). Leave no jargon the note doesn't define: vendor phrases such as "unstructured data" or "scenarios" become plain words. Because: an unknown word costs the reader the rest of the line, and a word with two meanings makes them stop to work out which.

4. **Link a note at its first mention.** For a term an earlier note taught, add a reminder of a few words instead of a definition: "a [[Blob Storage resource model|container]] (a named group of blobs)". Because: a few words bring back what the reader learned days ago, without teaching it twice.

5. **Keep the "because" inside the bullet.** Give every rule, limit and default its scope ("blob names", not "names") and its reason, in the same bullet or a sub-bullet under it. Use the sources' reason. When they give none, say what follows from the rule ("so `Cat.jpg` is a second blob"), and never invent a reason. Because: a rule without its reason can't be applied to a new case, and an invented reason teaches something false.

6. **Write terse, indented bullets.**
   - Everything under a `##` heading is a bulleted list, so it sits indented under its heading. A top-level bullet holds one point. Its sub-bullets, one tab deeper, hold its detail, reason or example. Never nest deeper.
   - One fact per bullet, in about 20 words at most. A bullet may be a fragment when its subject is clear from the bullet above. Name who acts when it isn't obvious ("your server creates the SAS").
   - Keep the joining words that carry meaning: because, so, unless, instead of. Cut the rest: no line that announces the next one ("Hello Interview describes the steps."), no recap, no hedge that carries no real doubt, no idioms or emoji.
   - Put at most five bullets in a group.
   - Keep the prose terse, never the code. Code is complete, with every import, field and method body, a line comment on each step, and no placeholder such as `...` or `/* swap */`. It counts toward no word limit, rule 7's 450 included, so never shorten it to fit one.

   Because: the reader scans, the indent shows what belongs to what, and the reasons are what turn a list of facts into a model. A reader new to the topic can't fill a gap in code.

## A subtopic note

7. **Teach at most three new concepts, in 150–450 words across the subtopic's notes.** A new subtopic usually needs 200–350. Use as few as the question needs, and never pad to reach the floor. A new concept is a term the reader doesn't know and the note keeps using. Bold it once, as the label of the bullet that defines it (`- **Proxy:** a server that …`). Bold nothing else except the labels in rule 8. When the sources show a new concept in a tool or a language, the bullet that defines it, or one under it, says where it lives there: each class, method, built-in or setting (in Java, a condition variable is `wait` and `notify` on any object, or a `Condition` from `lock.newCondition()`). Cut what the note's question doesn't need, such as name lengths, quotas and account limits: leave them out, or make them a Left out item. Because: working memory holds only three or four new things at once, and an interesting detail the question doesn't need hurts learning. A concept the reader can't find in their tool is one they can't use.

8. **Open with two labelled lines: the point, then the case.**
   - `**In short:**` One or two lines that give the note's point and name the problem it solves, so the line stands on its own. Never label it "Answer": the title is a concept, so there is no question on the page for it to answer. It may say what the `summary` says, in the problem's terms, but never copies it. A subtopic that changes an earlier flow says what the change fixes.
   - `**Example:**` One concrete case in names and numbers, never placeholders like `<account>`, with each part named ("container `videos` of account `contosomedia`"). A case carried over from an earlier note gets one short reminder, not its full setup. Use this case in every later bullet that can.

   Because: the point first lets the reader see where the detail is going, and a labelled case grounds each later bullet before the reader can guess wrong.

9. **Head each part, show why before how, and keep other signals rare.**
   - After the two lines, give each part a `##` heading naming what it explains, three at most.
   - When the subtopic's concept exists to get around a constraint, the first of the three parts is `## Why it exists`: the constraints in order, each with its because, ending with the concept as the way out.
   - Trace a mechanism with two or more actors, such as threads or services, in numbered steps on the Example's case, nested under the bullet it shows: each step a text arrow of who holds or does what (`2. Worker: wait() lets go of the lock → sleeps`).
   - Draw any other flow of three or more steps as a text arrow or Mermaid of at most six nodes, in the note's own words, nested under the bullet it shows.
   - Use at most one callout: a `> [!warning]` titled with the correction, after its section's bullets, for a trap. A trap is a wrong belief the reader probably holds that would cause a real mistake.

   Because: headings help a reader new to a topic find and remember its parts. A concept that gets around a constraint makes sense only once the reader has seen the simpler ways fail, and a mechanism with several actors only once each step says who holds what. A callout or diagram works only while it is rare, and a cold reader sees only text.

10. **Close the body with `## In an interview`:** 1–3 bullets on what you'd say or decide, and the mistake it prevents. For a Scope whose goal isn't interviews, name the heading after that goal's use instead. Never recap. Because: this is the part the reader returns to before using the topic, and a heading makes it one click away in the outline.

11. **List 2–4 topics under Left out on purpose.** Each is a link and, in plain words, the question its note will answer. Because: the reader picks deep dives from this list, and the question says what they would learn.

## The topic note's Overview

12. **Frame the topic in at most 100 words:** one line on the problem it solves, in the reader's terms, then 2–4 bullets on the one model the subtopics build on, linked. Don't list the subtopics or restate the `summary`. Because: the reader comes back to the Overview for the frame, and the Learning graph already holds the list.

## A filed passage

13. **Repair before you add.** If the question shows that the note failed to define a term or give a reason, fix that bullet where it stands. Because: the next reader would trip at the same place.

14. **Put a new passage where it will be found, written as part of the note.** A passage that extends a section becomes a bullet in it, after the bullet it extends: the answer, with its reason and one example as sub-bullets. Keep it to about 60 words and at most one new concept. A new aspect gets its own `##` section, before In an interview. Add its pages to Sources, and never write "you asked", "Q:" or a date. Because: the note must still read as one explanation, and an answer that needs more is a new subtopic.

## An ordinary note (`type: note`)

15. **Keep the owner's bullet style, under rules 1, 3 and 5.** Give each rule's reason in its bullet or the one below, use plain `##` headings, and leave no section empty. Because: these are the owner's lookup notes, and those three rules keep them usable a year later.
