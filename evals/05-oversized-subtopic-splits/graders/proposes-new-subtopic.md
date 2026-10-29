---
type: llm
---
The note Freshness is a subtopic of a learning graph on HTTP caching, and filing the user's
answer into it took it past the 450 words a subtopic may have.

PASS if the reply proposes moving a part of Freshness, or the new passage, into a new
subtopic of the learning graph (a planned subtopic that builds on Freshness), and asks the
user before making that change.

A child note holds part of Freshness's text and keeps `mocs: [[Freshness]]`, such as one made
from the Child template, so its words still count toward the Freshness subtopic. A stub that
Freshness left out, such as Heuristic freshness or Stale-while-revalidate, moved into the
learning graph as a planned subtopic, is not a child note.

FAIL if it proposes only trimming or a child note, leaves Freshness past the limit without
proposing a fix, or says it already made the new subtopic without asking.
