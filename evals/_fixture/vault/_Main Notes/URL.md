---
summary: "A URL names a resource on the web: a scheme, a host, a path and an optional query, as in https://shop.example/logo.png?v=2."
type: note
mocs:
  - "[[Web development MOC]]"
aliases:
  - Uniform Resource Locator
created: "2026-10-18"
---
## Parts
- `https` is the scheme: the protocol the client uses to fetch the resource.
- `shop.example` is the host: the server that holds the resource.
- `/logo.png` is the path, and `?v=2` the query, which the server may read to pick a version.
	- Two URLs that differ only in the query are still different URLs, so they name different resources.

## Sources
- [What is a URL?](https://developer.mozilla.org/en-US/docs/Learn_web_development/Howto/Web_mechanics/What_is_a_URL), MDN
