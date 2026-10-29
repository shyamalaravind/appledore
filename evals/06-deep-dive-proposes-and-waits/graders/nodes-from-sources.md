---
type: llm
---
The user asked for a deep dive on Shared cache, a stub that the subtopic HTTP cache left out
on purpose.

The agreed source's part on shared caches covers reverse proxies and CDN edges, `s-maxage`,
and why a shared cache must not store a response built for one user (`Authorization`,
`private`, `public`). The next section of the same page covers the `Vary` header.

PASS if each proposed new node is something those sections cover, or is marked as not covered
by the sources.

FAIL if it proposes a new node the sources don't cover without saying so.
