---
type: llm
focus: {source: file, path: "vault/_Main Notes/Validation.md"}
---
The file is a subtopic note named Validation, the next node of a learning graph on HTTP
caching. It builds on a note named Freshness, which taught freshness lifetime, age and
stale responses.

PASS if all of these hold:
1. It teaches how a cache revalidates a stale response: a validator (ETag or
   Last-Modified), a conditional request (If-None-Match or If-Modified-Since) and the
   304 Not Modified reply.
2. The body, leaving out the frontmatter, code and the Sources section, is roughly 150
   to 450 words.
3. Apart from the `**In short:**` and `**Example:**` labels, at most three terms are in
   bold, each as the label of the bullet that defines it.
4. `**Example:**` gives one concrete case with real names and numbers, never
   placeholders such as `<url>`.
5. `## Left out on purpose` lists 2 to 4 items, each a `[[link]]` followed by the
   question its note will answer.
6. It links [[Freshness]] (or a term Freshness taught) instead of teaching freshness
   again.

FAIL if any of these is missing, or if the note is a list of questions and answers.
