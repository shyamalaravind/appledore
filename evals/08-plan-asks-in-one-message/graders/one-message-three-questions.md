---
type: llm
---
The user asked to study DNS, a topic the vault has no note on. The vault has one root
map, Web development MOC, holding notes on HTTP, URLs and HTTP caching.

PASS if the reply, in one message, does all of these:
1. Asks about sources and proposes 2 to 5 of them, official documentation or
   standards first.
2. Asks what the topic is for (the goal, which sets how deep to go) and what the user
   can be assumed to know already.
3. Asks where the topic note should sit in the vault, recommending a parent, such as
   Web development MOC or a new map.
4. Gives a recommendation for each of the three, so the user could reply "all fine".

FAIL if it asks only one or two of these, asks them one at a time, or says it has
already created notes for the topic.
