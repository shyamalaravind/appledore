---
summary: "HTTP caches reuse stored responses to skip round trips: freshness says how long a copy is reusable, and validation checks a stale copy with the origin."
type: topic
status: learning
mocs:
  - "[[Web development MOC]]"
builds_on: []
aliases: []
created: "2026-10-20"
---
## Overview
Every repeat request for an unchanged response costs a round trip and work on the origin server; caching avoids both.
- An [[HTTP cache]] stores responses, in the browser or in a shared proxy or CDN.
- [[Freshness]] says how long a stored copy may be reused without asking the origin.
- Once a copy is stale, [[Validation]] lets the origin confirm it in a short reply instead of sending it again.

## Scope
- **Goal:** system design interviews: choose the caching headers for a web app, and say what each cache on the path will do with them.
- **Starting from:** knows [[HTTP]] requests, responses, headers and status codes; every caching term is defined from scratch.
- **In:** private and shared caches, freshness, validation, Cache-Control directives, Vary, cache busting.
- **Out:** service workers, browser storage APIs, and HTTP/2 and HTTP/3 transport details.

## Learning graph
%% Derived from the subtopics' and planned stubs' builds_on and the stubs' mocs by appledore.py graph. Regenerate; don't edit by hand. %%

## Sources
- [HTTP caching field guide, part 1: caches and freshness](file://@@SOURCES@@/caching-basics.md)
- [HTTP caching field guide, part 2: validation and shared caches](file://@@SOURCES@@/validation-and-shared-caches.md)
