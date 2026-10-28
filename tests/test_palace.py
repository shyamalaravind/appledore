"""Tests for scripts/palace.py. Run: python3 -m unittest discover -s tests"""

import contextlib
import io
import subprocess
import sys
import tempfile
import textwrap
import unicodedata
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import palace  # noqa: E402


def note(summary, mocs=(), **props):
    lines = ["---", f"summary: {summary}"]
    for key, value in props.items():
        if isinstance(value, (list, tuple)):
            lines.append(f"{key}:" if value else f"{key}: []")
            lines += [f'  - "{v}"' for v in value]
        else:
            lines.append(f"{key}: {value}")
    lines.append("mocs:" if mocs else "mocs: []")
    lines += [f'  - "[[{m}]]"' for m in mocs]
    lines += ["created: 2026-10-21", "---"]
    return "\n".join(lines) + "\n"


class VaultTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "Mind palace"
        self.root.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def vault(self):
        return palace.Vault(self.root)

    def run_cli(self, *argv):
        out = io.StringIO()
        code = 0
        with contextlib.redirect_stdout(out):
            try:
                palace.main(["--vault", str(self.root), *argv])
            except SystemExit as e:
                code = e.code
        return out.getvalue(), code

    def small_vault(self):
        self.write("_-MOCs/Azure MOC.md", "---\nsummary: Azure.\ncreated: 2026-10-21\n---\n![[Children.base]]\n")
        self.write("_-MOCs/Children.base", "filters:\n  and:\n    - mocs.contains(this)\n")
        self.write("_Main Notes/Service Bus.md", note("A topic.", ["Azure MOC"], type="topic", status="learning")
                   + "## Learning graph\n%% derived %%\n- [[Old]]\n\n## Sources\n- x\n")
        self.write("_Main Notes/Queue.md", note("Queues.", ["Service Bus"], type="subtopic", builds_on=[]) + "words " * 400)
        self.write("_Main Notes/Peek-lock.md", note("Locks.", ["Service Bus"], type="subtopic", builds_on=["[[Queue]]"]) + "words " * 400)
        self.write("_Main Notes/Sessions.md", note("Sessions.", ["Service Bus"], type="subtopic", builds_on=["[[Queue]]"]) + "words " * 400)
        self.write("Stubs/AMQP.md", note("The wire protocol.", ["Queue"]))


class FrontmatterTests(unittest.TestCase):
    def test_block_and_flow_lists_and_quotes(self):
        data = palace.parse_yaml(textwrap.dedent('''\
            summary: "Start here: the maps."
            mocs:
              - "[[A MOC]]"
              - "[[B]]"
            aliases: [x, "y, z"]
            builds_on: []
            source: "" # Book, article
            created: 2025-06-19'''))
        self.assertEqual(data["summary"], "Start here: the maps.")
        self.assertEqual(data["mocs"], ["[[A MOC]]", "[[B]]"])
        self.assertEqual(data["aliases"], ["x", "y, z"])
        self.assertEqual(data["builds_on"], [])
        self.assertEqual(data["source"], "")
        self.assertEqual(data["created"], "2025-06-19")

    def test_dump_round_trips(self):
        data = {"summary": "A: b #c", "mocs": ["[[X]]"], "aliases": [], "created": "2026-01-02"}
        self.assertEqual(palace.parse_yaml(palace.dump_yaml(data)), data)


class ConvertTests(unittest.TestCase):
    def test_learning_template_note(self):
        old = ("\n**date**: 2025-06-23\n**source:** Chat gpt\n**MOCs**: [[Azure Cloud]], [[Server Less]]]]\n"
               "**tags:** #\n\n---\n\n\n\n# Summary\nText.\n")
        new = palace.convert_text(old)
        fm, body = palace.split_frontmatter(new)
        data = palace.parse_yaml(fm)
        self.assertEqual(data["mocs"], ["[[Azure Cloud]]", "[[Server Less]]"])
        self.assertEqual(data["created"], "2025-06-23")
        self.assertNotIn("tags", data)
        self.assertTrue(body.startswith("# Summary\nText."))
        self.assertIn("## Sources\n- Chat gpt", body)

    def test_variants(self):
        self.assertIn('  - "[[Front End]]"', palace.convert_text("**MOCs*: [[Front End]]\n\nThe code.\n"))
        self.assertIn("mocs: []", palace.convert_text("**date**: 2025-06-19\n**MOCs**: [[]]\n**tags:** #\n\n---\n"))
        moved = palace.convert_text('---\nReferences: "[[Web Protocols]]"\n---\n\nHTTP/2.\n')
        self.assertIn('mocs:\n  - "[[Web Protocols]]"', moved)
        self.assertNotIn("References", moved)
        self.assertNotIn("Sources", palace.convert_text('**source:** "" # Book, article\n**MOCs**: [[A]]\n'))

    def test_nothing_to_convert(self):
        self.assertIsNone(palace.convert_text("Just a body with **bold**: text.\n"))
        self.assertIsNone(palace.convert_text(note("x", ["A"])))


class QueryTests(VaultTest):
    def test_resolve_ignores_case_paths_and_code(self):
        self.small_vault()
        self.write("_Main Notes/Other.md", note("o", ["Azure MOC"], type="note")
                   + "See [[queue]], [[Stubs/AMQP|the protocol]] and `[[Not a link]]`.\n```\n[[Nor this]]\n```\n")
        v = self.vault()
        other = v.get("Other")
        names = [link.name for link in other.body_links()]
        self.assertEqual(names, ["queue", "Stubs/AMQP"])
        self.assertIs(v.resolve("queue"), v.get("Queue"))
        self.assertIs(v.resolve("Stubs/AMQP"), v.get("AMQP"))
        self.assertEqual(v.resolve("Children.base"), "_-MOCs/Children.base")

    def test_children_chain_and_kinds(self):
        self.small_vault()
        v = self.vault()
        self.assertEqual(sorted(n.title for n in v.children(v.get("Service Bus"))), ["Peek-lock", "Queue", "Sessions"])
        self.assertEqual([n.title for n in v.chain(v.get("AMQP"))], ["Queue", "Service Bus", "Azure MOC"])
        self.assertEqual(v.get("AMQP").kind, "stub")
        self.assertEqual(v.get("Azure MOC").kind, "moc")

    def test_find_matches_aliases_and_squashed_names(self):
        self.write("_Main Notes/Serverless computing.md", note("Run code.", ["X"], type="note", aliases=["Server Less"]))
        out, _ = self.run_cli("find", "serverless")
        self.assertIn("Serverless computing.md", out)
        out, _ = self.run_cli("find", "server less")
        self.assertIn("Serverless computing.md", out)

    def test_words_count_links_as_their_shown_text(self):
        self.write("_Main Notes/W.md", note("w", ["X"], type="note")
                   + "See [the docs](https://learn.microsoft.com/a/b) and [[Long target name|it]], then [[Two words]].\n"
                   + "## Sources\n- [Page](https://x.y)\n")
        self.assertEqual(self.vault().get("W").words(), 8)

    def test_words_leave_out_code(self):
        self.write("_Main Notes/C.md", note("c", ["X"], type="note")
                   + "Call `wait()` here.\n```java\nclass TaskQueue {\n    void take() {}\n}\n```\n")
        self.assertEqual(self.vault().get("C").words(), 2)

    def test_graph_draws_builds_on_and_stubs(self):
        self.small_vault()
        v = self.vault()
        lines, warnings = v.learning_graph(v.get("Service Bus"))
        self.assertEqual(lines, ["- [[Queue]]", "  - [[Peek-lock]]", "  - [[Sessions]]", "  - [[AMQP]] · stub"])
        self.assertEqual(warnings, [])

    def test_planned_stubs_sit_in_the_tree_and_next_sorts_them(self):
        self.small_vault()
        self.write("Stubs/Dead-letter.md", note("Dead letters.", ["Service Bus"], builds_on=["[[Peek-lock]]"]))
        self.write("Stubs/Replay.md", note("Replay.", ["Service Bus"], builds_on=["[[Dead-letter]]"]))
        self.write("Stubs/Topics.md", note("Topics.", ["Service Bus"], builds_on=[]))
        v = self.vault()
        lines, _ = v.learning_graph(v.get("Service Bus"))
        self.assertEqual(lines, ["- [[Queue]]", "  - [[Peek-lock]]", "    - [[Dead-letter]] · stub",
                                 "      - [[Replay]] · stub", "  - [[Sessions]]", "  - [[AMQP]] · stub",
                                 "- [[Topics]] · stub"])
        out, _ = self.run_cli("next", "Service Bus")
        self.assertIn("Service Bus: 3 subtopics written, 3 planned, 1 left out", out)
        ready = out.split("ready:")[1].split("waiting:")[0]
        self.assertIn("Dead-letter  [stub]  Dead letters.  (builds on: Peek-lock)", ready)
        self.assertIn("Topics  [stub]  Topics.  (builds on: nothing)", ready)
        self.assertIn("Replay  [stub]  Replay.  (waits for: Dead-letter)", out.split("waiting:")[1])
        self.assertIn("AMQP  [stub]  The wire protocol.  (left out by: Queue)", out.split("left out:")[1])
        self.run_cli("graph", "Service Bus", "--write")
        self.assertEqual(palace.check(self.vault()), ([], []))

    def test_next_left_out_groups_the_stubs_by_the_note_that_left_them_out(self):
        self.small_vault()
        self.write("Stubs/Batching.md", note("How do you send many messages at once?", ["Queue"]))
        self.write("Stubs/Lock renewal.md", note("How does a lock outlive its duration?", ["Peek-lock"]))
        self.write("Stubs/Topics.md", note("Topics.", ["Service Bus"], builds_on=[]))  # planned, not left out
        out, code = self.run_cli("next", "Service Bus", "--left-out")
        self.assertEqual(code, 0, out)
        link = "obsidian://open?vault=Mind%20palace&file="
        self.assertEqual(out, "Service Bus: 3 stubs left out by 2 notes\n"
                              f"- Left out by [Queue]({link}_Main%20Notes%2FQueue):\n"
                              f"  - [AMQP]({link}Stubs%2FAMQP): The wire protocol.\n"
                              f"  - [Batching]({link}Stubs%2FBatching): How do you send many messages at once?\n"
                              f"- Left out by [Peek-lock]({link}_Main%20Notes%2FPeek-lock):\n"
                              f"  - [Lock renewal]({link}Stubs%2FLock%20renewal): How does a lock outlive its duration?\n")
        (self.root / "Stubs/AMQP.md").unlink()
        (self.root / "Stubs/Batching.md").unlink()
        (self.root / "Stubs/Lock renewal.md").unlink()
        out, _ = self.run_cli("next", "Service Bus", "--left-out")
        self.assertEqual(out, "Service Bus: no stubs left out\n")

    def test_next_left_out_lists_a_stub_once_and_only_the_topics_own(self):
        self.small_vault()
        self.write("Stubs/AMQP.md", note("The wire protocol.", ["Queue", "Peek-lock"]))  # under its first parent only
        self.write("_Main Notes/Event Grid.md", note("Another topic.", ["Azure MOC"], type="topic", status="learning"))
        self.write("_Main Notes/Push delivery.md", note("Push.", ["Event Grid"], type="subtopic", builds_on=[]))
        self.write("Stubs/Webhooks.md", note("How does Event Grid call you?", ["Push delivery"]))
        out, _ = self.run_cli("next", "Service Bus", "--left-out")
        link = "obsidian://open?vault=Mind%20palace&file="
        self.assertEqual(out, "Service Bus: 1 stub left out by 1 note\n"
                              f"- Left out by [Queue]({link}_Main%20Notes%2FQueue):\n"
                              f"  - [AMQP]({link}Stubs%2FAMQP): The wire protocol.\n")

    def test_graph_write_replaces_only_its_section(self):
        self.small_vault()
        self.run_cli("graph", "Service Bus", "--write")
        text = (self.root / "_Main Notes/Service Bus.md").read_text()
        self.assertIn(palace.GRAPH_COMMENT + "\n- [[Queue]]\n  - [[Peek-lock]]", text)
        self.assertNotIn("[[Old]]", text)
        self.assertTrue(text.endswith("## Sources\n- x\n"))
        errors, warnings = palace.check(self.vault())
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])


class CheckTests(VaultTest):
    def messages(self):
        errors, warnings = palace.check(self.vault())
        return [m for _, m in errors], [m for _, m in warnings]

    def test_clean_vault(self):
        self.small_vault()
        self.run_cli("graph", "Service Bus", "--write")
        errors, warnings = self.messages()
        self.assertEqual((errors, warnings), ([], []))

    def test_defects(self):
        self.small_vault()
        self.write("_Main Notes/Empty.md", "")
        self.write("_Main Notes/Loose.md", "---\nsummary: s\ntype: note\ncreated: 2026-10-21\n---\nSee [[Missing]].\n")
        self.write("_Main Notes/A.md", note("a", ["Azure MOC"], type="note", builds_on=["[[B]]"]))
        self.write("_Main Notes/B.md", note("b", ["Azure MOC"], type="note", builds_on=["[[A]]"]))
        self.write("_Main Notes/Dup.md", note("d", ["Azure MOC"], type="note", aliases=["Queue"]))
        errors, _ = self.messages()
        self.assertTrue(any("empty file" in m for m in errors))
        self.assertTrue(any("unresolved link [[Missing]]" in m for m in errors))
        self.assertTrue(any("no mocs" in m for m in errors))
        self.assertTrue(any("builds_on cycle" in m for m in errors))
        self.assertTrue(any("alias 'Queue' is the title" in m for m in errors))

    def test_a_split_frees_words_only_as_a_new_subtopic(self):
        self.small_vault()
        self.write("_Main Notes/Session state.md", note("State.", ["Sessions"], type="subtopic", builds_on=[]) + "words " * 100)
        self.run_cli("graph", "Service Bus", "--write")
        _, warnings = self.messages()
        self.assertTrue(any("500 words across 2 note(s)" in m for m in warnings))
        self.write("_Main Notes/Session state.md", note("State.", ["Service Bus"], type="subtopic", builds_on=["[[Sessions]]"]) + "words " * 200)
        self.run_cli("graph", "Service Bus", "--write")
        self.assertEqual(self.messages(), ([], []))

    def test_style_warnings(self):
        self.small_vault()
        self.write("_-MOCs/Tiny MOC.md", "---\nsummary: t\nmocs:\n  - \"[[Azure MOC]]\"\ncreated: 2026-10-21\n---\nA definition.\n")
        self.write("_Main Notes/Chunky.md", note("c", ["Azure MOC"], type="subtopic", builds_on=[]) + "x " * 50)
        _, warnings = self.messages()
        self.assertTrue(any("never teaches" in m for m in warnings))
        self.assertTrue(any("dissolve" in m for m in warnings))
        self.assertTrue(any("subtopic's mocs is its topic" in m for m in warnings))
        self.assertTrue(any("50 words" in m for m in warnings))
        self.assertTrue(any("out of date" in m for m in warnings))


class MoveTests(VaultTest):
    def test_rename_rewrites_every_link_form(self):
        self.small_vault()
        self.write("_Main Notes/Other.md", note("o", ["Queue"], type="note")
                   + "[[Queue]], [[queue#Ordering|ordered]], ![[Queue]], [[_Main Notes/Queue]] and `[[Queue]]`.\n")
        out, code = self.run_cli("mv", "Queue", "Service Bus queue", "--alias")
        self.assertEqual(code, 0, out)
        other = (self.root / "_Main Notes/Other.md").read_text()
        self.assertIn('  - "[[Service Bus queue]]"', other)
        self.assertIn("[[Service Bus queue]], [[Service Bus queue#Ordering|ordered]], ![[Service Bus queue]], "
                      "[[Service Bus queue]] and `[[Queue]]`.", other)
        moved = self.vault().get("Service Bus queue")
        self.assertEqual(moved.aliases, ["Queue"])
        self.assertIn('  - "[[Service Bus queue]]"', (self.root / "_Main Notes/Peek-lock.md").read_text())
        self.assertFalse((self.root / "_Main Notes/Queue.md").exists())

    def test_move_to_folder_and_case_only_rename(self):
        self.small_vault()
        self.run_cli("mv", "AMQP", "_Main Notes/")
        self.assertEqual(self.vault().get("AMQP").kind, "note")
        out, code = self.run_cli("mv", "Peek-lock", "peek-lock")
        self.assertEqual(code, 0, out)
        self.assertIn("peek-lock.md", [p.name for p in (self.root / "_Main Notes").iterdir()])

    def test_refuses_a_clash(self):
        self.small_vault()
        out, code = self.run_cli("mv", "Queue", "sessions")
        self.assertEqual(code, 2)


class OpenTests(VaultTest):
    """palace open builds the commands; subprocess.run and Popen are mocked, so nothing launches."""

    LINK = "obsidian://open?vault=Mind%20palace&file=_Main%20Notes%2FPeek-lock"
    CLI_OPEN = ["obsidian", "vault=Mind palace", "open", "path=_Main Notes/Peek-lock.md"]
    HANGS = object()

    def setUp(self):
        super().setUp()
        self.small_vault()
        env = mock.patch.dict(palace.os.environ)
        env.start()
        self.addCleanup(env.stop)
        for name in ("PALACE_OPEN", "DISPLAY", "WAYLAND_DISPLAY"):
            palace.os.environ.pop(name, None)

    def open(self, outputs=None, which=("obsidian", "open", "xdg-open"), platform="darwin", name="Peek-lock"):
        """Run palace open with the given programs on PATH; outputs maps a program to its stdout, to
        None for a nonzero exit, or to HANGS for one still running at the timeout. Returns (stdout
        lines, the commands run); self.opener_kwargs holds how the system's opener was started."""
        outputs, commands = outputs or {}, []

        def result(command):
            commands.append(command)
            return outputs.get(command[1] if command[0] == "obsidian" else command[0], "")

        def fake_run(command, **kwargs):
            out = result(command)
            if out is self.HANGS:
                raise subprocess.TimeoutExpired(command, kwargs.get("timeout"))
            return subprocess.CompletedProcess(command, 1 if out is None else 0, out or "", "")

        def fake_popen(command, **kwargs):
            self.opener_kwargs = kwargs
            out, process = result(command), mock.Mock()
            if out is self.HANGS:
                process.wait.side_effect = subprocess.TimeoutExpired(command, 5)
            else:
                process.wait.return_value = 1 if out is None else 0
            return process

        with mock.patch.object(palace.shutil, "which", lambda name: f"/bin/{name}" if name in which else None), \
                mock.patch.object(palace.subprocess, "run", side_effect=fake_run), \
                mock.patch.object(palace.subprocess, "Popen", side_effect=fake_popen), \
                mock.patch.object(palace.sys, "platform", platform):
            out, code = self.run_cli("open", name)
        self.assertEqual(code, 0, out)
        return out.splitlines(), commands

    def test_the_link_is_url_encoded(self):
        self.assertEqual(palace.obsidian_uri(self.vault(), self.vault().get("Peek-lock")), self.LINK)
        root = Path(self.tmp.name) / "Notes & ideas #2"
        (root / "_Main Notes").mkdir(parents=True)
        (root / "_Main Notes/Café + tea & 100% = yes.md").write_text(note("x", ["A"], type="note"), encoding="utf-8")
        v = palace.Vault(root)
        self.assertEqual(palace.obsidian_uri(v, v.get("Café + tea & 100% = yes")),
                         "obsidian://open?vault=Notes%20%26%20ideas%20%232"
                         "&file=_Main%20Notes%2FCaf%C3%A9%20%2B%20tea%20%26%20100%25%20%3D%20yes")

    def test_the_cli_gets_the_path_obsidian_keys_the_note_by(self):
        decomposed = unicodedata.normalize("NFD", "Café")  # how some tools write é to disk
        self.write(f"_Main Notes/{decomposed}.md", note("c", ["Service Bus"], type="note"))
        _, commands = self.open({"version": "1.14.5", "vault=Mind palace": "Opened: _Main Notes/Café.md"},
                                name=decomposed)
        self.assertEqual(commands[1], ["obsidian", "vault=Mind palace", "open", "path=_Main Notes/Caf\u00e9.md"])

    def test_the_cli_first(self):
        lines, commands = self.open({"version": "1.14.5 (installer 1.14.5)",
                                     "vault=Mind palace": "Opened: _Main Notes/Peek-lock.md"})
        self.assertEqual(commands, [["obsidian", "version"], self.CLI_OPEN])
        self.assertEqual(lines, [self.LINK, "opened through the Obsidian command line interface"])

    def test_the_link_when_the_cli_is_off_missing_or_fails(self):
        off = "Command line interface is not enabled. Please turn it on in Settings > General > Advanced."
        lines, commands = self.open({"version": off})
        self.assertEqual(commands, [["obsidian", "version"], ["open", self.LINK]])
        self.assertEqual(lines, [self.LINK, "opened through the obsidian:// link"])
        _, commands = self.open({"version": "1.14.5", "vault=Mind palace": "Vault not found."})
        self.assertEqual(commands, [["obsidian", "version"], self.CLI_OPEN, ["open", self.LINK]])
        _, commands = self.open({"version": self.HANGS})
        self.assertEqual(commands, [["obsidian", "version"], ["open", self.LINK]])
        palace.os.environ["WAYLAND_DISPLAY"] = "wayland-0"
        _, commands = self.open(which=("xdg-open",), platform="linux")
        self.assertEqual(commands, [["xdg-open", self.LINK]])

    def test_the_opener_runs_detached_and_may_stay_in_the_foreground(self):
        # An app the opener starts would otherwise hold its output open until the timeout.
        palace.os.environ["DISPLAY"] = ":0"
        lines, _ = self.open({"xdg-open": self.HANGS}, which=("xdg-open",), platform="linux")
        self.assertEqual(self.opener_kwargs, {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL,
                                              "stderr": subprocess.DEVNULL, "start_new_session": True})
        self.assertEqual(lines[1], "opened through the obsidian:// link")

    def test_windows_uses_start(self):
        with mock.patch.object(palace.os, "startfile", create=True) as startfile:
            lines, commands = self.open(which=(), platform="win32")
        startfile.assert_called_once_with(self.LINK)
        self.assertEqual(lines[1], "opened through the obsidian:// link")

    def test_only_the_link_when_turned_off_or_nothing_opens(self):
        palace.os.environ["PALACE_OPEN"] = "0"
        lines, commands = self.open()
        self.assertEqual((lines, commands), ([self.LINK, "not opened: PALACE_OPEN=0"], []))
        del palace.os.environ["PALACE_OPEN"]
        lines, commands = self.open(which=("xdg-open",), platform="linux")  # no desktop
        self.assertEqual((lines, commands), ([self.LINK, "not opened: no desktop (DISPLAY and WAYLAND_DISPLAY are unset)"], []))
        palace.os.environ["DISPLAY"] = ":0"
        lines, _ = self.open(which=(), platform="linux")
        self.assertEqual(lines[0], self.LINK)
        self.assertTrue(lines[1].startswith("not opened"))
        lines, _ = self.open({"version": None, "open": None})
        self.assertTrue(lines[1].startswith("not opened"))
        with mock.patch.object(palace.os, "startfile", create=True, side_effect=OSError):
            lines, _ = self.open(which=(), platform="win32")
        self.assertTrue(lines[1].startswith("not opened"))

    def test_a_reply_that_isnt_utf_8_or_never_comes(self):
        reply = [sys.executable, "-c", "import sys; sys.stdout.buffer.write(b'Opened: \\x81')"]
        self.assertEqual(palace.try_run(reply), "Opened: \ufffd")
        self.assertIsNone(palace.try_run([sys.executable, "-c", "import time; time.sleep(10)"], timeout=0.2))


if __name__ == "__main__":
    unittest.main()
