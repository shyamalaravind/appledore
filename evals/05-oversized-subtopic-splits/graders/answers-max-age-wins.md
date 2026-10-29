---
type: llm
---
The user asked which of max-age and Expires a cache uses when a response carries both. The
agreed source says max-age wins and the cache ignores Expires.

PASS if the reply answers in line with that.

FAIL if it says Expires wins, or that the cache uses both.
