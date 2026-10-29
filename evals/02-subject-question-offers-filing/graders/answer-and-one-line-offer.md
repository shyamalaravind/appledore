---
type: llm
---
The user asked whether a browser's cache reuses the response to a POST request. The
agreed source says caches store responses to GET requests and most store nothing else;
a POST response can be reused only when it carries explicit freshness information and
a Content-Location header, which most caches don't implement, so in practice it is not
reused.

PASS if both hold:
1. The reply answers the question in line with that: in practice, no.
2. It ends with one line that offers to file the answer into the vault, names where
   (a note such as [[HTTP cache]], with a section or as a new subtopic), and can be
   answered in a word, such as "yes / no / elsewhere".

FAIL if there is no offer, if the offer is a numbered or multi-line menu of places, if
the reply says the answer has already been filed or written, or if the answer
contradicts the source.
