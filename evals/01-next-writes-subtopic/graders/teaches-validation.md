---
type: llm
focus: {source: file, path: "vault/_Main Notes/Validation.md"}
---
The file is a subtopic note named Validation, the next node of a learning graph on HTTP
caching.

PASS if it teaches how a cache revalidates a stale response: a validator (ETag or
Last-Modified), a conditional request (If-None-Match or If-Modified-Since) and the 304 Not
Modified reply.

FAIL if any of the three is missing, or if the note is a list of questions and answers.
