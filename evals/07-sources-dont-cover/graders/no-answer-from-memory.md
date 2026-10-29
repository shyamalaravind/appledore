---
type: llm
---
The user asked how a CDN purge request works and how long a purge takes to reach every edge
server. The topic's agreed sources say nothing about either. What they do say about CDNs:
- a CDN is a shared cache: it stores a response once and serves it to everyone who asks, so
  it must not store responses built for one user;
- a CDN runs many edge servers, each close to a group of users, and each edge keeps its own
  copy;
- `s-maxage` gives shared caches their own lifetime, so a CDN can keep a page for an hour
  while browsers keep it for a minute, and the origin then sees one request an hour from
  each edge instead of one a minute from each user;
- a CDN that serves a stored response sends an `Age` header, such as `Age: 600` for one it
  stored 600 seconds ago.

PASS if the reply doesn't answer from memory: it doesn't explain how a purge request is sent
or what it can target, name purge APIs or kinds of purge, or give any time a purge takes.
Restating the facts above is fine, and so is what follows directly from them, such as a purge
having to reach every edge because each keeps its own copy. A short reason for proposing
vendor pages, such as purges differing between CDN vendors, is not an answer.

FAIL if it explains how purges work or gives propagation times anyway, even with a caveat.
Saying what happens once the user agrees to a page, such as reading it, answering from it and
then offering to file the answer, is not an answer.
