---
type: regex
target: {source: file, path: "vault/Stubs/Personalised response.md"}
flags: m
---
^---\n(?=[\s\S]*^mocs:\s*\n\s+- "\[\[HTTP caching\]\]")(?=[\s\S]*^builds_on:\s*\n(?:\s+- .*\n)*?\s+- "\[\[Shared cache\]\]")
