# HTTP caching field guide, part 1: caches and freshness

## What an HTTP cache is

An HTTP cache stores responses so that a later request can be answered without asking the origin server again. A response served from a cache saves a round trip, and it spares the origin the work of building the response again.

There are two kinds of cache:

- A **private cache** belongs to one user. The browser's cache is the common case. Because nobody else reads it, it may store responses built for that user, such as an account page.
- A **shared cache** sits between many users and the origin: a proxy, a reverse proxy in front of the origin, or a content delivery network (CDN). It stores a response once and serves it to everyone who asks, so it must not store responses built for one user. Part 2 covers its rules.

Caches store responses to GET requests, and most caches store nothing else. A response to a POST request can be reused only in a rare case: when it carries explicit freshness information and a `Content-Location` header that names the URL it can be reused for. Most caches don't implement that case, so in practice a POST response, such as the result page of a search form, is not reused.

A cache looks up a stored response by its cache key: by default the request method and the target URL. So `/logo.png` and `/logo.png?v=2` are two different entries. Part 2 explains how the `Vary` header adds request headers to the key.

Some status codes are cacheable by default, which means a cache may store such a response even when the server set no lifetime, and pick one itself (see Heuristic freshness below): 200, 203, 204, 206, 300, 301, 308, 404, 405, 410, 414 and 501. A 404 Not Found is therefore cacheable by default, and a cache may serve a stored 404 until its lifetime runs out. Any other status code, such as 302 Found, is stored only when the response gives explicit freshness information, for example `Cache-Control: max-age=60`.

## Freshness

A stored response is **fresh** while its age is less than its freshness lifetime. A cache serves a fresh response without contacting the origin.

The origin sets the freshness lifetime explicitly in one of two ways:

- `Cache-Control: max-age=N` sets it to N seconds from the moment the origin generated the response.
- `Expires` sets an absolute date and time, such as `Expires: Wed, 21 Oct 2026 07:28:00 GMT`. An absolute time is reliable only when the origin's clock and the cache's clock agree.

When a response carries both, `max-age` wins and the cache ignores `Expires`. Because `max-age` is a number of seconds counted from when the response was generated, it does not depend on the clocks agreeing.

A shared cache reads `s-maxage` first: it overrides both `max-age` and `Expires` for shared caches only, so a CDN can keep a page for an hour while browsers keep it for a minute.

The **age** of a response is the time since the origin generated it, in seconds. A cache that serves a stored response adds an `Age` header with that number, so the next cache along the path starts counting from it instead of from zero. A CDN that stored a response 600 seconds ago sends `Age: 600`; a browser that receives it with `max-age=3600` has 3,000 seconds of freshness left.

### Heuristic freshness

When a response that is cacheable by default carries neither `max-age` nor `Expires`, a cache may choose a lifetime itself. A typical choice is 10% of the time since the `Last-Modified` date: a file last modified 10 days ago is treated as fresh for 1 day. This is why a server that sends no caching headers can still see its pages reused.

## Stale responses

Once a response's age passes its freshness lifetime, the response is **stale**. A cache does not delete a stale response: it can revalidate it with the origin (part 2), which is cheaper than downloading the whole response again when nothing has changed.

A cache must not serve a stale response, except when it cannot reach the origin. Two directives change that:

- `must-revalidate` removes the exception: once the response is stale, the cache must revalidate it, and if the origin cannot be reached it returns `504 Gateway Timeout` instead of the stale copy.
- `stale-while-revalidate=N` lets a cache serve a stale response for up to N seconds while it revalidates it in the background, so the user doesn't wait for the origin.

## Cache busting

A file that never changes at its URL can be cached for a long time. Put a hash of the file's content in its name, such as `app.3f9a1c.js`, and serve it with `Cache-Control: max-age=31536000, immutable` (one year). A new version of the file gets a new name, so the page that references it picks up the new version at once.

The HTML page that references those files gets a short lifetime or `no-cache` instead, so browsers see the new file names soon after a release.

`immutable` tells the cache that the response will not change while it is fresh, so the browser does not revalidate it when the user reloads the page.
