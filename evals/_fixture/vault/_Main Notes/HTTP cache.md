---
summary: "A store of HTTP responses that answers repeat requests without the origin server; a private cache serves one user, a shared cache many."
type: subtopic
mocs:
  - "[[HTTP caching]]"
builds_on:
  - "[[HTTP]]"
aliases: []
created: "2026-10-20"
---
**In short:** Asking the origin server for the same response again costs a round trip and server work; a cache keeps a copy of the response and answers the repeat request itself.

**Example:** A browser fetches `https://shop.example/logo.png` from the origin `shop.example`, stores the response, and shows the logo on the next page without sending a request.

## What it stores
- **HTTP cache:** a store of [[HTTP]] responses, each kept under the request that fetched it, for reuse by a later request.
	- A reuse saves the round trip, and spares the origin the work of building the response again.
- A cache finds a stored response by the request's method and [[URL]].
	- So `logo.png` and `logo.png?v=2` are two separate entries, and a changed URL always misses.

## Private and shared
- **Private cache:** one user's cache, such as the browser's.
	- Nobody else reads it, so it may keep pages built for that user, such as an account page.
- **Shared cache:** a proxy or content delivery network (CDN) between many users and the origin.
	- It stores a response once and serves it to everyone who asks for it.
	- So it must not store a page built for one user, or it would show that page to all of them.

## In an interview
- Name the caches on the path, browser, CDN and reverse proxy, before choosing headers, because each one keeps its own copy.
	- Prevents the mistake of tuning the browser's cache while the CDN serves an old copy.

## Left out on purpose
- [[Shared cache]]: how does a proxy or CDN decide which responses it may store for everyone?
- [[Cache key]]: which parts of a request, beyond the method and URL, does a cache match on?

## Sources
- [HTTP caching field guide, part 1: What an HTTP cache is](file://@@SOURCES@@/caching-basics.md#what-an-http-cache-is)
