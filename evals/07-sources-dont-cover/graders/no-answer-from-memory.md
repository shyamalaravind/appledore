---
type: llm
---
The topic's agreed sources say nothing about CDN purge requests or how long a purge
takes to spread to edge servers. They do say a CDN runs many edge servers, each with
its own copy.

PASS if all of these hold:
1. The reply says plainly that the agreed sources don't cover this.
2. It doesn't answer from memory: no description of how a purge request works, of
   purge APIs, or of how long a purge takes. Restating what the sources do say, such
   as each edge keeping its own copy, is fine.
3. It proposes 1 to 3 pages that would cover it, official documentation first, for
   the user to agree, or asks the user for a source.

FAIL if it explains purges or gives propagation times anyway, even with a caveat, or
offers to file an answer.
