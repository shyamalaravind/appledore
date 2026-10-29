---
type: llm
---
The user asked for a deep dive on Shared cache, a stub that the subtopic HTTP cache left out
on purpose.

The learning graph already plans two stubs on nearby questions: Vary header (the request
headers a response depends on, so a cache keeps one copy per value) and Cache key (the parts of
a request a cache matches to find a stored response).

PASS if no proposed new node covers what Vary header or Cache key covers. A reply that links
either stub, has a new node build on it, or offers to move it under Shared cache reuses it,
and passes.

FAIL if a proposed new node covers what Vary header or Cache key covers, such as a node on
`Vary` at a CDN or on what a CDN's cache key holds, whether or not it is marked as not covered
by the sources.
