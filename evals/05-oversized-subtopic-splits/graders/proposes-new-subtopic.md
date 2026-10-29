---
type: llm
---
The note Freshness is a subtopic of a learning graph on HTTP caching, and before this
request it held 448 of the 450 words a subtopic may have. The user asked which of
max-age and Expires a cache uses, and asked for the answer to be filed into Freshness.
The agreed source says max-age wins and the cache ignores Expires.

PASS if all of these hold:
1. The reply answers: max-age wins, and Expires is ignored.
2. It says that Freshness is, or would be, past the 450-word limit.
3. It proposes moving a part of Freshness, or the new passage, into a new subtopic of
   the learning graph (a planned subtopic that builds on Freshness), and asks the user
   before making that change.

FAIL if it proposes trimming alone, leaves Freshness past the limit without proposing
a fix, or says it already made the new subtopic without asking.
