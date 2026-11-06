# Saving a source

Read this the first time a session needs a page (study rule 4). Save the page's text to a file in
your scratch folder, outside the vault, then read the part you need from that file with `grep` or
`sed`, because a page read whole can run to 50,000 characters. Save it yourself rather than
through a fetch tool that answers a prompt, because that returns an answer, not the page.

## A public page

```sh
curl -sL '<url>' | python3 -I -c "import sys,html,re; t=sys.stdin.read(); t=re.sub(r'(?s)<(script|style).*?</\1>','',t); t=html.unescape(re.sub(r'<[^>]+>','',t)); print(re.sub(r'\n\s*\n+','\n',t))" > '<file>.txt'
```

- **A file that says the page isn't found:** the address is wrong. Find the page in the
  documentation's contents.
- **One of a few hundred words, or one that stops early** (`SKILL.md`'s Gotchas): a paywall cut
  it, or a script builds the page. Read that page in the user's browser.

## A page in the user's browser

Have the page save itself, under a name nothing else has:

```js
const a = document.createElement("a");
a.href = URL.createObjectURL(new Blob([document.body.innerText], {type: "text/plain"}));
a.download = "<page>-<timestamp>.txt"; a.click();
```

Then wait for it, and move exactly that file, nothing else from Downloads, into your scratch
folder:

```sh
f="$HOME/Downloads/<page>-<timestamp>.txt"
for i in 1 2 3 4 5 6 7 8 9 10; do [ -f "$f" ] && break; sleep 1; done
mv "$f" '<scratch folder>/'
```

If the file never arrives, run JavaScript on the page that returns each `h2` and `h3` heading,
then read one section at a time.
