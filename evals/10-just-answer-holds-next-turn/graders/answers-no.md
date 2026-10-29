---
type: llm
---
The user asked whether a browser's cache reuses the response to a POST request, such as the
results page of a search form. The agreed source says caches store responses to GET requests
and most store nothing else; a POST response can be reused only when it carries explicit
freshness information and a `Content-Location` header, which most caches don't implement, so
in practice it is not reused.

PASS if the reply answers in line with that: in practice, no.

FAIL if it says the browser reuses the response, or contradicts the source.
