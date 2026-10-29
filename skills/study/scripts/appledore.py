#!/usr/bin/env python3
"""The Mind Palace's index. Every query reads the notes themselves, so it never drifts.

Usage: appledore.py [--vault PATH] COMMAND ...

  find QUERY [--kind K] [--body]      notes whose title, aliases or summary match QUERY
  tree [MOC] [--depth N] [--summary]  the MOC chains, from the root MOCs down
  related NOTE                        a note's chain, children, prerequisites and links
  backlinks NOTE                      every note that links to NOTE, and where
  graph TOPIC [--write]               a topic's learning graph, derived from builds_on
  next TOPIC [--left-out]             its planned subtopics: ready, waiting, and the stubs left out
  check                               the vault's invariants; exits 1 on any error
  convert [NOTE ...] [--write]        legacy inline **MOCs**: fields to YAML frontmatter
  mv NOTE NEW [--alias] [--dry-run]   rename or move a note and rewrite every link to it
  open NOTE                           open a note in Obsidian, and print its obsidian:// link

NOTE is a title, an alias or a path inside the vault. The vault defaults to
~/work-space/Solenya/Mind palace; set APPLEDORE_VAULT or pass --vault to use another.
open uses the Obsidian command line interface when it is turned on, and the
system's opener with the obsidian:// link otherwise; APPLEDORE_OPEN=0 only prints the link.
There is no stored index: each call parses the vault's Markdown. Python 3.8+,
standard library only.
"""

from __future__ import annotations

import argparse
import difflib
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path, PurePosixPath
from urllib.parse import quote

DEFAULT_VAULT = Path.home() / "work-space" / "Solenya" / "Mind palace"

# The vault layout (the vault's README.md). Hard-coded until appledore is generalised.
NOTES_DIR = "_Main Notes"
MOCS_DIR = "_-MOCs"
STUBS_DIR = "Stubs"
PROBLEMS_DIR = "DSA Problems"
NOT_NOTES_DIRS = {"__templates", "_attachments", "copilot"}
ROOT_TITLES = {"home", "readme"}

NOTE_TYPES = ("topic", "subtopic", "note")
STATUSES = {"topic": {"learning", "done"}, "problem": {"solved", "revisit"}}
DIFFICULTIES = {"easy", "medium", "hard"}
PROP_ORDER = ("summary", "type", "url", "difficulty", "status", "mocs", "builds_on", "aliases", "created")
KNOWN_PROPS = set(PROP_ORDER) | {"tags", "cssclasses"}
REQUIRED = {
    "topic": ("summary", "type", "status", "mocs", "created"),
    "subtopic": ("summary", "type", "mocs", "builds_on", "created"),
    "note": ("summary", "type", "mocs", "created"),
    "stub": ("summary", "mocs", "created"),
    "moc": ("summary", "created"),
    "problem": ("summary", "url", "difficulty", "status", "mocs", "created"),
}
MAX_PARENTS = 2
MAX_PREREQUISITES = 3
MOC_DISSOLVE_AT = 2   # a MOC with this many children or fewer is dissolved
MOC_SPLIT_AT = 30     # a hub with more children than this is split
SUBTOPIC_WORDS = (150, 450)
GRAPH_COMMENT = ("%% Derived from the subtopics' and planned stubs' builds_on and the stubs' mocs by "
                 "appledore.py graph. Regenerate; don't edit by hand. %%")

LINK = re.compile(r"(!?)\[\[([^\[\]]*?)\]\]")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
INLINE_CODE = re.compile(r"(`+)[^`\n]+?\1")
COMMENT = re.compile(r"%%.*?%%", re.S)
FM_KEY = re.compile(r"^([A-Za-z_][\w-]*):(?:[ \t]+(.*?))?[ \t]*$")
FM_ITEM = re.compile(r"^[ \t]+-(?:[ \t]+(.*?))?[ \t]*$")
LEGACY_FIELD = re.compile(r"^\*\*([A-Za-z]+)(?::\*\*|\*\*:|\*:)[ \t]*(.*?)[ \t]*$")
LEGACY_KEYS = {"date", "source", "mocs", "tags"}
LEGACY_IN_BODY = re.compile(r"^\*\*(?:MOCs|date|source|tags)\b", re.M | re.I)
HEADING = re.compile(r"^(#{1,6})[ \t]+(.*?)[ \t]*$", re.M)
URL_LINK = re.compile(r"\[([^\[\]]*)\]\([^()\s]*\)")         # [text](url)
WIKI_SHOWN = re.compile(r"!?\[\[(?:[^\[\]|]*\|)?([^\[\]|]*)\]\]")  # [[target|shown]] or [[target]]
BARE_URL = re.compile(r"https?://\S+")
SOURCES = re.compile(r"^## Sources\b.*?(?=^#{1,2}[ \t]|\Z)", re.M | re.S)
BAD_TITLE_CHARS = set('\\/:#^[]|')


def die(message: str, code: int = 2) -> None:
    print(f"appledore.py: {message}", file=sys.stderr)
    sys.exit(code)


def env(name: str):
    """APPLEDORE_<name>, or the old PALACE_<name> with a notice, until the next version drops it."""
    value = os.environ.get(f"APPLEDORE_{name}")
    if value is None and f"PALACE_{name}" in os.environ:
        print(f"appledore.py: PALACE_{name} is now APPLEDORE_{name}; the old name stops working in the next version",
              file=sys.stderr)
        value = os.environ[f"PALACE_{name}"]
    return value


# ---------------------------------------------------------------- frontmatter

def split_frontmatter(text: str):
    """Return (frontmatter text, body). The frontmatter text is None when there is none."""
    if not (text.startswith("---\n") or text.startswith("---\r\n")):
        return None, text
    lines = text.split("\n")
    for i in range(1, len(lines)):
        if lines[i].rstrip() in ("---", "..."):
            return "\n".join(lines[1:i]), "\n".join(lines[i + 1:])
    return None, text


def scalar(value: str) -> str:
    """Unquote a YAML scalar, or cut a trailing comment off a plain one."""
    if value[:1] in ("'", '"'):
        quote, out, i = value[0], [], 1
        while i < len(value):
            c = value[i]
            if quote == '"' and c == "\\" and i + 1 < len(value):
                out.append(value[i + 1])
                i += 2
                continue
            if c == quote:
                if quote == "'" and value[i + 1:i + 2] == "'":
                    out.append("'")
                    i += 2
                    continue
                return "".join(out)
            out.append(c)
            i += 1
        return value
    return re.split(r"\s+#", value, maxsplit=1)[0].strip()


def split_inline_list(inner: str) -> list:
    """Split the inside of a YAML flow list on commas outside quotes and [[links]]."""
    items, buf, quote, depth = [], [], None, 0
    for i, c in enumerate(inner):
        if quote:
            buf.append(c)
            if c == quote:
                quote = None
            continue
        if c in ("'", '"'):
            quote = c
        elif inner.startswith("[[", i):
            depth += 1
        elif inner.startswith("]]", i) and depth:
            depth -= 1
        elif c == "," and not depth:
            items.append("".join(buf).strip())
            buf = []
            continue
        buf.append(c)
    if "".join(buf).strip():
        items.append("".join(buf).strip())
    return [scalar(x) for x in items]


def parse_yaml(text: str) -> dict:
    """Parse the YAML subset Obsidian writes: scalars, flow lists and block lists."""
    data, key = {}, None
    for line in text.split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        item = FM_ITEM.match(line)
        if item and key is not None:
            if not isinstance(data[key], list):
                data[key] = []
            if item.group(1) is not None:
                data[key].append(scalar(item.group(1)))
            continue
        m = FM_KEY.match(line)
        if not m:
            continue
        key, value = m.group(1), m.group(2)
        if not value:
            data[key] = None
        elif value.startswith("[") and value.endswith("]") and not value.startswith("[["):
            data[key] = split_inline_list(value[1:-1])
        else:
            data[key] = scalar(value)
    return data


NEEDS_QUOTES = re.compile(r"""^[\s\-?:,\[\]{}#&*!|>'"%@`\d.+]|[:#]\s|:$|\s$|^(?:true|false|yes|no|null|~)$""", re.I)


def yaml_str(value) -> str:
    s = str(value)
    if DATE.match(s):
        return s
    if s == "" or NEEDS_QUOTES.search(s) or "[[" in s:
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return s


def dump_yaml(data: dict) -> str:
    out = []
    for key, value in data.items():
        if isinstance(value, list):
            if value:
                out.append(f"{key}:")
                out.extend(f"  - {yaml_str(v)}" for v in value)
            else:
                out.append(f"{key}: []")
        elif value is None:
            out.append(f"{key}:")
        else:
            out.append(f"{key}: {yaml_str(value)}")
    return "\n".join(out)


def ordered(data: dict) -> dict:
    keys = [k for k in PROP_ORDER if k in data] + [k for k in data if k not in PROP_ORDER]
    return {k: data[k] for k in keys}


def with_frontmatter(data: dict, body: str) -> str:
    body = body.lstrip("\n").rstrip() + "\n" if body.strip() else ""
    return "---\n" + dump_yaml(ordered(data)) + "\n---\n" + body


# ---------------------------------------------------------------- links

def mask(text: str) -> str:
    """Blank out code and %% comments, keeping every offset, so links inside them are ignored."""
    chars = list(text)

    def blank(start, end):
        for i in range(start, end):
            if chars[i] != "\n":
                chars[i] = " "

    pos, fence = 0, None
    for line in text.split("\n"):
        m = FENCE.match(line)
        if fence:
            blank(pos, pos + len(line))
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence):
                fence = None
        elif m:
            fence = m.group(1)
            blank(pos, pos + len(line))
        pos += len(line) + 1
    masked = "".join(chars)
    for m in INLINE_CODE.finditer(masked):
        blank(m.start(), m.end())
    masked = "".join(chars)
    for m in COMMENT.finditer(masked):
        blank(m.start(), m.end())
    return "".join(chars)


def blank_matches(pattern, text: str) -> str:
    """Blank out every match of pattern, keeping every offset."""
    return pattern.sub(lambda m: re.sub(r"[^\n]", " ", m.group()), text)


def fold(text: str) -> str:
    """Lowercase text without changing its length, so offsets in it still point into the original.
    İ is the one letter whose lowercase is longer."""
    return text.replace("İ", "I").lower()


def split_inner(inner: str):
    """[[name#heading|display]] -> (name, heading or None, display or None)."""
    target, bar, display = inner.partition("|")
    if target.endswith("\\"):            # a pipe escaped inside a table
        target = target[:-1]
    name, hash_, heading = target.partition("#")
    return name.strip(), (heading if hash_ else None), (display if bar else None)


class Link:
    __slots__ = ("name", "heading", "display", "embed", "where", "line")

    def __init__(self, inner, embed, where, line=""):
        self.name, self.heading, self.display = split_inner(inner)
        self.embed, self.where, self.line = embed, where, line

    def __str__(self):
        return ("!" if self.embed else "") + "[[" + self.name + ("#" + self.heading if self.heading is not None else "") + "]]"


# ---------------------------------------------------------------- the vault

class Note:
    def __init__(self, root: Path, path: Path):
        self.path = path
        self.rel = PurePosixPath(path.relative_to(root).as_posix())
        self.title = path.stem
        self.text = path.read_text(encoding="utf-8").lstrip("﻿")
        fm_text, self.body = split_frontmatter(self.text)
        self.has_frontmatter = fm_text is not None
        self.fm = parse_yaml(fm_text) if fm_text else {}
        self.folder = self.rel.parts[0] if len(self.rel.parts) > 1 else ""
        self.kind = self._kind()
        self._links = None

    def _kind(self) -> str:
        if self.folder == MOCS_DIR:
            return "moc"
        if self.folder == STUBS_DIR:
            return "stub"
        if self.folder == PROBLEMS_DIR:
            return "problem"
        if self.folder == NOTES_DIR:
            t = self.fm.get("type")
            return t if t in NOTE_TYPES else "note"
        if not self.folder and self.title.lower() in ROOT_TITLES:
            return "root"
        return "other"

    def values(self, key) -> list:
        v = self.fm.get(key)
        if v is None:
            return []
        return [str(x) for x in v] if isinstance(v, list) else [str(v)]

    @property
    def summary(self) -> str:
        return " ".join(self.values("summary")).strip()

    @property
    def aliases(self) -> list:
        return [a for a in self.values("aliases") if a.strip()]

    def prop_links(self, key) -> list:
        return [Link(m.group(2), bool(m.group(1)), key)
                for value in self.values(key) for m in LINK.finditer(value)]

    def body_links(self) -> list:
        if self._links is None:
            offset = len(self.text) - len(self.body)
            masked = mask(self.text)
            lines = self.text.split("\n")
            self._links = []
            for m in LINK.finditer(masked, offset):
                n = self.text.count("\n", 0, m.start()) + 1
                self._links.append(Link(self.text[m.start(2):m.end(2)], bool(m.group(1)), n, lines[n - 1].strip()))
        return self._links

    def all_links(self) -> list:
        return [link for key in self.fm for link in self.prop_links(key)] + self.body_links()

    def words(self) -> int:
        """Words in the body as a reader sees them: a link counts as its shown text, and the
        Sources section and code are left out."""
        body = re.split(r"^## Sources\b", mask(self.body), maxsplit=1, flags=re.M)[0]
        body = WIKI_SHOWN.sub(r"\1", URL_LINK.sub(r"\1", body))
        return len(re.findall(r"[^\s#*\->|`]+", body))

    def prose(self) -> str:
        """The text with all but the body's prose blanked, keeping every offset: frontmatter, code,
        comments, links, embeds, URLs, headings and the Sources section."""
        start = len(self.text) - len(self.body)
        text = re.sub(r"[^\n]", " ", self.text[:start]) + mask(self.text)[start:]
        for pattern in (SOURCES, HEADING, LINK, URL_LINK, BARE_URL):
            text = blank_matches(pattern, text)
        return text


class Vault:
    def __init__(self, root):
        self.root = Path(root).expanduser().resolve()
        if not self.root.is_dir():
            die(f"no vault at {self.root}")
        self.notes, self.files = [], {}
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
            for name in sorted(filenames):
                path = Path(dirpath) / name
                rel = path.relative_to(self.root).as_posix()
                self.files.setdefault(name.lower(), []).append(rel)
                if name.endswith(".md") and rel.split("/")[0] not in NOT_NOTES_DIRS:
                    self.notes.append(Note(self.root, path))
        self.notes.sort(key=lambda n: (len(n.rel.parts), str(n.rel).lower()))
        self.by_title, self.by_rel = {}, {}
        for n in self.notes:
            self.by_title.setdefault(n.title.lower(), []).append(n)
            self.by_rel[str(n.rel).lower()] = n
        self._resolved, self._children, self._dependants, self._backlinks = {}, None, None, None
        self._names, self._name_pattern = None, None

    # -- lookups

    def resolve(self, name: str):
        """Resolve a link target the way Obsidian does: a Note, a file's path, or None."""
        key = name.strip().lower()
        if key in self._resolved:
            return self._resolved[key]
        found = None
        if not key:
            pass
        elif "/" in key:
            found = self.by_rel.get(key) or self.by_rel.get(key + ".md")
            if found is None:
                for rel, n in self.by_rel.items():
                    if rel.endswith("/" + key) or rel.endswith("/" + key + ".md"):
                        found = n
                        break
            if found is None and (self.root / name.strip()).is_file():
                found = name.strip()
        else:
            notes = self.by_title.get(key[:-3] if key.endswith(".md") else key)
            if notes:
                found = notes[0]
            elif self.files.get(key):
                found = self.files[key][0]
        self._resolved[key] = found
        return found

    def get(self, name: str) -> Note:
        """Find a note by title, path or alias, for a command-line argument."""
        found = self.resolve(name)
        if isinstance(found, Note):
            return found
        path = Path(name).expanduser()
        if path.is_absolute():
            try:
                found = self.by_rel.get(path.resolve().relative_to(self.root).as_posix().lower())
            except ValueError:
                found = None
            if found:
                return found
        hits = [n for n in self.notes if name.strip().lower() in (a.lower() for a in n.aliases)]
        if len(hits) == 1:
            return hits[0]
        if len(hits) > 1:
            die(f"{name!r} is an alias of several notes: " + ", ".join(str(n.rel) for n in hits))
        die(f"no note named {name!r}; try: appledore.py find {name!r}")

    def note_links(self, note: Note, key: str) -> list:
        return [self.resolve(link.name) for link in note.prop_links(key)]

    def parents(self, note: Note) -> list:
        return self.note_links(note, "mocs")

    def prerequisites(self, note: Note) -> list:
        return self.note_links(note, "builds_on")

    def children(self, note: Note) -> list:
        if self._children is None:
            self._children = self._invert("mocs")
        return self._children.get(id(note), [])

    def dependants(self, note: Note) -> list:
        if self._dependants is None:
            self._dependants = self._invert("builds_on")
        return self._dependants.get(id(note), [])

    def _invert(self, key) -> dict:
        index = {}
        for n in self.notes:
            for target in self.note_links(n, key):
                if isinstance(target, Note) and n not in index.setdefault(id(target), []):
                    index[id(target)].append(n)
        return index

    def backlinks(self, note: Note) -> list:
        if self._backlinks is None:
            self._backlinks = {}
            for n in self.notes:
                for link in n.all_links():
                    target = self.resolve(link.name)
                    if isinstance(target, Note):
                        self._backlinks.setdefault(id(target), []).append((n, link))
        return self._backlinks.get(id(note), [])

    def unlinked_mentions(self, note: Note) -> list:
        """Every other note the body names by title or alias but never links, as (target, name as
        written, line) at its first mention. A hyphen joins words, so "Lock-free" doesn't name a note
        called Lock. A one-word name matches only in its own capitalisation, so the word "graph"
        doesn't name a note called Graph; a longer name matches in any case."""
        if self._names is None:
            self._names = {}  # a one-word name as written, a longer one lowercased
            for n in self.notes:
                if n.kind != "root":
                    for name in [n.title] + n.aliases:
                        key = " ".join(name.split())
                        if key:
                            self._names.setdefault(key if " " not in key else key.lower(), n)
            # Lowercased names grouped by their first letter, so the scan tries only the names that
            # can start at each word, and stays fast however many notes the vault has.
            groups = {}
            for k in sorted({fold(k) for k in self._names}, key=len, reverse=True):  # the longest name wins
                groups.setdefault(re.escape(k[0]), []).append(r"[ \t]+".join(map(re.escape, k[1:].split(" "))))
            self._name_pattern = re.compile(r"(?<![\w-])(?:" + "|".join(
                first + "(?:" + "|".join(rests) + ")" for first, rests in groups.items()) + r")(?![\w-])")
        if not self._names:
            return []
        skip = {id(note)} | {id(p) for p in self.parents(note)} | {id(self.resolve(l.name)) for l in note.body_links()}
        text, found = note.prose(), []
        for m in self._name_pattern.finditer(fold(text)):  # a one-word name's case is checked below
            written = " ".join(text[m.start():m.end()].split())
            target = self._names.get(written if " " not in written else written.lower())
            if target is not None and id(target) not in skip:
                skip.add(id(target))
                found.append((target, written, text.count("\n", 0, m.start()) + 1))
        return found

    def roots(self) -> list:
        return [n for n in self.notes if n.kind == "moc" and not n.values("mocs")]

    def chain(self, note: Note, parent: Note = None) -> list:
        """The primary chain above a note: its first parent, that parent's first, up to a root."""
        out, seen = [], {id(note)}
        current = parent if parent is not None else self._first_parent(note)
        while isinstance(current, Note) and id(current) not in seen:
            out.append(current)
            seen.add(id(current))
            current = self._first_parent(current)
        if isinstance(current, Note):
            out.append(None)  # a cycle
        return out

    def _first_parent(self, note: Note):
        parents = self.parents(note)
        return parents[0] if parents else None

    # -- the learning graph

    def learning_graph(self, topic: Note):
        """The topic's tree as (lines, warnings): each subtopic under its first prerequisite inside the topic."""
        rows, warnings = self.graph_rows(topic)
        lines = ["  " * level + f"- [[{n.title}]]" + (" · stub" if n.kind == "stub" else "") for level, n, _ in rows]
        return lines, warnings

    def graph_rows(self, topic: Note):
        """The topic's tree as (rows, warnings), rows being (level, note, left_out) in drawing order.
        Its nodes are the subtopics and the planned stubs (stubs whose mocs is the topic), each drawn
        under its first prerequisite inside the topic; a stub a subtopic left out is a leaf under it."""
        members, seen = [], {id(topic)}

        def collect(parent):
            for child in sorted(self.children(parent), key=lambda n: n.title.lower()):
                if id(child) in seen or self._first_parent(child) is not parent:
                    continue
                if child.kind == "subtopic" or (child.kind == "stub" and parent is topic):
                    seen.add(id(child))
                    members.append(child)
                    if child.kind == "subtopic":
                        collect(child)

        collect(topic)
        inside = {id(m) for m in members}
        under, warnings = {}, []
        for m in members:
            prereqs = [p for p in self.prerequisites(m) if isinstance(p, Note) and id(p) in inside]
            if prereqs:
                under[id(m)] = prereqs[0]
            else:
                parent = self._first_parent(m)
                under[id(m)] = parent if isinstance(parent, Note) and id(parent) in inside else None
        for m in members:  # break builds_on cycles by lifting a node to the top
            path, current = [], m
            while current is not None and id(current) not in [id(p) for p in path]:
                path.append(current)
                current = under[id(current)]
            if current is not None:
                warnings.append(f"builds_on cycle through [[{current.title}]]; drawn at the top level")
                under[id(current)] = None
        left_out = []
        for parent in members:
            for child in self.children(parent):
                if child.kind == "stub" and self._first_parent(child) is parent and id(child) not in inside:
                    left_out.append((child, parent))

        def depth(n, trail=()):
            prereqs = [p for p in self.prerequisites(n) if isinstance(p, Note) and id(p) in inside and p not in trail]
            return 1 + max((depth(p, trail + (n,)) for p in prereqs), default=0)

        rows = []

        def draw(parent, level):
            nodes = [m for m in members if under[id(m)] is parent]
            for m in sorted(nodes, key=lambda n: (depth(n), n.title.lower())):
                rows.append((level, m, False))
                draw(m, level + 1)
            for stub, p in sorted(left_out, key=lambda s: s[0].title.lower()):
                if p is parent:
                    rows.append((level, stub, True))

        draw(None, 0)
        return rows, warnings


# ---------------------------------------------------------------- output helpers

def label(note, with_summary=True, width=110) -> str:
    if not isinstance(note, Note):
        return f"{note} [file]" if note else "(unresolved)"
    text = f"{note.title}  [{note.kind}]"
    if with_summary and note.summary:
        s = note.summary
        text += "  " + (s if len(s) <= width else s[:width - 1] + "…")
    return text


def obsidian_uri(vault: Vault, note: Note) -> str:
    """The link that opens a note in Obsidian: the vault's folder name and the note's path
    without .md, both URL-encoded."""
    return (f"obsidian://open?vault={quote(vault.root.name, safe='')}"
            f"&file={quote(str(note.rel.with_suffix('')), safe='')}")


def section(title, items):
    if items:
        print(f"{title}:")
        for item in items:
            print(f"  - {item}")


def graph_section(text: str):
    """(start, end) of the Learning graph section's content, or None."""
    m = re.search(r"^## Learning graph[ \t]*$", text, re.M)
    if not m:
        return None
    start = m.end() + 1 if m.end() < len(text) else m.end()
    nxt = re.compile(r"^#{1,2}[ \t]", re.M).search(text, start)
    return start, (nxt.start() if nxt else len(text))


def drawn_graph(text: str) -> list:
    bounds = graph_section(text)
    if not bounds:
        return None
    content = COMMENT.sub("", text[bounds[0]:bounds[1]])
    return [line.rstrip() for line in content.split("\n") if line.strip()]


# ---------------------------------------------------------------- commands

def norm(s: str) -> str:
    return re.sub(r"[\W_]+", "", s.lower())


def cmd_find(vault: Vault, args):
    query = args.query.strip().lower()
    terms, nq = query.split(), norm(args.query)
    hits = []
    for n in vault.notes:
        if args.kind and n.kind != args.kind:
            continue
        names = [n.title.lower()] + [a.lower() for a in n.aliases]
        haystack = " ".join(names + [n.summary.lower()])
        if not terms:
            score = 1
        elif query in names or nq in (norm(x) for x in names):
            score = 100
        elif any(nq and nq in norm(x) for x in names):
            score = 60
        elif all(t in haystack for t in terms):
            score = 30
        elif args.body and all(t in n.body.lower() for t in terms):
            score = 10
        else:
            continue
        hits.append((-score, str(n.rel).lower(), n))
    if not hits:
        print("no matches")
    for _, _, n in sorted(hits, key=lambda h: h[:2]):
        print(f"{n.rel}  [{n.kind}]  {n.summary or '(no summary)'}")


def cmd_tree(vault: Vault, args):
    roots = [vault.get(args.moc)] if args.moc else vault.roots()
    shown = set()

    def walk(note, level):
        if args.depth is not None and level > args.depth:
            return
        for child in sorted(vault.children(note), key=lambda n: (n.kind != "moc", n.title.lower())):
            primary = vault._first_parent(child)
            line = "  " * level + "- " + label(child, args.summary)
            if primary is not note:
                print(line + f"  (main place: {label(primary, False)})")
                continue
            if id(child) in shown:
                print(line + "  (cycle)")
                continue
            shown.add(id(child))
            print(line)
            walk(child, level + 1)

    for root in roots:
        shown.add(id(root))
        print(label(root, args.summary))
        walk(root, 1)
    if not args.moc:
        loose = [n for n in vault.notes if id(n) not in shown and n.kind != "root"]
        section("outside every chain", [f"{label(n, False)}  {n.rel}" for n in loose])


def cmd_related(vault: Vault, args):
    n = vault.get(args.note)
    print(f"{label(n, False)}  {n.rel}")
    if n.summary:
        print(f"  {n.summary}")
    parents = vault.parents(n)
    for i, parent in enumerate(parents):
        if not isinstance(parent, Note):
            print(f"{'chain' if i == 0 else 'also under'}: (unresolved parent)")
            continue
        chain = [parent] + vault.chain(parent)
        titles = [c.title if c else "(cycle)" for c in chain]
        print(f"{'chain' if i == 0 else 'also under'}: " + " → ".join(titles))
    children = vault.children(n)
    prereqs = vault.prerequisites(n)
    dependants = vault.dependants(n)
    first = parents[0] if parents else None
    siblings = [c for c in vault.children(first) if c is not n] if isinstance(first, Note) else []
    section("children", [label(c) for c in children])
    section("builds on", [label(p) for p in prereqs])
    section("needed by", [label(d) for d in dependants])
    section("siblings", [label(s, False) for s in siblings[:MOC_SPLIT_AT]])
    known = {id(x) for x in parents + children + prereqs + dependants if isinstance(x, Note)}
    out, missing = [], []
    for link in n.body_links():
        target = vault.resolve(link.name)
        if isinstance(target, Note):
            if id(target) not in known and id(target) != id(n):
                known.add(id(target))
                out.append(label(target))
        elif target is None and str(link) not in missing:
            missing.append(str(link))
    section("links to", out)
    section("unresolved links", missing)
    incoming = []
    for src, _ in vault.backlinks(n):
        if id(src) not in known and src is not n:
            known.add(id(src))
            incoming.append(label(src))
    section("linked from", incoming)


def cmd_backlinks(vault: Vault, args):
    n = vault.get(args.note)
    hits = vault.backlinks(n)
    if not hits:
        print("no backlinks")
    for src, link in hits:
        where = link.where if isinstance(link.where, str) else f"line {link.where}: {link.line[:100]}"
        print(f"{src.rel}  {where}")


def cmd_graph(vault: Vault, args):
    topic = vault.get(args.topic)
    if topic.kind != "topic":
        die(f"{topic.title!r} is a {topic.kind}, not a topic (type: topic)")
    lines, warnings = vault.learning_graph(topic)
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    if not args.write:
        print("\n".join(lines) if lines else "(no subtopics or stubs yet)")
        return
    text = topic.text
    bounds = graph_section(text)
    block = GRAPH_COMMENT + "\n" + "".join(line + "\n" for line in lines) + "\n"
    if bounds:
        new = text[:bounds[0]] + block + text[bounds[1]:]
    else:
        m = re.search(r"^## Sources\b", text, re.M)
        at = m.start() if m else len(text)
        new = text[:at].rstrip("\n") + "\n\n## Learning graph\n" + block + text[at:]
    if new != text:
        topic.path.write_text(new, encoding="utf-8")
        print(f"updated the learning graph in {topic.rel} ({len(lines)} lines)")
    else:
        print(f"the learning graph in {topic.rel} is already current")


def print_left_out(vault: Vault, topic: Note, rows):
    """The stubs the topic's notes left out, as Markdown links grouped by the note that left
    each out, in the learning graph's order."""
    groups = {}
    for _, n, left in rows:
        if left:
            parent = vault._first_parent(n)
            groups.setdefault(id(parent), (parent, []))[1].append(n)
    groups = [groups[id(n)] for _, n, left in rows if not left and id(n) in groups]
    count = sum(len(stubs) for _, stubs in groups)
    if not count:
        print(f"{topic.title}: no stubs left out")
        return
    print(f"{topic.title}: {count} stub{'' if count == 1 else 's'} left out "
          f"by {len(groups)} note{'' if len(groups) == 1 else 's'}")
    for parent, stubs in groups:
        print(f"- Left out by [{parent.title}]({obsidian_uri(vault, parent)}):")
        for s in stubs:
            print(f"  - [{s.title}]({obsidian_uri(vault, s)})" + (f": {s.summary}" if s.summary else ""))


def cmd_next(vault: Vault, args):
    topic = vault.get(args.topic)
    if topic.kind != "topic":
        die(f"{topic.title!r} is a {topic.kind}, not a topic (type: topic)")
    rows, _ = vault.graph_rows(topic)
    if args.left_out:
        print_left_out(vault, topic, rows)
        return
    written = [n for _, n, _ in rows if n.kind == "subtopic"]
    planned = [n for _, n, left in rows if n.kind == "stub" and not left]
    left_out = [n for _, n, left in rows if left]
    ready, waiting = [], []
    for n in planned:
        prereqs = vault.prerequisites(n)
        missing = [p.title if isinstance(p, Note) else "(unresolved)" for p in prereqs
                   if not isinstance(p, Note) or p.kind == "stub"]
        if missing:
            waiting.append(f"{label(n)}  (waits for: {', '.join(missing)})")
        else:
            ready.append(f"{label(n)}  (builds on: {', '.join(p.title for p in prereqs) or 'nothing'})")
    print(f"{topic.title}: {len(written)} subtopic{'' if len(written) == 1 else 's'} written, "
          f"{len(planned)} planned, {len(left_out)} left out")
    section("ready", ready)
    section("waiting", waiting)
    section("left out", [f"{label(n)}  (left out by: {vault._first_parent(n).title})" for n in left_out])


def check(vault: Vault):
    """Return (errors, warnings), each a list of (path, message)."""
    errors, warnings = [], []

    def err(n, msg):
        errors.append((str(n.rel), msg))

    def warn(n, msg):
        warnings.append((str(n.rel), msg))

    for title, notes in vault.by_title.items():
        if len(notes) > 1:
            for n in notes:
                err(n, "another note has the same name, ignoring case: " + ", ".join(str(o.rel) for o in notes if o is not n))
    names = {}
    for n in vault.notes:
        for a in n.aliases:
            owner = vault.by_title.get(a.lower())
            if owner and owner[0] is not n:
                err(n, f"alias {a!r} is the title of {owner[0].rel}")
            if a.lower() in names and names[a.lower()] is not n:
                err(n, f"alias {a!r} is also an alias of {names[a.lower()].rel}")
            names[a.lower()] = n

    urls = {}
    for n in vault.notes:
        if not n.text.strip():
            err(n, "empty file: make it a stub (summary + mocs) or delete it")
            continue
        if LEGACY_IN_BODY.search(n.body):
            err(n, "legacy inline fields (**MOCs**: …): run appledore.py convert")
        for link in n.all_links():
            if vault.resolve(link.name) is None:
                where = link.where if isinstance(link.where, str) else f"line {link.where}"
                err(n, f"unresolved link {link} ({where})")
        if n.kind == "root":
            continue
        if n.kind == "other":
            warn(n, "outside the vault's folders (_Main Notes, _-MOCs, Stubs, DSA Problems)")
            continue
        if not n.has_frontmatter:
            err(n, "no frontmatter")
        for key in REQUIRED[n.kind]:
            if key not in n.fm or (key not in ("builds_on", "mocs") and not n.values(key)):
                err(n, f"missing {key}")
        for key in n.fm:
            if key not in KNOWN_PROPS:
                warn(n, f"unknown property {key!r}")
        if n.folder == NOTES_DIR and n.fm.get("type") not in NOTE_TYPES:
            err(n, f"type must be one of {', '.join(NOTE_TYPES)}, not {n.fm.get('type')!r}")
        if n.kind in STATUSES and n.fm.get("status") is not None and n.fm.get("status") not in STATUSES[n.kind]:
            err(n, f"status must be one of {', '.join(sorted(STATUSES[n.kind]))}")
        if n.kind == "problem":
            if n.fm.get("difficulty") is not None and n.fm.get("difficulty") not in DIFFICULTIES:
                err(n, "difficulty must be easy, medium or hard")
            url = (n.fm.get("url") or "").strip().rstrip("/").lower()
            if url:
                if url in urls:
                    err(n, f"same url as {urls[url].rel}")
                urls[url] = n
        created = n.fm.get("created")
        if created and not DATE.match(str(created)):
            warn(n, "created should be YYYY-MM-DD")

        for key in ("mocs", "builds_on", "aliases"):
            if n.fm.get(key) is not None and not isinstance(n.fm[key], list):
                err(n, f"{key} must be a list, even with one value")
        values = n.values("mocs")
        if len(n.prop_links("mocs")) < len(values):
            err(n, "every mocs value must be a link: - \"[[Parent]]\"")
        parents = vault.parents(n)
        if n.kind != "moc" and not values:
            err(n, "no mocs: every note sits under a parent")
        if len(parents) > MAX_PARENTS:
            warn(n, f"{len(parents)} parents; at most {MAX_PARENTS} (one concept parent, one context parent)")
        if n.kind in ("subtopic", "stub") and len(parents) > 1:
            warn(n, f"a {n.kind} has exactly one parent")
        if n.kind == "subtopic" and parents and isinstance(parents[0], Note) and parents[0].kind not in ("topic", "subtopic"):
            warn(n, f"a subtopic's mocs is its topic note, not the {parents[0].kind} {parents[0].title!r}")
        chain = vault.chain(n) if parents else []
        if chain[-1:] == [None]:
            err(n, "its mocs chain loops back on itself")
        elif chain and chain[-1].kind != "moc":
            warn(n, f"its chain ends at {chain[-1].title!r}, which is not a root MOC")

        prereqs = vault.prerequisites(n)
        if len(n.prop_links("builds_on")) < len(n.values("builds_on")):
            err(n, "every builds_on value must be a link")
        if len(prereqs) > MAX_PREREQUISITES:
            warn(n, f"{len(prereqs)} prerequisites; list only direct ones (at most {MAX_PREREQUISITES})")
        for p in parents:
            if isinstance(p, Note) and p in prereqs:
                warn(n, f"lists its parent {p.title!r} in builds_on")
            if isinstance(p, Note) and any(vault.resolve(l.name) is p for l in n.body_links() if not l.embed):
                warn(n, f"links its parent {p.title!r} in the body; mocs already says it")
        for target, written, line in vault.unlinked_mentions(n):
            warn(n, f'mentions "{written}" (line {line}) but never links [[{target.title}]]')

        if n.kind == "stub":
            rest = re.split(r"^## Sources\b", n.body, maxsplit=1, flags=re.M)[0]
            if rest.strip():
                warn(n, "a stub has no body (only an optional ## Sources)")
        if n.kind == "moc":
            for line in n.body.split("\n"):
                s = line.strip()
                if s and not (s.startswith("![[") and s.endswith("]]")) and not s.startswith("#") \
                        and not s.lower().startswith("start here"):
                    warn(n, "a MOC never teaches: only headings, a Start here line and embedded Bases")
                    break
            count = len(vault.children(n))
            if parents and count <= MOC_DISSOLVE_AT:
                warn(n, f"{count} children: dissolve it (point them at its parent)")
            if count > MOC_SPLIT_AT:
                warn(n, f"{count} children: split it")
        elif len(vault.children(n)) > MOC_SPLIT_AT:
            warn(n, f"{len(vault.children(n))} children: group some under a MOC beside it")

        if n.kind == "subtopic" and not (parents and isinstance(parents[0], Note) and parents[0].kind == "subtopic"):
            group, stack = [], [n]
            while stack:
                node = stack.pop()
                group.append(node)
                stack.extend(c for c in vault.children(node) if c.kind == "subtopic" and vault._first_parent(c) is node and c not in group)
            words = sum(g.words() for g in group)
            low, high = SUBTOPIC_WORDS
            if not low <= words <= high:
                warn(n, f"{words} words across {len(group)} note(s); a subtopic is {low}–{high}")
        if n.kind == "topic":
            lines, _ = vault.learning_graph(n)
            drawn = drawn_graph(n.text)
            if drawn is None:
                warn(n, "no ## Learning graph section")
            elif drawn != lines:
                warn(n, f"the learning graph is out of date: run appledore.py graph {n.title!r} --write")

    # builds_on cycles across the whole vault
    state = {}

    def visit(n, trail):
        state[id(n)] = 1
        for p in vault.prerequisites(n):
            if not isinstance(p, Note):
                continue
            if state.get(id(p)) == 1:
                loop = trail[trail.index(p):] + [p] if p in trail else [n, p]
                err(n, "builds_on cycle: " + " → ".join(x.title for x in loop))
            elif not state.get(id(p)):
                visit(p, trail + [p])
        state[id(n)] = 2

    for n in vault.notes:
        if not state.get(id(n)):
            visit(n, [n])
    return errors, warnings


def cmd_check(vault: Vault, args):
    errors, warnings = check(vault)
    for title, items in (("errors", errors), ("warnings", warnings)):
        if items:
            print(f"{title} ({len(items)}):")
            for rel, msg in items:
                print(f"  {rel}: {msg}")
    print(f"{len(vault.notes)} notes, {len(errors)} errors, {len(warnings)} warnings")
    sys.exit(1 if errors else 0)


def convert_text(text: str):
    """Move legacy inline fields (and legacy YAML keys) into frontmatter. None if nothing changes."""
    fm_text, body = split_frontmatter(text.lstrip("﻿"))
    data = parse_yaml(fm_text) if fm_text else {}
    lines, fields, i = body.split("\n"), {}, 0
    while i < len(lines):
        m = LEGACY_FIELD.match(lines[i].strip())
        if m and m.group(1).lower() in LEGACY_KEYS:
            fields[m.group(1).lower()] = m.group(2)
        elif lines[i].strip():
            break
        i += 1
    legacy_yaml = [k for k in data if k.lower() in ("references", "topics", "date", "source")]
    if not fields and not legacy_yaml:
        return None
    if fields:
        if i < len(lines) and lines[i].strip() == "---":
            i += 1
        lines = lines[i:]

    def link_values(value):
        found = []
        for v in value if isinstance(value, list) else ([value] if value else []):
            names = [split_inner(m.group(2))[0] for m in LINK.finditer(v)]
            found += [f"[[{name}]]" for name in names if name]  # drops empty [[]] links
            if v.strip() and not names:
                found.append(v.strip())
        return found

    new = dict(data)
    links, sources = [], []
    for key in ["mocs"] + [k for k in legacy_yaml if k.lower() in ("references", "topics")]:
        links += link_values(new.pop(key, None))
    links += link_values(fields.get("mocs"))
    if links or "mocs" in fields or "mocs" in data:
        new["mocs"] = list(dict.fromkeys(links))
    created = new.pop("date", None) or fields.get("date")
    if created and DATE.match(str(created).strip()):
        new.setdefault("created", str(created).strip())
    tags = re.findall(r"#([\w/-]+)", fields.get("tags", ""))
    if tags:
        new["tags"] = list(dict.fromkeys((new.get("tags") or []) + tags))
    for source in (fields.get("source"), new.pop("source", None)):
        source = scalar(source.strip()) if isinstance(source, str) and source.strip() else ""
        if source:
            sources.append(source)

    body = "\n".join(lines).strip("\n")
    if sources:
        m = re.search(r"^## Sources[ \t]*$", body, re.M)
        bullets = "".join(f"- {s}\n" for s in sources)
        body = (body[:m.end()] + "\n" + bullets.rstrip("\n") + body[m.end():]) if m else (body + "\n\n## Sources\n" + bullets).lstrip("\n")
    return with_frontmatter(new, body)


def cmd_convert(vault: Vault, args):
    notes = [vault.get(n) for n in args.notes] if args.notes else vault.notes
    changed = 0
    for n in notes:
        new = convert_text(n.text)
        if new is None or new == n.text:
            continue
        changed += 1
        if args.write:
            n.path.write_text(new, encoding="utf-8")
            print(f"converted {n.rel}")
        else:
            sys.stdout.writelines(difflib.unified_diff(
                n.text.splitlines(True), new.splitlines(True), f"a/{n.rel}", f"b/{n.rel}"))
            print()
    print(f"{changed} note(s) {'converted' if args.write else 'to convert (dry run; add --write)'}")


def rewrite_links(vault: Vault, text: str, target: Note, new_name: str):
    """Point every link to target at new_name, keeping headings and display text. Returns (text, count)."""
    out, last, count = [], 0, 0
    for m in LINK.finditer(mask(text)):
        name, heading, display = split_inner(text[m.start(2):m.end(2)])
        if vault.resolve(name) is not target:
            continue
        inner = new_name + ("#" + heading if heading is not None else "") + ("|" + display if display is not None else "")
        out += [text[last:m.start(2)], inner]
        last, count = m.end(2), count + 1
    return "".join(out) + text[last:], count


def cmd_mv(vault: Vault, args):
    note = vault.get(args.note)
    dest = args.new.strip().lstrip("/")
    if dest.endswith("/"):
        new_rel = PurePosixPath(dest) / note.rel.name
    elif "/" in dest:
        new_rel = PurePosixPath(dest if dest.endswith(".md") else dest + ".md")
    else:
        new_rel = note.rel.parent / (dest if dest.endswith(".md") else dest + ".md")
    new_title = new_rel.stem
    if BAD_TITLE_CHARS & set(new_title) or not new_title.strip():
        die(f"a title can't hold any of {' '.join(sorted(BAD_TITLE_CHARS))}; put the real form in aliases")
    clash = vault.by_title.get(new_title.lower(), [])
    if any(n is not note for n in clash):
        die(f"{new_title!r} already exists: {clash[0].rel}")
    if new_rel == note.rel:
        die("that is where it already is")

    edits = []
    for n in vault.notes:
        text, count = rewrite_links(vault, n.text, note, new_title)
        if n is note and args.alias and new_title != note.title:
            fm_text, body = split_frontmatter(text)
            data = parse_yaml(fm_text) if fm_text else {}
            aliases = [a for a in (data.get("aliases") or []) if a]
            if note.title.lower() not in (a.lower() for a in aliases):
                data["aliases"] = aliases + [note.title]
            text = with_frontmatter(data, body)
        if text != n.text:
            edits.append((n, text, count))
    links = sum(c for _, _, c in edits)
    print(f"{'would move' if args.dry_run else 'moved'} {note.rel} → {new_rel}; "
          f"{links} link(s) in {sum(1 for e in edits if e[2])} note(s)")
    for n, _, count in edits:
        if count:
            print(f"  {n.rel}: {count}")
    if args.dry_run:
        return
    for n, text, _ in edits:
        n.path.write_text(text, encoding="utf-8")
    target = vault.root / new_rel
    target.parent.mkdir(parents=True, exist_ok=True)
    os.rename(note.path, target)  # a case-only rename works on case-insensitive disks too


def try_run(command, timeout=15):
    """A command's output, or None when it can't start, fails or hangs."""
    try:
        done = subprocess.run(command, capture_output=True, encoding="utf-8", errors="replace", timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def start_opener(command, wait=5) -> bool:
    """Hand a link to the system's opener, detached from this process and its output, because an
    app the opener starts would hold captured output open. True when the opener exits 0, or is
    still running after `wait` seconds, as xdg-open is while an app it started runs."""
    try:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, start_new_session=True)
    except OSError:
        return False
    try:
        return process.wait(timeout=wait) == 0
    except subprocess.TimeoutExpired:
        return True


def open_in_obsidian(vault: Vault, note: Note) -> str:
    """Open a note in the running Obsidian app, and say how, or why it didn't."""
    if env("OPEN") == "0":
        return "not opened: APPLEDORE_OPEN=0"
    # The CLI answers even when it is turned off (Settings → General → Advanced), so a
    # version number is what says it's on, and "Opened: <path>" that the open worked.
    if shutil.which("obsidian") and re.match(r"\d", try_run(["obsidian", "version"]) or ""):
        path = unicodedata.normalize("NFC", str(note.rel))  # Obsidian keys its files by NFC paths
        out = try_run(["obsidian", f"vault={vault.root.name}", "open", f"path={path}"])
        if out and out.startswith("Opened"):
            return "opened through the Obsidian command line interface"
    uri = obsidian_uri(vault, note)
    if sys.platform.startswith("win"):
        try:
            os.startfile(uri)  # what start does, without cmd's quoting of & and %
            return "opened through the obsidian:// link"
        except OSError:
            pass
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        if opener == "xdg-open" and not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            return "not opened: no desktop (DISPLAY and WAYLAND_DISPLAY are unset)"  # xdg-open would try a text browser
        if shutil.which(opener) and start_opener([opener, uri]):
            return "opened through the obsidian:// link"
    return "not opened: neither the Obsidian command line interface nor the system's opener worked"


def cmd_open(vault: Vault, args):
    n = vault.get(args.note)
    print(obsidian_uri(vault, n))
    print(open_in_obsidian(vault, n))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="appledore.py", description=__doc__.split("\n")[0],
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--vault", default=env("VAULT") or str(DEFAULT_VAULT))
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("find", help="notes whose title, aliases or summary match")
    p.add_argument("query")
    p.add_argument("--kind", choices=["topic", "subtopic", "note", "stub", "moc", "problem", "root", "other"])
    p.add_argument("--body", action="store_true", help="also search note bodies")
    p.set_defaults(run=cmd_find)

    p = sub.add_parser("tree", help="the MOC chains, from the root MOCs down")
    p.add_argument("moc", nargs="?")
    p.add_argument("--depth", type=int)
    p.add_argument("--summary", action="store_true")
    p.set_defaults(run=cmd_tree)

    p = sub.add_parser("related", help="a note's chain, children, prerequisites and links")
    p.add_argument("note")
    p.set_defaults(run=cmd_related)

    p = sub.add_parser("backlinks", help="every note that links to NOTE")
    p.add_argument("note")
    p.set_defaults(run=cmd_backlinks)

    p = sub.add_parser("graph", help="a topic's learning graph, derived from builds_on")
    p.add_argument("topic")
    p.add_argument("--write", action="store_true", help="redraw the topic note's Learning graph section")
    p.set_defaults(run=cmd_graph)

    p = sub.add_parser("next", help="a topic's planned subtopics: ready, waiting, and the stubs left out")
    p.add_argument("topic")
    p.add_argument("--left-out", action="store_true",
                   help="only the stubs left out, as links grouped by the note that left each out")
    p.set_defaults(run=cmd_next)

    p = sub.add_parser("check", help="the vault's invariants")
    p.set_defaults(run=cmd_check)

    p = sub.add_parser("convert", help="legacy inline fields to YAML frontmatter")
    p.add_argument("notes", nargs="*")
    p.add_argument("--write", action="store_true")
    p.set_defaults(run=cmd_convert)

    p = sub.add_parser("mv", help="rename or move a note, rewriting every link to it")
    p.add_argument("note")
    p.add_argument("new", help="a new title, a path like 'Stubs/Dapr', or a folder ending in /")
    p.add_argument("--alias", action="store_true", help="keep the old title as an alias")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(run=cmd_mv)

    p = sub.add_parser("open", help="open a note in Obsidian, and print its obsidian:// link")
    p.add_argument("note")
    p.set_defaults(run=cmd_open)

    args = parser.parse_args(argv)
    args.run(Vault(args.vault), args)


if __name__ == "__main__":
    main()
