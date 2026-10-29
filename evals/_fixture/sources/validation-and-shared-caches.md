# HTTP caching field guide, part 2: validation and shared caches

<!-- A source page for appledore's evals. Its facts follow RFC 9111, HTTP Caching, and RFC 9110, HTTP Semantics. -->

## Validation

When a stored response is stale, a cache can ask the origin whether it is still good instead of downloading it again. This is **revalidation**, and it uses a conditional request.

A conditional request needs a **validator**: a value from the stored response that identifies its version.

- `ETag` is an opaque tag the origin gives one version of a resource, such as `ETag: "33a64df5"`. Any change to the resource gets a new tag.
- `Last-Modified` is the date and time the resource last changed.

The cache sends the validator back in a request header:

- `If-None-Match: "33a64df5"` asks for the resource only if its current tag differs.
- `If-Modified-Since: <date>` asks for it only if it changed after that date.

If the resource has not changed, the origin answers `304 Not Modified`, with headers and no body. The cache updates the stored response's headers from the 304, including its new freshness lifetime, and serves the body it already has. The response is fresh again, and only a few hundred bytes crossed the network. If the resource has changed, the origin answers `200 OK` with the new body, and the cache replaces its copy.

`ETag` is the better validator. `Last-Modified` has a resolution of one second, so a file changed twice within the same second looks unchanged. When a request carries both headers, the server uses `If-None-Match` and ignores `If-Modified-Since`.

A validator is strong or weak. A strong `ETag` changes whenever any byte of the response changes. A weak one, written `W/"33a64df5"`, changes only when the meaning changes, so two responses that differ only in, say, a timestamp in the footer can share it. A weak validator cannot be used for range requests, which fetch part of a response, because the bytes may differ.

## Cache-Control directives

The `Cache-Control` response header says who may store a response and how they may reuse it:

- `no-store`: no cache may store any part of the response.
- `no-cache`: a cache may store the response, but must revalidate it with the origin before every reuse. It does not mean "don't cache".
- `private`: only a private cache, such as the browser's, may store the response.
- `public`: any cache may store the response, even one that otherwise would not, such as a shared cache given a response to a request that carried an `Authorization` header.
- `max-age=N` and `s-maxage=N`: the freshness lifetime, for every cache and for shared caches only (part 1).

## Shared caches

A shared cache serves one stored response to many users. A reverse proxy sits in front of the origin; a CDN runs many edge servers, each close to a group of users, and each edge keeps its own copy.

`s-maxage` gives shared caches their own lifetime, so a CDN can keep a page for an hour while browsers keep it for a minute. The origin then sees one request an hour from each edge instead of one a minute from each user.

A shared cache must not store a response built for one user, because it would serve that page to everyone:

- A response to a request that carried an `Authorization` header is not stored by a shared cache, unless the response says `public`, `s-maxage` or `must-revalidate`.
- Mark every other personalised response `private`, such as an account page identified by a cookie, because a shared cache has no other way to tell that it is personalised.

## The Vary header

`Vary` names the request headers that a response depends on, and adds them to the cache key. `Vary: Accept-Encoding` makes a cache store the gzip-compressed and the uncompressed response apart, and serve each only to requests that ask for it.

`Vary: *` means the response depends on something other than request headers, so a cache never reuses it without revalidating.

Each value of a varied header gets its own copy, so `Vary: User-Agent`, which has thousands of values, splits the cache into thousands of copies and few requests find a stored one.
