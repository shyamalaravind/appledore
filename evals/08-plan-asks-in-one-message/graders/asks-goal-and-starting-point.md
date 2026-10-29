---
type: llm
---
The user asked to study DNS, a topic the vault has no note on. The vault has one root map,
Web development MOC, holding notes on HTTP, URLs and HTTP caching.

PASS if the reply asks what the topic is for (the goal, which sets how deep to go) and what
the user can be assumed to know already, with a recommendation or a guess for each that the
user could accept by replying "all fine".

FAIL if it asks about only one of the two, leaves either without a recommendation or a
guess, or says it will ask about them later.
