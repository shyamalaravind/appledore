#!/usr/bin/env python3
"""The Mind Palace's index. Every query reads the notes themselves, so it never drifts.

Usage: appledore.py [--vault PATH] COMMAND ...

  find QUERY [--kind K] [--body]      notes whose title, aliases or summary match QUERY
  tree [MOC] [--depth N] [--summary] [--mocs]
                                      the MOC chains, from the root MOCs down; --mocs keeps
                                      only the MOCs, the topics and the notes directly under a MOC
  related NOTE                        a note's chain, children, prerequisites and links
  backlinks NOTE                      every note that links to NOTE, and where
  graph TOPIC [--write]               a topic's learning graph, derived from builds_on
  next TOPIC [--left-out]             its planned subtopics: recommended, ready, waiting, left out
  check                               the vault's invariants; exits 1 on any error. Reads only
  convert [NOTE ...] [--write]        legacy inline **MOCs**: fields to YAML frontmatter
  mv NOTE NEW [--alias]               rename or move a note and rewrite every link to it
  new KIND TITLE [key=value ...]      create a note from its template in __templates/; KIND is a
                                      topic, subtopic, note, stub, moc, problem or child (a part
                                      split off NOTE in mocs=NOTE); refuses a name already taken
  promote NOTE KIND [key=value ...]   make a stub or a note a topic, subtopic or note: a stub moves
                                      to _Main Notes/, and one with no text gets the template's parts
  set NOTE key=value ...              set properties; key+=value adds to a list, key-=value takes out
  merge NOTE INTO [--force]           fold NOTE into INTO, point every link at INTO, delete NOTE
  open NOTE                           open a note in Obsidian, and print its obsidian:// link
  review [NOTE ...]                   the wrap-up review of the notes changed since the vault's last
                                      commit, or of the notes named
  commit -F - | MESSAGE               commit the vault, case-only renames included, and push it once;
                                      refuses mid-merge, on a detached HEAD or with check errors;
                                      -F - reads the message from standard input
  brief SUBTOPIC                      the cold reader's brief: cold-read.md, the reader and the
                                      subtopic's notes, numbered

key=value sets a property: a link property (mocs, builds_on) takes a note's title, alias or path,
and repeating a key in one call lists several values. An empty value empties a list and removes
anything else. new also takes source=TEXT, a bullet under ## Sources. A - reads more key=value
lines from standard input, where the shell expands nothing in a quoted heredoc (<<'EOF').

The write commands (mv, new, promote, set and merge) take --dry-run, which prints the diff and
writes nothing; graph and convert only read unless given --write. A write command refuses, writing
nothing, when its result would add a check error, and it redraws the learning graph of each topic
whose graph holds a note it changed.

NOTE is a title, an alias or a path inside the vault. The vault defaults to
~/work-space/Solenya/Mind palace; set APPLEDORE_VAULT or pass --vault to use another.
open uses the Obsidian command line interface when it is turned on, and the
system's opener with the obsidian:// link otherwise; APPLEDORE_OPEN=0 only prints the link.
There is no stored index: each call parses the vault's Markdown. Python 3.8+,
standard library only.
"""

from __future__ import annotations

import argparse
import collections
import datetime
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
TEMPLATES_DIR = "__templates"
NOT_NOTES_DIRS = {TEMPLATES_DIR, "_attachments", "copilot"}
ROOT_TITLES = {"home", "readme"}

# Each kind of note: its folder, the template in TEMPLATES_DIR that `new` makes it from, the
# properties it must have and the statuses it may have.
Kind = collections.namedtuple("Kind", "folder template required statuses")
KINDS = {
    "topic": Kind(NOTES_DIR, "Topic", ("summary", "type", "status", "mocs", "created"), {"learning", "done"}),
    "subtopic": Kind(NOTES_DIR, "Subtopic", ("summary", "type", "mocs", "builds_on", "created"), set()),
    "note": Kind(NOTES_DIR, "Note", ("summary", "type", "mocs", "created"), set()),
    "stub": Kind(STUBS_DIR, "Stub", ("summary", "mocs", "created"), set()),
    "moc": Kind(MOCS_DIR, "MOC", ("summary", "created"), set()),
    "problem": Kind(PROBLEMS_DIR, "Problem", ("summary", "url", "difficulty", "status", "mocs", "created"),
                    {"solved", "revisit"}),
}
CHILD_TEMPLATE = "Child"  # Note composer's template for a part split off a note

NOTE_TYPES = ("topic", "subtopic", "note")
STATUSES = {kind: k.statuses for kind, k in KINDS.items() if k.statuses}
DIFFICULTIES = {"easy", "medium", "hard"}
PROP_ORDER = ("summary", "type", "url", "difficulty", "status", "mocs", "builds_on", "aliases", "created")
KNOWN_PROPS = set(PROP_ORDER) | {"tags", "cssclasses"}
REQUIRED = {kind: k.required for kind, k in KINDS.items()}
MAX_PARENTS = 2
MAX_PREREQUISITES = 3
MOC_DISSOLVE_AT = 2   # a MOC with this many children or fewer is dissolved
MOC_SPLIT_AT = 30     # a hub with more children than this is split
SUMMARY_WORDS = 25
MAX_CONCEPTS = 3      # bold concept labels in a subtopic (writing rule 7)
LEFT_OUT = (2, 4)     # topics under a subtopic's Left out on purpose (writing rule 11)
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
SHAPE_PARTS = (("**In short:**", re.compile(r"^\*\*In short(?::\*\*|\*\*:)", re.M)),  # writing rules 8, 10, 11
               ("**Example:**", re.compile(r"^\*\*Example(?::\*\*|\*\*:)", re.M)),
               ("## In an interview", re.compile(r"^## In an interview\b", re.M)),
               ("## Left out on purpose", re.compile(r"^## Left out\b", re.M)))
LEFT_OUT_LIST = re.compile(r"^## Left out\b.*?$(.*?)(?=^#{1,2}[ \t]|\Z)", re.M | re.S)
BOLD = re.compile(r"\*\*([^*\n]+?)\*\*")
GOAL = re.compile(r"^[ \t]*[-*][ \t]+\*\*Goal(?::\*\*|\*\*:)(.*)$", re.M)  # a topic's Scope line


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
    def __init__(self, root: Path, path: Path, text: str = None):
        self.path = path
        self.rel = PurePosixPath(path.relative_to(root).as_posix())
        self.title = path.stem
        self.text = (path.read_text(encoding="utf-8") if text is None else text).lstrip("﻿")
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
    def __init__(self, root, planned=None):
        """planned maps a path inside the vault to the text a write command will give it, or to None
        for a file it removes, so the vault can be checked as the command would leave it."""
        self.root = Path(root).expanduser().resolve()
        if not self.root.is_dir():
            die(f"no vault at {self.root}")
        self.notes, self.files = [], {}
        planned = dict(planned or {})

        def add(rel, text=None):
            path = self.root / rel
            self.files.setdefault(path.name.lower(), []).append(rel)
            if rel.endswith(".md") and rel.split("/")[0] not in NOT_NOTES_DIRS:
                self.notes.append(Note(self.root, path, text))

        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
            for name in sorted(filenames):
                rel = (Path(dirpath) / name).relative_to(self.root).as_posix()
                if rel not in planned:
                    add(rel)
                elif planned[rel] is not None:
                    add(rel, planned.pop(rel))
        for rel, text in planned.items():
            if text is not None:
                add(rel, text)
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
        lines = ["  " * level + f"- [[{n.title}]]" + (" · left out" if left else " · stub" if n.kind == "stub" else "")
                 for level, n, left in rows]
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

    # -- what tree, check, review and brief share

    def outside_chains(self) -> list:
        """The notes whose first parents never reach a root MOC, so no chain lists them."""
        out = []
        for n in self.notes:
            top = ([n] + self.chain(n))[-1]
            if n.kind != "root" and not (isinstance(top, Note) and top.kind == "moc" and not top.values("mocs")):
                out.append(n)
        return out

    def main_subtopic(self, note: Note) -> Note:
        """The subtopic whose words a note counts toward: the note itself, or the subtopic above it
        reached through first parents that are subtopics."""
        seen, parent = {id(note)}, self._first_parent(note)
        while isinstance(parent, Note) and parent.kind == "subtopic" and id(parent) not in seen:
            note = parent
            seen.add(id(note))
            parent = self._first_parent(note)
        return note

    def subtopic_notes(self, main: Note) -> list:
        """The notes a main subtopic spans: it, then each child subtopic after its first parent, in
        title order."""
        group = []

        def collect(n):
            group.append(n)
            for c in sorted(self.children(n), key=lambda c: c.title.lower()):
                if c.kind == "subtopic" and self._first_parent(c) is n and c not in group:
                    collect(c)

        collect(main)
        return group


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


def find_section(text: str, title: str, ends_at=2):
    """(heading start, content start, end) of the first `## <title>` section outside code and
    comments, or None. It ends at the next heading of level ends_at or above."""
    masked = mask(text)
    m = re.search(rf"^## {re.escape(title)}\b.*$", masked, re.M)
    if not m:
        return None
    start = min(m.end() + 1, len(text))
    nxt = re.compile(rf"^#{{1,{ends_at}}}[ \t]", re.M).search(masked, start)
    return m.start(), start, nxt.start() if nxt else len(text)


def graph_section(text: str):
    """(start, end) of the Learning graph section's content, or None. It ends at the next heading of
    any level, so the text under a ### heading below the graph is never redrawn away."""
    bounds = find_section(text, "Learning graph", 6)
    return bounds[1:] if bounds else None


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
    above = set()  # with --mocs: the MOCs, the topics and every note on the chain above one
    if args.mocs:
        for n in vault.notes:
            if n.kind in ("moc", "topic"):
                above |= {id(n)} | {id(c) for c in vault.chain(n) if c is not None}

    def walk(note, level, printed):
        # A note past --depth, or one --mocs leaves out, is still walked but not printed, so
        # it still counts as inside a chain.
        for child in sorted(vault.children(note), key=lambda n: (n.kind != "moc", n.title.lower())):
            primary = vault._first_parent(child)
            visible = printed and (args.depth is None or level <= args.depth) \
                and (not args.mocs or id(child) in above or note.kind == "moc")
            line = "  " * level + "- " + label(child, args.summary or (args.mocs and child.kind in ("moc", "topic")))
            if primary is not note:
                if visible:
                    print(line + f"  (main place: {label(primary, False)})")
                continue
            if id(child) in shown:
                if visible:
                    print(line + "  (cycle)")
                continue
            shown.add(id(child))
            if visible:
                print(line)
            walk(child, level + 1, visible)

    for root in roots:
        shown.add(id(root))
        print(label(root, args.summary or (args.mocs and root.kind in ("moc", "topic"))))
        walk(root, 1, True)
    if not args.moc:
        section("outside every chain", [f"{label(n, False)}  {n.rel}" for n in vault.outside_chains()])


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
    new = with_graph(text, lines)
    if new != text:
        write_note(topic.path, new)
        print(f"updated the learning graph in {topic.rel} ({len(lines)} lines)")
    else:
        print(f"the learning graph in {topic.rel} is already current")


def with_graph(text: str, lines: list) -> str:
    """A topic note's text with its Learning graph section drawn as lines, the section added before
    Sources when there is none."""
    bounds = graph_section(text)
    block = GRAPH_COMMENT + "\n" + "".join(line + "\n" for line in lines) + "\n"
    if bounds:
        return text[:bounds[0]] + block + text[bounds[1]:]
    sources = find_section(text, "Sources")
    at = sources[0] if sources else len(text)
    return text[:at].rstrip("\n") + "\n\n## Learning graph\n" + block + text[at:]


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
    planned = [(level, n) for level, n, left in rows if n.kind == "stub" and not left]
    left_out = [n for _, n, left in rows if left]
    ready, waiting, ready_rows = [], [], []
    for level, n in planned:
        prereqs = vault.prerequisites(n)
        missing = [p.title if isinstance(p, Note) else "(unresolved)" for p in prereqs
                   if not isinstance(p, Note) or p.kind == "stub"]
        if missing:
            waiting.append(f"{label(n)}  (waits for: {', '.join(missing)})")
        else:
            ready_rows.append((level, n))
            ready.append(f"{label(n)}  (builds on: {', '.join(p.title for p in prereqs) or 'nothing'})")
    print(f"{topic.title}: {len(written)} subtopic{'' if len(written) == 1 else 's'} written, "
          f"{len(planned)} planned, {len(left_out)} left out")
    if ready_rows:  # the shallowest ready node, ties in drawing order, so "next" never has to ask
        print(f"recommended: {min(ready_rows, key=lambda row: row[0])[1].title}")
    section("ready", ready)
    section("waiting", waiting)
    section("left out", [f"{label(n)}  (left out by: {vault._first_parent(n).title})" for n in left_out])


def embeds_children(note: Note) -> bool:
    """Whether the note lists its children by embedding Children.base."""
    return any(link.embed and PurePosixPath(link.name).name.lower() == "children.base" for link in note.body_links())


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
        length = len(WIKI_SHOWN.sub(r"\1", n.summary).split())
        if length > SUMMARY_WORDS:
            warn(n, f"summary has {length} words; one sentence of at most {SUMMARY_WORDS}")
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
        merged = MERGED_HEADING.search(mask(n.body))
        if merged:
            warn(n, f"{merged.group().strip()!r} still holds text appledore merge moved in: "
                    "fold it into the note and delete that heading")
        if n.kind in ("topic", "subtopic") and embeds_children(n):
            listed = "its Learning graph" if n.kind == "topic" else "its Left out list"
            warn(n, f"embeds Children.base, which only a MOC or a type: note needs; {listed} already shows its children")
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

        if n.kind == "subtopic" and vault.main_subtopic(n) is n:
            group = vault.subtopic_notes(n)
            words = sum(g.words() for g in group)
            low, high = SUBTOPIC_WORDS
            if not low <= words <= high:
                warn(n, f"{words} words across {len(group)} note(s); a subtopic is {low}–{high}")
            body = mask(n.body)
            # Writing rule 10 names the closing section after the goal's use when the goal isn't interviews.
            goal = GOAL.search(parents[0].body) if parents and isinstance(parents[0], Note) else None
            missing = [part for part, pattern in SHAPE_PARTS if not pattern.search(body)
                       and not (part == "## In an interview" and goal and "interview" not in goal.group(1).lower())]
            if missing:
                warn(n, f"no {', '.join(missing)}; a subtopic opens with **In short:** and **Example:** "
                        "and ends with ## In an interview and ## Left out on purpose")
            left_out = LEFT_OUT_LIST.search(body)
            if left_out:
                count = len(re.findall(r"^[-*][ \t]+\S", left_out.group(1), re.M))
                if not LEFT_OUT[0] <= count <= LEFT_OUT[1]:
                    warn(n, f"{count} topic{'' if count == 1 else 's'} under Left out on purpose; "
                            f"list {LEFT_OUT[0]}–{LEFT_OUT[1]}")
            bold = [b for g in group for b in BOLD.findall(g.prose()) if b.strip(" :") not in ("In short", "Example")]
            if len(bold) > MAX_CONCEPTS:
                warn(n, f"{len(bold)} bold terms across {len(group)} note(s); a subtopic bolds only its new "
                        f"concepts, at most {MAX_CONCEPTS}")
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

    # Obsidian leaves an empty Untitled Base behind when a new one is abandoned
    for rel in sorted(r for rels in vault.files.values() for r in rels if r.lower().endswith(".base")):
        empty = not (vault.root / rel).read_text(encoding="utf-8", errors="replace").strip()
        untitled = PurePosixPath(rel).stem.lower().startswith("untitled")
        if empty or untitled:
            warnings.append((rel, f"{'an empty' if empty else 'an'}{' Untitled' if untitled else ''} Base: "
                                  + ("delete it" if empty else "name it for what it lists, or delete it")))
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
        bounds = find_section(body, "Sources")
        bullets = "".join(f"- {s}\n" for s in sources)
        if bounds:
            at = bounds[1]
            body = body[:at] + ("" if body[:at].endswith("\n") else "\n") + bullets + body[at:]
        else:
            body = (body + "\n\n## Sources\n" + bullets).lstrip("\n")
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
            write_note(n.path, new)
            print(f"converted {n.rel}")
        else:
            sys.stdout.writelines(difflib.unified_diff(
                n.text.splitlines(True), new.splitlines(True), f"a/{n.rel}", f"b/{n.rel}"))
            print()
    print(f"{changed} note(s) {'converted' if args.write else 'to convert (dry run; add --write)'}")


def rewrite_links(vault: Vault, text: str, target: Note, new_name: str, paths_only=False, keep_shown=False):
    """Point every link to target at new_name, keeping headings and display text, and a pipe escaped
    in a table row, where a bare one would split the cell. Returns (text, count). With paths_only,
    only the links that name target by its path change, as a move to another folder needs. With
    keep_shown, as a merge needs, a body link that showed target's name keeps showing it, as
    [[new|old]], and a property link becomes a plain [[new]]."""
    body_start = len(text) - len(split_frontmatter(text)[1])
    out, last, count = [], 0, 0
    for m in LINK.finditer(mask(text)):
        inner = text[m.start(2):m.end(2)]
        name, heading, display = split_inner(inner)
        if vault.resolve(name) is not target or (paths_only and "/" not in name):
            continue
        if keep_shown and m.start() < body_start:
            heading = display = None
        elif keep_shown and display is None and not m.group(1):  # an embed shows the note, not its name
            shown = re.sub(r"\.md$", "", name.rsplit("/", 1)[-1])
            display = shown if shown != new_name else None
        row = text[text.rfind("\n", 0, m.start()) + 1:m.start()].lstrip().startswith("|")
        bar = "\\|" if row or "\\|" in inner else "|"
        new = new_name + ("#" + heading if heading is not None else "") + (bar + display if display is not None else "")
        out += [text[last:m.start(2)], new]
        last, count = m.end(2), count + 1
    return "".join(out) + text[last:], count


def cmd_mv(vault: Vault, args):
    note = vault.get(args.note)
    new_rel = move_target(vault, note, args.new)
    if note.kind == "stub" and new_rel.parts[0] == NOTES_DIR:
        die(f"a stub becomes a written note with appledore promote '{note.title}' topic, subtopic or note, "
            f"which also gives it the type every note in {NOTES_DIR}/ needs")
    new_title = new_rel.stem
    changes, links, counts = Changes(vault), 0, []
    for n in vault.notes:
        text, count = rewrite_links(vault, n.text, note, new_title)
        if n is note:
            if args.alias and new_title != note.title:
                aliases = as_list(parse_yaml(split_frontmatter(text)[0] or "").get("aliases"))
                if note.title.lower() not in (a.lower() for a in aliases):
                    text = set_frontmatter(text, {"aliases": aliases + [note.title]})
            changes.move(note.rel, new_rel, text)
        elif count:
            changes.write(n.rel, text)
        if count:
            links += count
            counts.append(f"  {n.rel}: {count}")
    finish(changes, args.dry_run,
           [f"moved {note.rel} → {new_rel}; {links} link(s) in {len(counts)} note(s)"] + counts)


# ---------------------------------------------------------------- vault writes

LIST_PROPS = ("mocs", "builds_on", "aliases", "tags", "cssclasses")
LINK_PROPS = ("mocs", "builds_on")
ASSIGNMENT = re.compile(r"^([A-Za-z_]\w*)([+-]?)=(.*)$", re.S)
SOURCE_ASSIGNMENT = re.compile(r"^source\+?=")
PLACEHOLDER = re.compile(r"\{\{[ \t]*(\w+)(?::([^{}]*))?[ \t]*\}\}")  # Obsidian's {{date:YYYY-MM-DD}}
MOMENT = {"YYYY": "%Y", "YY": "%y", "MM": "%m", "DD": "%d", "HH": "%H", "mm": "%M", "ss": "%S"}
MERGED_HEADING = re.compile(r"^## Merged from\b.*$", re.M)
LINE_NUMBER = re.compile(r"\bline \d+\b")
DELETE = object()
ASSIGN_HELP = ("key=value sets a property, and a key repeated in one call lists several values. A link "
               "property (mocs, builds_on) takes a note's title, alias or path. key+=value adds to a list "
               "and key-=value takes out of one. An empty value empties a list and removes anything else. "
               "A - reads more key=value lines from standard input: pass free text in a quoted heredoc "
               "(<<'EOF'), because the shell expands $ and backticks inside double quotes.")


def now():
    """The time a new note is made at."""
    return datetime.datetime.now()


def as_list(value) -> list:
    return [v for v in (value if isinstance(value, list) else [value]) if v]


def fill_template(text: str, title: str, when, values=None) -> str:
    """A template with Obsidian's {{title}}, {{date}} and {{time}} filled in, in the format a
    placeholder gives, each name in values filled from it (Note composer's {{fromTitle}}), and any
    other placeholder, such as {{content}}, left empty. A date format with a token MOMENT lacks is
    refused, so a note never gets a date half filled in."""
    values = {k.lower(): v for k, v in (values or {}).items()}

    def fill(m):
        name, fmt = m.group(1).lower(), m.group(2)
        if name == "title":
            return title
        if name in values:
            return values[name]
        if name not in ("date", "time"):
            return ""
        fmt = (fmt or ("YYYY-MM-DD" if name == "date" else "HH:mm")).strip()
        unknown = [t for t in re.findall(r"([A-Za-z])(\1*)", fmt) if t[0] + t[1] not in MOMENT]
        if unknown or "[" in fmt:
            die(f"the template's {m.group()} uses a token appledore can't fill; it fills {' '.join(MOMENT)}")
        return when.strftime(re.sub(r"([A-Za-z])\1*", lambda t: MOMENT[t.group()], fmt.replace("%", "%%")))
    return PLACEHOLDER.sub(fill, text)


def template(vault: Vault, name: str) -> str:
    """The vault's own template, so the templates stay the one source of each kind's shape."""
    path = vault.root / TEMPLATES_DIR / f"{name}.md"
    if not path.is_file():
        die(f"no {TEMPLATES_DIR}/{path.name}: appledore makes this kind of note from it")
    return path.read_text(encoding="utf-8").lstrip("﻿")


def set_frontmatter(text: str, changes: dict) -> str:
    """The text with each property in changes set to its value, or removed when it is DELETE. Only
    those properties' lines change, so the rest stays as Obsidian wrote it, including lines appledore
    can't parse, such as a property whose name has a space; a new property goes where PROP_ORDER
    puts it."""
    fm_text, body = split_frontmatter(text)
    blocks = []  # [key, lines]: a property's line and the indented lines under it, or [None, [line]]
    for line in fm_text.split("\n") if fm_text else []:
        m = FM_KEY.match(line)
        if m:
            blocks.append([m.group(1), [line]])
        elif line[:1] in (" ", "\t") and blocks:
            blocks[-1][1].append(line)
        else:
            blocks.append([None, [line]])

    def rank(key):
        return PROP_ORDER.index(key) if key in PROP_ORDER else len(PROP_ORDER)

    for key, value in changes.items():
        at = next((i for i, b in enumerate(blocks) if b[0] == key), None)
        if value is DELETE:
            if at is not None:
                del blocks[at]
            continue
        lines = dump_yaml({key: value}).split("\n")
        if at is not None:
            blocks[at][1] = lines
            continue
        keyed = [i for i, b in enumerate(blocks) if b[0] is not None]
        before = [i for i in keyed if rank(blocks[i][0]) <= rank(key)]
        blocks.insert(before[-1] + 1 if before else keyed[0] if keyed else len(blocks), [key, lines])
    return "---\n" + "\n".join(line for _, lines in blocks for line in lines) + "\n---\n" + body


def link_name(value: str) -> str:
    """The note a property value or an argument names: [[X|shown]] and X both name X."""
    m = LINK.search(value)
    return split_inner(m.group(2))[0] if m else value.strip()


def read_assignments(args: list) -> list:
    """The key=value arguments, with a - replaced by the lines on standard input, one key=value a line.
    Standard input is read as UTF-8, which a heredoc sends, whatever encoding the platform gives a
    pipe; a - that reads no line is refused, because a forgotten heredoc would look like success."""
    out = []
    for a in args:
        if a != "-":
            out.append(a)
            continue
        try:
            text = sys.stdin.buffer.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            die("standard input isn't UTF-8")
        lines = [line for line in text.split("\n") if line.strip()]
        if not lines:
            die("- read no key=value line from standard input; pass them in a heredoc: - <<'EOF'")
        out += lines
    return out


def assign(vault: Vault, data: dict, assignments: list, title: str) -> dict:
    """The property changes that key=value, key+=value and key-=value make to data. A link property
    takes a note's title, alias or path, and stores a link to its title. Whether the result breaks a
    rule is check's to say: every write command runs it before writing."""
    changes, replaced = {}, set()
    for a in assignments:
        m = ASSIGNMENT.match(a)
        if not m:
            die(f"{a!r} isn't key=value, key+=value or key-=value")
        key, op, value = m.group(1), m.group(2), m.group(3).strip()
        if key == "source":
            die("source= adds a source only to a new note; edit an existing note's ## Sources section")
        if key not in KNOWN_PROPS:
            die(f"unknown property {key!r}; the vault's are {', '.join(PROP_ORDER)}")
        if key not in LIST_PROPS:
            if op:
                die(f"{key} holds one value: use {key}=")
            changes[key] = value if value else DELETE
            continue
        current = changes.get(key, data.get(key))
        items = [] if current in (None, DELETE) else as_list(current)
        if not op and key not in replaced:  # the first key= in a call replaces the list, the next ones add
            items = []
            replaced.add(key)
        if not value:
            if op:
                die(f"{key}{op}= needs a value")
            changes[key] = items
            continue
        if key in LINK_PROPS:
            target = vault.get(link_name(value))
            value = f"[[{target.title}]]"

            def same(v):
                return vault.resolve(link_name(v)) is target
        else:
            def same(v):
                return norm_name(v) == norm_name(value)
        if op == "-":
            if not any(same(v) for v in items):
                die(f"{value!r} isn't in {key}")
            items = [v for v in items if not same(v)]
        elif not any(same(v) for v in items) and not (key == "aliases" and norm_name(value) == norm_name(title)):
            items.append(value)
        changes[key] = items
    return changes


def norm_name(name: str) -> str:
    """A name as the duplicate check compares it: in one Unicode form, because a disk can store é as
    e plus an accent, ignoring case, and with spaces, hyphens and underscores alike."""
    return re.sub(r"[\s_-]+", " ", unicodedata.normalize("NFC", name).lower()).strip()


def same_name(vault: Vault, name: str) -> list:
    """The notes whose title or an alias is name, as norm_name compares them."""
    key = norm_name(name)
    return [n for n in vault.notes if key in (norm_name(x) for x in [n.title] + n.aliases)]


def close_names(vault: Vault, name: str) -> list:
    """The notes whose title or an alias is spelt nearly like name: the duplicates a new note risks."""
    names = {}
    for n in vault.notes:
        if n.kind != "root":
            for x in [n.title] + n.aliases:
                names.setdefault(norm_name(x), n)
    hits = difflib.get_close_matches(norm_name(name), list(names), n=5, cutoff=0.8)
    return list(dict.fromkeys(names[h] for h in hits))


def check_title(title: str):
    """Refuse a title that Obsidian can't link to, or hides because it starts with a dot."""
    if BAD_TITLE_CHARS & set(title) or not title.strip():
        die(f"a title can't hold any of {' '.join(sorted(BAD_TITLE_CHARS))}; put the real form in aliases")
    if title.startswith("."):
        die("a title can't start with a dot, because Obsidian hides that file; put the real form in aliases")


def move_target(vault: Vault, note: Note, dest: str) -> PurePosixPath:
    """Where a note goes for `mv NOTE DEST`: a new title, a path, or a folder ending in /. Refused when
    the title can't be used, another note has it, or another file is there, so a move never
    replaces a file."""
    dest = dest.strip().lstrip("/")
    if dest.endswith("/"):
        new_rel = PurePosixPath(dest) / note.rel.name
    elif "/" in dest:
        new_rel = PurePosixPath(dest if dest.endswith(".md") else dest + ".md")
    else:
        new_rel = note.rel.parent / (dest if dest.endswith(".md") else dest + ".md")
    check_title(new_rel.stem)
    key = unicodedata.normalize("NFC", new_rel.stem).lower()
    clash = [n for n in vault.notes if n is not note and unicodedata.normalize("NFC", n.title).lower() == key]
    if clash:
        die(f"{new_rel.stem!r} already exists: {clash[0].rel}")
    if new_rel == note.rel:
        die("that is where it already is")
    target = vault.root / new_rel
    if target.exists() and not os.path.samefile(target, note.path):  # a case-only rename is the same file
        die(f"{new_rel} already exists")
    return new_rel


def source_items(text: str):
    """(the text without its Sources section, the section's items). An item is a line and the
    indented lines under it, so a nested line stays with its source."""
    bounds = find_section(text, "Sources")
    if not bounds:
        return text, []
    items = []
    for line in text[bounds[1]:bounds[2]].split("\n"):
        if line.strip() in ("", "-"):
            continue
        if line[:1] in (" ", "\t") and items:
            items[-1] += "\n" + line.rstrip()
        else:
            items.append(line.rstrip())
    return text[:bounds[0]] + text[bounds[2]:], items


def add_sources(text: str, items: list) -> str:
    """The text with each item under its ## Sources section, in place of a template's empty bullet,
    leaving out an item the section already has. A note without the section gets one at the end."""
    if not items:
        return text
    text = text if text.endswith("\n") else text + "\n"
    bounds = find_section(text, "Sources")
    if not bounds:
        _, body = split_frontmatter(text)
        return text.rstrip("\n") + "\n" + ("\n" if body.strip() else "") + "## Sources\n" + "\n".join(items) + "\n"
    _, kept = source_items(text)
    seen, lines = set(), []
    for item in kept + items:
        if " ".join(item.split()) not in seen:
            seen.add(" ".join(item.split()))
            lines.append(item)
    start, end = bounds[1], bounds[2]
    return text[:start] + "\n".join(lines) + "\n" + ("\n" if end < len(text) else "") + text[end:]


def write_note(path: Path, text: str, create=False):
    """Write a file whole. A new one is made only when no file has its name, so nothing is ever
    overwritten; an existing one gets a finished copy swapped in, so a crash or a sync client never
    meets half a note."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if create:
        try:
            with open(path, "x", encoding="utf-8") as f:
                f.write(text)
        except FileExistsError:
            die(f"a file named like {path.name} is already in {path.parent.name}/; nothing was overwritten")
        return
    tmp = path.with_name(f".{path.name}.appledore")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


class Changes:
    """The files one write command changes, gathered before any is written. Every write command goes
    through finish(), so each is checked the same way before it writes, has the same dry run, a
    diff, and swaps each file in whole."""

    def __init__(self, vault: Vault):
        self.vault = vault
        self.texts = {}  # path inside the vault -> its new text, or None for a file that goes
        self.moves = {}  # new path -> old path
        self.carried = {}  # a merged note's path -> the note its text, and so its errors, now sit in

    def write(self, rel, text):
        self.texts[str(rel)] = text

    def move(self, old, new, text):
        self.texts[str(old)], self.texts[str(new)] = None, text
        self.moves[str(new)] = str(old)

    def delete(self, rel):
        self.texts[str(rel)] = None

    def after(self) -> Vault:
        return Vault(self.vault.root, self.texts)

    def original(self, rel) -> str:
        note = self.vault.by_rel.get(rel.lower())
        return note.text if note else ""

    def diff(self):
        for rel in sorted(self.texts, key=str.lower):
            text, old = self.texts[rel], self.moves.get(rel, rel)
            if text is None:
                if rel not in self.moves.values():
                    print(f"delete {rel}")
                continue
            if old != rel:
                print(f"move {old} → {rel}")
            before = self.original(old)
            for line in difflib.unified_diff(before.splitlines(True), text.splitlines(True),
                                             f"a/{old}" if before else "/dev/null", f"b/{rel}"):
                sys.stdout.write(line if line.endswith("\n") else line + "\n")

    def apply(self):
        root = self.vault.root
        created = [rel for rel, text in self.texts.items()
                   if text is not None and rel not in self.moves and self.vault.by_rel.get(rel.lower()) is None]
        for rel in created:  # first, so a name already on disk stops the command before anything else
            write_note(root / rel, self.texts[rel], create=True)
        for new, old in self.moves.items():
            (root / new).parent.mkdir(parents=True, exist_ok=True)
            os.rename(root / old, root / new)  # a case-only rename works on case-insensitive disks too
        for rel, text in self.texts.items():
            if text is not None and rel not in created:
                write_note(root / rel, text)
        for rel, text in self.texts.items():
            if text is None and rel not in self.moves.values():
                (root / rel).unlink()


def redraw_touched(changes: Changes, after: Vault) -> list:
    """Redraw the Learning graph of each topic whose graph holds a note the changes touch, before or
    after them, when it no longer matches; a topic with nothing to draw gets no section. Every other
    topic is left as it is. Returns the paths of the topics redrawn."""
    touched = {PurePosixPath(rel).stem.lower() for rel in changes.texts}

    def members(vault):
        return {t.title.lower(): {n.title.lower() for _, n, _ in vault.graph_rows(t)[0]} | {t.title.lower()}
                for t in vault.notes if t.kind == "topic"}

    before, now_ = members(changes.vault), members(after)
    redrawn = []
    for topic in after.notes:
        if topic.kind != "topic" or not touched & (before.get(topic.title.lower(), set()) | now_[topic.title.lower()]):
            continue
        lines, _ = after.learning_graph(topic)
        if drawn_graph(topic.text) != lines and (lines or graph_section(topic.text)):
            changes.write(topic.rel, with_graph(topic.text, lines))
            redrawn.append(str(topic.rel))
    return redrawn


def finish(changes: Changes, dry_run: bool, report: list):
    """Check the vault as the changes would leave it, redraw the learning graphs they touch, then
    write them all, or with dry_run print them as a diff. A command whose result would add a check
    error is refused whole, so no write command leaves the vault with an error it didn't have."""
    after = changes.after()
    redrawn = redraw_touched(changes, after)
    if redrawn:
        after = changes.after()
    # Errors are matched per note and without their line numbers, so an error a note already had
    # still counts as old after the write moves it to another line.
    moved = {old.lower(): new.lower() for new, old in changes.moves.items()}
    moved.update((old.lower(), into.lower()) for old, into in changes.carried.items())

    def key(rel, msg):
        return moved.get(rel.lower(), rel.lower()), LINE_NUMBER.sub("", msg)

    old = collections.Counter(key(rel, msg) for rel, msg in check(changes.vault)[0])
    added = []
    for rel, msg in check(after)[0]:
        if old[key(rel, msg)]:
            old[key(rel, msg)] -= 1
        else:
            added.append((rel, msg))
    if added:
        die("refused, so nothing was written: it would leave these check errors:\n"
            + "\n".join(f"  {rel}: {msg}" for rel, msg in added))
    report = report + [f"redrew the learning graph in {rel}" for rel in redrawn]
    if dry_run:
        print("dry run, so nothing was written:")
        print("\n".join(report))
        changes.diff()
        return
    changes.apply()
    print("\n".join(report))


def cmd_new(vault: Vault, args):
    title = unicodedata.normalize("NFC", args.title.strip())  # Obsidian keys its files by NFC names
    title = title[:-3] if title.lower().endswith(".md") else title
    check_title(title)
    if args.kind == "moc" and not title.endswith(" MOC"):
        die("a MOC's title ends in ' MOC'")
    for n in same_name(vault, title):
        what = "a note" if norm_name(n.title) == norm_name(title) else "an alias of a note"
        die(f"{title!r} is already {what}: {n.rel}  [{n.kind}]  {n.summary}\n"
            "Link that note instead, or give this one a name of its own.")
    assignments = read_assignments(args.assignments)
    sources = [s if s.startswith("- ") else "- " + s
               for s in (a.split("=", 1)[1].strip() for a in assignments if SOURCE_ASSIGNMENT.match(a)) if s]
    assignments = [a for a in assignments if not SOURCE_ASSIGNMENT.match(a)]
    if any(re.match(r"type[+-]?=", a) for a in assignments):
        die(f"the kind sets the type: appledore new {args.kind} …")
    values, parent = {}, None
    if args.kind == "child":
        parents = [a.split("=", 1)[1] for a in assignments if re.match(r"mocs\+?=", a)]
        if not parents:
            die("a child needs the note it is part of: mocs=<that note>")
        parent = vault.get(link_name(parents[0]))
        values["fromTitle"] = parent.title
    folder, name = (NOTES_DIR, CHILD_TEMPLATE) if args.kind == "child" else KINDS[args.kind][:2]
    text = fill_template(template(vault, name), title, now(), values)
    fm_text, _ = split_frontmatter(text)
    data = parse_yaml(fm_text) if fm_text else {}
    changes = assign(vault, data, assignments, title)
    planned = parent is not None and parent.kind == "stub" and any(
        isinstance(p, Note) and p.kind == "topic" for p in vault.parents(parent))  # a subtopic still being written
    if parent is not None and (parent.kind == "subtopic" or planned):
        # The part of a subtopic is a subtopic, with no prerequisites of its own (the vault's README).
        changes["type"] = "subtopic"
        changes.setdefault("builds_on", as_list(data.get("builds_on")))
    if not {**data, **changes}.get("created"):
        changes["created"] = now().date().isoformat()
    rel = f"{folder}/{title}.md"
    plan = Changes(vault)
    plan.write(rel, add_sources(set_frontmatter(text, changes), sources))
    report = [f"created {rel}"]
    close = close_names(vault, title)
    if close:
        report.append("names already close to it: " + ", ".join(f"{n.title} ({n.rel})" for n in close)
                      + "; if one is the same concept, merge them with appledore merge")
    finish(plan, args.dry_run, report)


def cmd_promote(vault: Vault, args):
    note = vault.get(args.note)
    if note.kind not in ("stub",) + NOTE_TYPES:
        die(f"{note.title!r} is a {note.kind}; only a stub or a note in {NOTES_DIR}/ becomes a {args.kind}")
    t_fm, t_body = split_frontmatter(fill_template(template(vault, KINDS[args.kind].template), note.title, now()))
    t_data = parse_yaml(t_fm) if t_fm else {}
    # The template adds the properties a kind has and sets its type; the note keeps its own values.
    changes = {k: v for k, v in t_data.items() if k == "type" or (k not in note.fm and v is not None)}
    changes.update(assign(vault, {**note.fm, **changes}, read_assignments(args.assignments), note.title))
    rest, sources = source_items(note.body)
    if note.kind == "stub" and not rest.strip():  # a stub holds only its Sources, so it takes the template's parts
        fm_text = split_frontmatter(note.text)[0]
        text = add_sources(("---\n" + fm_text + "\n---\n" if fm_text else "") + t_body, sources)
    else:
        text = note.text
    text = set_frontmatter(text, changes)
    plan = Changes(vault)
    if note.folder == NOTES_DIR:
        plan.write(note.rel, text)
        report = [f"{note.rel}: now a {args.kind}"]
    else:
        new_rel = move_target(vault, note, NOTES_DIR + "/")
        for n in vault.notes:
            if n is not note:
                new, count = rewrite_links(vault, n.text, note, note.title, paths_only=True)
                if count:
                    plan.write(n.rel, new)
        plan.move(note.rel, new_rel, text)
        report = [f"{note.rel} → {new_rel}: now a {args.kind}"]
    finish(plan, args.dry_run, report)


def cmd_set(vault: Vault, args):
    note = vault.get(args.note)
    changes = assign(vault, note.fm, read_assignments(args.assignments), note.title)
    if "type" in changes and note.folder != NOTES_DIR:
        die(f"only a note in {NOTES_DIR}/ has a type; appledore promote makes a stub a written note")
    text = set_frontmatter(note.text, changes)
    if text == note.text:
        print(f"{note.rel}: already set")
        return
    plan = Changes(vault)
    plan.write(note.rel, text)
    finish(plan, args.dry_run, [f"{note.rel}: set {', '.join(changes)}"])


def tidy_link_props(vault: Vault, text: str, me: Note) -> str:
    """The text with each link property listing a note once, and never the note itself."""
    fm_text, _ = split_frontmatter(text)
    data = parse_yaml(fm_text) if fm_text else {}
    changes = {}
    for key in LINK_PROPS:
        values = data.get(key)
        if not isinstance(values, list):
            continue
        kept, seen = [], set()
        for v in values:
            target = vault.resolve(link_name(v))
            ident = id(target) if target is not None else link_name(v).lower()
            if target is not me and ident not in seen:
                seen.add(ident)
                kept.append(v)
        if kept != values:
            changes[key] = kept
    return set_frontmatter(text, changes) if changes else text


def cmd_merge(vault: Vault, args):
    old, into = vault.get(args.note), vault.get(args.into)
    if old is into:
        die("a note can't merge into itself")
    if not args.force:
        if old.kind in ("moc", "topic"):
            die(f"{old.title!r} is a {old.kind}, so merging it would take apart its "
                f"{'chain' if old.kind == 'moc' else 'learning graph'}; pass --force if the user wants that")
        if into.kind == "stub" and old.kind != "stub":
            die(f"{into.title!r} is a stub and {old.title!r} is a written {old.kind}: merge the stub into the "
                "written note instead, by swapping the two, or pass --force")
    if vault.parents(into) == [old]:
        die(f"{into.title!r} sits only under {old.title!r}, so the merge would leave it with no parent; "
            "give it another first, with appledore set")
    plan, links = Changes(vault), 0
    for n in vault.notes:
        if n is not old:
            text, count = rewrite_links(vault, n.text, old, into.title, keep_shown=True)
            if count:
                plan.write(n.rel, tidy_link_props(vault, text, n))
                links += count
    linked = len(plan.texts)
    text = plan.texts.get(str(into.rel), into.text)
    # into takes old's names as aliases and its prerequisites, and keeps its own place.
    data = parse_yaml(split_frontmatter(text)[0] or "")
    aliases, prereqs = as_list(data.get("aliases")), as_list(data.get("builds_on"))
    changes = {"aliases": list(aliases), "builds_on": list(prereqs)}
    for name in [old.title] + old.aliases:
        if norm_name(name) not in [norm_name(a) for a in changes["aliases"]] + [norm_name(into.title)]:
            changes["aliases"].append(name)
    known = {id(vault.resolve(link_name(p))) for p in prereqs} | {id(into)} | {id(p) for p in vault.parents(into)}
    for target in vault.prerequisites(old):
        if isinstance(target, Note) and id(target) not in known:
            known.add(id(target))
            changes["builds_on"].append(f"[[{target.title}]]")
    text = set_frontmatter(text, {k: v for k, v in changes.items() if v != (aliases if k == "aliases" else prereqs)})
    # old's summary and text land under a heading of their own, and its sources under into's, so
    # nothing is lost.
    rest, sources = source_items(split_frontmatter(rewrite_links(vault, old.text, old, into.title, keep_shown=True)[0])[1])
    parts = ([f"Summary: {old.summary}"] if old.summary else []) + ([rest.strip()] if rest.strip() else [])
    if parts:
        block = f"## Merged from {old.title}\n" + "\n\n".join(parts) + "\n"
        bounds = find_section(text, "Sources")
        text = (text[:bounds[0]].rstrip("\n") + "\n\n" + block + "\n" + text[bounds[0]:] if bounds
                else text.rstrip("\n") + "\n\n" + block)
    plan.write(into.rel, add_sources(text, sources))
    plan.delete(old.rel)
    plan.carried[str(old.rel)] = str(into.rel)
    own = {id(p) for p in vault.parents(into)}
    lost = [f"{key}: {', '.join(old.values(key))}" for key in old.fm
            if key not in ("summary", "aliases", "builds_on") and old.values(key)
            and not (key == "mocs" and all(id(p) in own for p in vault.parents(old)))]
    report = [f"merged {old.rel} into {into.rel}: {links} link(s) in {linked} note(s) now point at "
              f"{into.title!r}, which takes {old.title!r} as an alias; {old.rel} is deleted"]
    if parts:
        report.append(f"its summary and text sit under '## Merged from {old.title}' in {into.rel}: fold them in")
    if lost:
        report.append(f"not kept from {old.title!r}: " + "; ".join(lost))
    finish(plan, args.dry_run, report)


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


# ---------------------------------------------------------------- the wrap-up and the cold read

MOC_SUGGEST_AT = 5      # a type: note with this many children might be better as a MOC
DUPLICATE_WORDS = 4     # two summaries sharing at least this many key words,
DUPLICATE_SHARE = 0.6   # and this share of the shorter one's, likely say the same thing
STOPWORDS = set("""about after all also and any are been before but can does each for from has have how into its
more most not one only over such than that the their them then there these they this through two under use used
uses using was were what when where which while who why will with without would you your""".split())
STARTING_FROM = re.compile(r"^[ \t]*[-*][ \t]+\*\*Starting from(?::\*\*|\*\*:)[ \t]*(.*)$", re.M)  # a topic's Scope line
COLD_READ = Path(__file__).resolve().parent.parent / "cold-read.md"
IN_PROGRESS = (("MERGE_HEAD", "a merge"), ("CHERRY_PICK_HEAD", "a cherry-pick"), ("REVERT_HEAD", "a revert"),
               ("rebase-merge", "a rebase"), ("rebase-apply", "a rebase"))
SETTLE = "the user must settle these in git before a commit"
# The variables that tell git where a repository is: the names git rev-parse --local-env-vars prints,
# and GIT_NAMESPACE. Inherited from a git hook or a shell, they would override git -C and send a
# commit and a push to another repository.
GIT_LOCATION_VARS = {"GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT",
                     "GIT_OBJECT_DIRECTORY", "GIT_DIR", "GIT_WORK_TREE", "GIT_IMPLICIT_WORK_TREE", "GIT_GRAFT_FILE",
                     "GIT_INDEX_FILE", "GIT_NO_REPLACE_OBJECTS", "GIT_REPLACE_REF_BASE", "GIT_PREFIX",
                     "GIT_SHALLOW_FILE", "GIT_COMMON_DIR", "GIT_NAMESPACE"}


def git(vault: Vault, *args, timeout=60):
    """Run git in the vault's own repository, whatever the environment points at, and with no
    terminal, so neither git nor ssh can wait for a password, a passphrase or a host key answer:
    (exit code, stdout, stderr). The exit code is None when git can't start or hangs."""
    env = {k: v for k, v in os.environ.items() if k not in GIT_LOCATION_VARS}
    env["GIT_TERMINAL_PROMPT"] = "0"
    try:
        done = subprocess.run(["git", "-C", str(vault.root), *args], stdin=subprocess.DEVNULL, capture_output=True,
                              encoding="utf-8", errors="replace", timeout=timeout, start_new_session=True, env=env)
    except (OSError, subprocess.SubprocessError) as e:
        return None, "", str(e)
    return done.returncode, done.stdout, done.stderr.strip()


def git_or_die(vault: Vault, *args) -> str:
    code, out, err = git(vault, *args)
    if code != 0:
        die(f"git {args[0]} failed: {err or 'no output'}")
    return out


def own_repository(vault: Vault, instead: str = ""):
    """Stop unless the vault is the top folder of its own git repository, so a commit and a push
    hold only the vault's changes, and git's paths are the vault's."""
    code, prefix, err = git(vault, "rev-parse", "--show-prefix")
    if code != 0:
        die(f"the vault isn't a git repository ({err}){instead}")
    if prefix.strip():
        die(f"the vault is the folder {prefix.strip().rstrip('/')!r} inside a larger git repository, and "
            f"appledore reviews and commits only a vault that is its own repository{instead}")
    code, top, err = git(vault, "rev-parse", "--show-toplevel")
    try:
        same = code == 0 and os.path.samefile(top.strip(), vault.root)
    except OSError:
        same = False
    if not same:
        die(f"git's top folder is {top.strip() or err!r}, not the vault, and appledore reviews and commits "
            f"only a vault that is its own repository{instead}")


def repository_problems(vault: Vault) -> list:
    """What only the user can settle before a commit: a note git couldn't merge, which holds conflict
    markers that add -A would mark resolved; a merge, rebase, cherry-pick or revert in progress, which
    a commit would conclude; and a detached HEAD, where a commit would land on no branch."""
    unmerged = {entry.split("\t", 1)[1] for entry in git_or_die(vault, "ls-files", "-u", "-z").split("\0") if "\t" in entry}
    problems = [f"{rel}: unmerged, with conflict markers to resolve" for rel in sorted(unmerged)]
    paths = git_or_die(vault, "rev-parse", *[arg for name, _ in IN_PROGRESS for arg in ("--git-path", name)])
    for (_, what), path in zip(IN_PROGRESS, paths.splitlines()):
        if (vault.root / path).exists() and f"{what} is in progress" not in problems:
            problems.append(f"{what} is in progress")
    if git(vault, "symbolic-ref", "-q", "HEAD")[0] != 0:
        problems.append("HEAD is detached, so a commit would land on no branch")
    return problems


def session_changes(vault: Vault) -> list:
    """The vault's paths changed since its last commit, as (git's two status letters, path, what its
    mocs listed at that commit, resolved in the vault as it is now: None for a parent renamed or
    deleted since, nothing for a note new since then), so the review sees the MOC a note left and
    the notes that gained a child."""
    own_repository(vault, "; name the notes to review instead")
    fields = git_or_die(vault, "status", "--porcelain", "-z", "--untracked-files=all").split("\0")
    changes, i = [], 0
    while i < len(fields):
        status, path, old = fields[i][:2], fields[i][3:], None
        i += 1
        if not path:
            continue
        if "R" in status or "C" in status:  # a staged rename or copy is followed by its old path
            old, i = fields[i], i + 1
        before = []
        if status[0] not in "?C" and path.endswith(".md"):
            code, text, _ = git(vault, "show", f"HEAD:{old or path}")
            fm_text = split_frontmatter(text)[0] if code == 0 else None
            mocs = parse_yaml(fm_text).get("mocs") if fm_text else None
            for value in mocs if isinstance(mocs, list) else [mocs] if mocs else []:
                before += [vault.resolve(split_inner(m.group(2))[0]) for m in LINK.finditer(value)]
        changes.append((status, path, [n if isinstance(n, Note) else None for n in before]))
    return sorted(changes, key=lambda c: c[1].lower())


def singular(word: str) -> str:
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    return word[:-1] if len(word) > 3 and word.endswith("s") and not word.endswith("ss") else word


def key_words(text: str) -> set:
    """A summary's words for comparing it with another: links as their shown text, without short
    and common words or a plural s."""
    words = re.findall(r"[a-z0-9]+", fold(WIKI_SHOWN.sub(r"\1", text)))
    return {singular(w) for w in words if len(w) > 2 and w not in STOPWORDS}


def likely_duplicates(vault: Vault, note: Note) -> list:
    """Other notes that may hold note's concept, as (note, why): the same name or alias, plural or
    singular, or summaries that share most of their key words."""
    names = {singular(norm(x)) for x in [note.title] + note.aliases}
    words, found = key_words(note.summary), []
    for other in vault.notes:
        if other is note or other.kind in ("root", "other"):
            continue
        if names & {singular(norm(x)) for x in [other.title] + other.aliases}:
            found.append((other, "the same name"))
            continue
        theirs = key_words(other.summary)
        shared = words & theirs
        if len(shared) >= max(DUPLICATE_WORDS, DUPLICATE_SHARE * min(len(words), len(theirs))):
            found.append((other, "summaries share " + ", ".join(sorted(shared))))
    return found


def cmd_review(vault: Vault, args):
    problems = []
    if args.notes:
        changes = [("??", str(vault.get(n).rel), []) for n in args.notes]
    else:
        changes = session_changes(vault)
        problems = repository_problems(vault)
    section(SETTLE, problems)
    # git on macOS prints paths precomposed (NFC), which a note's name on disk may not be.
    by_path = {unicodedata.normalize("NFC", str(n.rel)).lower(): n for n in vault.notes}
    notes, new, items, grew = [], [], [], {}
    for status, rel, before in changes:
        old = [p for p in before if p is not None]
        for p in old:  # how many more children each note has than at the last commit
            grew[id(p)] = grew.get(id(p), 0) - 1
        n = by_path.get(unicodedata.normalize("NFC", rel).lower())
        if n is None:
            items.append(f"{rel}  [{'deleted' if not (vault.root / rel).exists() else 'not a note'}]")
            continue
        notes.append(n)
        if status[0] in "?AR":
            new.append(n)
        # A parent at the last commit that no longer resolves was renamed or deleted, so the note may
        # sit under that same parent by a new name: only a parent it had then counts it again.
        renamed = len(old) < len(before)
        for p in vault.parents(n):
            if isinstance(p, Note) and (not renamed or p in old):
                grew[id(p)] = grew.get(id(p), 0) + 1
        parent = vault._first_parent(n)
        chain = [parent] + vault.chain(parent) if isinstance(parent, Note) else []
        items.append(f"{label(n, False)}  {n.rel}" + (
            "  under " + " → ".join(c.title if c else "(cycle)" for c in chain) if chain else ""))
    if not args.notes and not changes:
        print("nothing changed since the last commit")
    section("notes to review" if args.notes else "changed since the last commit", items)

    # What the wrap-up reviews: the changed notes, the MOCs and notes above them, and the
    # MOCs they left.
    reviewed = {}
    for n in notes + [p for _, _, before in changes for p in before if p is not None]:
        for x in [n] + [c for p in vault.parents(n) if isinstance(p, Note) for c in [p] + vault.chain(p)]:
            if isinstance(x, Note):
                reviewed.setdefault(id(x), x)
    reviewed = sorted(reviewed.values(), key=lambda n: str(n.rel).lower())
    paths = {str(n.rel) for n in reviewed} | {rel for _, rel, _ in changes}

    errors, warnings = check(vault)
    found = [("errors in the vault: fix each before committing", [f"{rel}: {m}" for rel, m in errors]),
             ("warnings on these notes and the chains above them",
              [f"{rel}: {m}" for rel, m in warnings if rel in paths])]
    # Only a note that gained children since the last commit, so a change the user declined isn't
    # proposed again at every wrap-up.
    hubs = [n for n in reviewed if n.kind == "note" and grew.get(id(n), 0) > 0]
    found.append(("gained children it doesn't list: add ![[Children.base]] at the end of the body, before Sources",
                  [f"{n.title}  ({len(vault.children(n))} children)" for n in hubs if not embeds_children(n)]))
    found.append((f"gained children, now {MOC_SUGGEST_AT} or more: maybe better as a MOC",
                  [f"{n.title}  ({len(vault.children(n))} children)" for n in hubs
                   if len(vault.children(n)) >= MOC_SUGGEST_AT]))
    pairs, seen = [], set()
    for n in new:
        for other, why in likely_duplicates(vault, n):
            if frozenset((id(n), id(other))) not in seen:
                seen.add(frozenset((id(n), id(other))))
                pairs.append(f"{n.title}  ~  {label(other, False)}: {why}")
    found.append(("likely duplicates: merge the two if they hold one concept", pairs))
    found.append(("outside every chain: set mocs so each chain reaches a root MOC",
                  [f"{label(n, False)}  {n.rel}" for n in vault.outside_chains()]))
    finished = []
    for topic in reviewed:
        if topic.kind == "topic" and topic.fm.get("status") != "done":
            rows, _ = vault.graph_rows(topic)
            if not any(n.kind == "stub" and not left for _, n, left in rows):
                written = sum(1 for _, n, _ in rows if n.kind == "subtopic")
                left_out = sum(1 for _, _, left in rows if left)
                finished.append(f"{topic.title}: {written} subtopic{'' if written == 1 else 's'} written, "
                                f"{left_out} stub{'' if left_out == 1 else 's'} left out")
    found.append(("topics with nothing planned: ask whether their status becomes done", finished))
    for title, lines in found:
        section(title, lines)
    if not problems and not any(lines for _, lines in found):
        print("nothing to change")


def case_renames(vault: Vault) -> list:
    """Tracked files whose name on disk now differs only in letter case. A repository that ignores
    case, as git sets one up on macOS, sees no change there, so a commit would keep the old name."""
    listings, found = {}, []
    for rel in filter(None, git_or_die(vault, "ls-files", "-z").split("\0")):
        folder = vault.root
        for part in PurePosixPath(rel).parts:
            if folder not in listings:
                try:
                    listings[folder] = {unicodedata.normalize("NFC", x) for x in os.listdir(folder)}
                except OSError:
                    listings[folder] = set()
            if unicodedata.normalize("NFC", part) not in listings[folder]:
                if (vault.root / rel).exists():  # it is still there under another case, not deleted
                    found.append(rel)
                break
            folder = folder / part
    return found


def commit_message(args) -> str:
    """The message: MESSAGE, or the text of the file -F names, standard input for -. Standard input,
    fed by a quoted heredoc, is the safe way, because in double quotes the shell runs a backtick span
    and expands a $."""
    if args.file is None:
        text = args.message
    elif args.file == "-":
        text = sys.stdin.read()
    else:
        try:
            text = Path(args.file).read_text(encoding="utf-8")
        except OSError as e:
            die(f"can't read the message: {e}")
    if not text.strip():
        die("the commit message is empty")
    return text.strip()


def cmd_commit(vault: Vault, args):
    message = commit_message(args)
    own_repository(vault)
    problems = repository_problems(vault)
    if problems:
        section(SETTLE, problems)
        die("nothing committed: ask the user to settle these first", 1)
    errors, _ = check(vault)
    if errors:
        for rel, msg in errors:
            print(f"  {rel}: {msg}")
        die(f"nothing committed: appledore check found {len(errors)} error(s); fix them first", 1)
    renamed = case_renames(vault)
    for rel in renamed:
        git_or_die(vault, "rm", "--cached", "-q", "--", rel)
    git_or_die(vault, "add", "-A")
    # Every file staged, with git's status letter, since add -A takes settings, attachments and
    # deletions too, and the user should see each one.
    fields, staged, i = git_or_die(vault, "diff", "--cached", "--name-status", "-z").split("\0"), [], 0
    while i < len(fields) - 1:
        paths = 2 if fields[i][:1] in ("R", "C") else 1  # a rename or copy names the old path, then the new
        staged.append(f"{fields[i][:1]}  " + " → ".join(fields[i + 1:i + 1 + paths]))
        i += 1 + paths
    if staged:
        code, _, err = git(vault, "commit", "-q", "-m", message)
        if code != 0:
            die(f"the commit failed, so nothing was pushed: {err}", 1)
        print(f"committed {len(staged)} file{'' if len(staged) == 1 else 's'}: {message.splitlines()[0]}")
        for line in staged:
            print(f"  {line}")
    else:
        print("nothing to commit")

    code, upstream, _ = git(vault, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    if code != 0:
        remotes = git_or_die(vault, "remote").split()
        if not remotes:
            print("not pushed: the vault has no remote")
            return
        die(f"not pushed: the branch has no upstream; the user can set one with git push -u {remotes[0]} HEAD", 1)
    upstream = upstream.strip()
    ahead = int(git_or_die(vault, "rev-list", "--count", "@{upstream}..HEAD"))
    if not ahead:
        print(f"nothing to push: {upstream} has every commit")
        return
    # One try only: a push that fails needs the user (a login, a network, a remote that moved on),
    # and the commit stays in the vault either way.
    code, _, err = git(vault, "push", "--quiet", timeout=120)
    if code != 0:
        die(f"the push to {upstream} failed and was not retried; {ahead} commit(s) wait in the vault: "
            f"{err or 'no output'}", 1)
    print(f"pushed {ahead} commit{'' if ahead == 1 else 's'} to {upstream}")


def cmd_brief(vault: Vault, args):
    note = vault.get(args.note)
    if note.kind != "subtopic":
        parent = vault._first_parent(note)
        if note.kind == "stub":  # a stub a subtopic left out is a deep dive, not part of its text
            why = "it has no text yet, so there is nothing to read cold"
        elif note.kind == "topic":
            why = "a cold read reads one subtopic; pass one of its subtopics"
        elif isinstance(parent, Note) and parent.kind == "subtopic":
            why = f"a cold read reads one subtopic; pass the subtopic it belongs to: {vault.main_subtopic(parent).title!r}"
        else:
            why = "a cold read reads one subtopic"
        die(f"{note.title!r} is a {note.kind}, not a written subtopic, and {why}")
    group = vault.subtopic_notes(vault.main_subtopic(note))  # a child's words are read with its whole subtopic
    topic = next((c for c in vault.chain(group[0]) if isinstance(c, Note) and c.kind == "topic"), None)
    start = STARTING_FROM.search(topic.body) if topic else None
    if not start or not start.group(1).strip():
        die(f"no topic above {group[0].title!r} has a **Starting from:** line, so the brief has no reader; ask the "
            "user what they knew before this topic, and add it to the topic's Scope as - **Starting from:** …")
    read = []
    for n in group:
        read += [p for p in vault.prerequisites(n) if isinstance(p, Note) and p not in group and p not in read]
    print(COLD_READ.read_text(encoding="utf-8").strip())
    print("\n## The reader\n")
    print("Starting from: " + WIKI_SHOWN.sub(r"\1", start.group(1)).strip())
    print("\nThe notes they have read:" + ("" if read else " none"))
    for p in read:
        print(f"- {p.title}: " + (WIKI_SHOWN.sub(r"\1", p.summary) or "(no summary)"))
    print("\n## The note")
    for n in group:
        print(f"\n### {n.title}\n")
        for i, line in enumerate(n.text.rstrip("\n").split("\n"), 1):
            print(f"{i}: {line}")


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
    p.add_argument("--mocs", action="store_true",
                   help="only the MOCs and topics, with their summaries, and the notes directly under a MOC")
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

    p = sub.add_parser("next", help="a topic's planned subtopics: recommended, ready, waiting, and the stubs left out")
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
    p.add_argument("--dry-run", action="store_true", help="print the diff and write nothing")
    p.set_defaults(run=cmd_mv)

    p = sub.add_parser("new", help="create a note from its template; refuses a name that is already taken",
                       epilog=ASSIGN_HELP + " source=TEXT adds TEXT as a bullet under ## Sources.")
    p.add_argument("kind", choices=list(KINDS) + ["child"],
                   help="child is a part split off the note in mocs=, from the Child template")
    p.add_argument("title")
    p.add_argument("assignments", nargs="*", metavar="key=value",
                   help="its properties, such as summary=... mocs=..., and source=TEXT for each source")
    p.add_argument("--dry-run", action="store_true", help="print the diff and write nothing")
    p.set_defaults(run=cmd_new)

    p = sub.add_parser("promote", help="make a stub or a note a topic, subtopic or note", epilog=ASSIGN_HELP)
    p.add_argument("note")
    p.add_argument("kind", choices=NOTE_TYPES)
    p.add_argument("assignments", nargs="*", metavar="key=value")
    p.add_argument("--dry-run", action="store_true", help="print the diff and write nothing")
    p.set_defaults(run=cmd_promote)

    p = sub.add_parser("set", help="set a note's properties", epilog=ASSIGN_HELP)
    p.add_argument("note")
    p.add_argument("assignments", nargs="+", metavar="key=value")
    p.add_argument("--dry-run", action="store_true", help="print the diff and write nothing")
    p.set_defaults(run=cmd_set)

    p = sub.add_parser("merge", help="fold NOTE into INTO, pointing every link at INTO, and delete NOTE")
    p.add_argument("note")
    p.add_argument("into")
    p.add_argument("--dry-run", action="store_true", help="print the diff and write nothing")
    p.add_argument("--force", action="store_true",
                   help="merge a MOC or a topic, or a written note into a stub, which merge otherwise refuses")
    p.set_defaults(run=cmd_merge)

    p = sub.add_parser("open", help="open a note in Obsidian, and print its obsidian:// link")
    p.add_argument("note")
    p.set_defaults(run=cmd_open)

    p = sub.add_parser("review", help="the wrap-up review of the notes changed since the vault's last commit")
    p.add_argument("notes", nargs="*", help="review these notes instead of the changed ones")
    p.set_defaults(run=cmd_review)

    p = sub.add_parser("commit", help="commit the vault, case-only renames included, and push it once")
    message = p.add_mutually_exclusive_group(required=True)
    message.add_argument("message", nargs="?", help="the message; -F - is safer, because the shell can't touch it")
    message.add_argument("-F", dest="file", metavar="FILE", help="read the message from FILE, or from standard input for -")
    p.set_defaults(run=cmd_commit)

    p = sub.add_parser("brief", help="the cold reader's brief for a subtopic")
    p.add_argument("note", metavar="subtopic")
    p.set_defaults(run=cmd_brief)

    # argparse leaves a key=value after an option such as --dry-run unparsed, so collect it here.
    args, extra = parser.parse_known_args(argv)
    if extra and not (hasattr(args, "assignments") and all(ASSIGNMENT.match(a) or a == "-" for a in extra)):
        parser.error("unrecognized arguments: " + " ".join(extra))
    if extra:
        args.assignments += extra
    args.run(Vault(args.vault), args)


if __name__ == "__main__":
    main()
