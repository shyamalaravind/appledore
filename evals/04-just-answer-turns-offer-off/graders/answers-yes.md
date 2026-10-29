---
type: llm
---
The user asked whether a cache can store a 404 Not Found response. The agreed source says 404
is one of the status codes that are cacheable by default, so a cache may store it even when
the server set no lifetime, picking one itself, and serve it until that lifetime runs out.

PASS if the reply answers in line with that: yes.

FAIL if it says no, or contradicts the source.
