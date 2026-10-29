---
summary: "The web's request-response protocol: a client sends a method, a URL and headers, and the server returns a status code, headers and a body."
type: note
mocs:
  - "[[Web development MOC]]"
aliases:
  - Hypertext Transfer Protocol
created: "2026-10-18"
---
## Requests and responses
- A client, such as a browser, sends a request: a method, a [[URL]], headers and an optional body.
	- GET asks for a resource, and POST sends data for the server to act on, such as a form.
- The server answers with a response: a status code, headers and an optional body.
	- `200 OK` means success, `404 Not Found` that nothing is at that URL, and `302 Found` that the resource is elsewhere for now.

## Headers
- Headers are `Name: value` lines that carry information about the message, such as `Content-Type: image/png`.
	- Both sides add them, so a feature such as caching can be added without changing the body.

## Sources
- [An overview of HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview), MDN
