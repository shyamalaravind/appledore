---
type: llm
---
Shared cache is a stub that the subtopic HTTP cache left out on purpose. The agreed
source's part on shared caches covers reverse proxies and CDN edges, `s-maxage`, why a
shared cache must not store a response built for one user (`Authorization`,
`private`, `public`), and the `Vary` header.

PASS if all of these hold:
1. The reply proposes 1 to 4 new nodes to go under Shared cache.
2. Each node has a title, a one-line summary and what it builds on (Shared cache, or
   another proposed node or an existing note).
3. Each node is something the source's part on shared caches covers, or is marked as
   not covered by the sources.
4. It asks the user to agree, change or cut the nodes before anything is written.

FAIL if it proposes more than 4 nodes, writes the subtopics' teaching text instead of
a plan, or says it has already created stubs or changed Shared cache.
