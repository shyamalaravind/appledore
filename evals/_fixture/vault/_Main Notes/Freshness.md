---
summary: "A stored response is fresh while its age is below the lifetime that max-age or Expires sets, and a fresh response is reused without asking the origin."
type: subtopic
mocs:
  - "[[HTTP caching]]"
builds_on:
  - "[[HTTP cache]]"
aliases:
  - Freshness lifetime
created: "2026-10-21"
---
**In short:** A cache needs a rule for how long a stored response stays safe to reuse without asking the origin; freshness is that rule, a lifetime the origin sets, compared with the response's age.

**Example:** `https://shop.example/logo.png` arrives at 09:00 with `Cache-Control: max-age=3600`. The browser's [[HTTP cache]] reuses it until 10:00 without sending a request.

## Lifetime
- **Freshness lifetime:** how long a response stays reusable after the origin generated it, set by the origin in a response header.
	- A cache reuses a fresh response without contacting the origin, so a hit costs no round trip.
- `Cache-Control: max-age=N` sets the lifetime to N seconds from when the origin generated the response.
	- `max-age=3600` on `logo.png` means one hour from 09:00.
- `Expires` sets an absolute date and time instead, such as `Expires: Wed, 21 Oct 2026 10:00:00 GMT`.
	- An absolute time is reliable only while the origin's clock and the cache's clock agree.
- A [[Shared cache|shared cache]], such as a CDN, reads `s-maxage` before either of them.
	- So a CDN can keep `logo.png` for a day while each browser keeps it for an hour.

## Age
- **Age:** the time since the origin generated the response, in seconds.
	- A cache compares the age with the lifetime: while the age is lower, the response is fresh.
- A cache that serves a stored response adds an `Age` header, so the next cache along the path starts counting from it instead of from zero.
	- A CDN that stored `logo.png` 600 seconds ago sends `Age: 600`, so the browser has 3,000 seconds of lifetime left, not 3,600.

## Stale responses
- **Stale:** a stored response whose age has passed its lifetime.
	- The cache keeps it instead of deleting it, because asking the origin whether it changed is cheaper than downloading it again.
- A cache must not serve a stale response, except when it can't reach the origin.
	- `must-revalidate` takes that exception away: when the origin is unreachable, the client gets `504 Gateway Timeout` instead of the old copy.
- After 10:00, the browser asks the origin about `logo.png` before it reuses the copy, as [[Validation]] explains.
	- If the logo hasn't changed, the browser keeps its copy and only the lifetime starts again.

## In an interview
- Give a long lifetime only where a stale copy is harmless, and say what serving one would cost the user.
	- Prevents the mistake of caching a price or a stock level for an hour, so customers see the old price.
- Name the layer each lifetime is for: browsers and CDNs each keep their own copy and count their own lifetime.
	- So say which header each cache reads: `s-maxage` for the CDN, `max-age` for the browser.

## Left out on purpose
- [[Heuristic freshness]]: what lifetime does a cache pick when the response sets none?
- [[Stale-while-revalidate]]: how can a cache serve a stale copy while it fetches a fresh one in the background?

## Sources
- [HTTP caching field guide, part 1: Freshness](file://@@SOURCES@@/caching-basics.md#freshness)
- [HTTP caching field guide, part 1: Stale responses](file://@@SOURCES@@/caching-basics.md#stale-responses)
