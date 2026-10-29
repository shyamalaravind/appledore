---
type: llm
---
Two nodes of a learning graph on HTTP caching were ready to write: Vary header, which
`appledore next` recommends because it sits higher in the graph, and Validation. The user said
"next".

PASS if the reply says it wrote Vary header and doesn't ask the user which ready node to
write. Naming Validation as also ready is fine, and so is a question about what to do after
reading the note.

FAIL if it asks which node to write, or says it wrote Validation instead.
