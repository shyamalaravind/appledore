---
type: regex
target: {source: file, path: "vault/_Main Notes/Validation.md"}
flags: m
---
^---\n(?=[\s\S]*^type: subtopic$)(?=[\s\S]*^mocs:\s*(?:\n\s+- |\[)"\[\[HTTP caching\]\]")(?=[\s\S]*^builds_on:\s*(?:\n\s+- |\[)"\[\[Freshness\]\]")
