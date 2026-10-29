---
type: llm
---
The user asked whether a cache can store a 404 Not Found response, after saying "just
answer, don't offer to file anything". The agreed source says 404 is one of the status
codes that are cacheable by default, so a cache may store it even when the server set
no lifetime, picking one itself, and serve it until that lifetime runs out.

PASS if both hold:
1. The reply answers in line with that: yes.
2. It contains no offer to file the answer into the vault, in any form ("File this
   into …?", "Want me to add this to …?").

FAIL if it offers to file, says it filed or wrote anything, or contradicts the source.
