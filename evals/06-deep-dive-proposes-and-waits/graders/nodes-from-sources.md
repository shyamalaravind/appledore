---
type: llm
---
The user asked for a deep dive on Shared cache, a stub that the subtopic HTTP cache left out
on purpose.

The agreed source's part on shared caches covers reverse proxies and CDN edges, `s-maxage`,
why a shared cache must not store a response built for one user (`Authorization`,
`private`, `public`), and the `Vary` header.

PASS if each proposed node is something that part covers, or is marked as not covered by the
sources.

FAIL if it proposes a node the sources don't cover without saying so.
