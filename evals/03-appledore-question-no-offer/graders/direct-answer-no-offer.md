---
type: llm
---
The user asked how appledore handles the answers to their questions. The right answer:
there are no question notes; an answer about the subject goes inside the topic or
subtopic notes it extends, or becomes a new subtopic when it fits none, and only after
the user says yes.

PASS if both hold:
1. The reply answers in line with that.
2. It makes no offer to file this reply itself into the vault (no line such as
   "File this into [[Note]]?"), because the question is about appledore, not about
   HTTP caching.

Describing how filing works is not an offer. FAIL if the reply offers to file itself,
says it has written or changed a note, or treats the question as one the topic's
sources must answer.
