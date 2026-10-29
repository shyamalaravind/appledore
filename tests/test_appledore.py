"""Tests for scripts/appledore.py. Run: python3 -m unittest discover -s tests"""

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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "study" / "scripts"))
import appledore  # noqa: E402


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


def shaped(words):
    """A subtopic's body with every fixed part (writing rules 8, 10 and 11), `words` words long; the
    parts themselves are 34 words."""
    return ("**In short:** " + "words " * (words - 34) + "\n**Example:** queue `orders` holds 3 messages.\n\n"
            "## In an interview\n- Say which delivery mode fits.\n\n## Left out on purpose\n"
            "- Ordering: how are messages kept in order?\n- Retries: how often is a message tried again?\n")


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
        return appledore.Vault(self.root)

    def run_cli(self, *argv):
        out = io.StringIO()
        code = 0
        with contextlib.redirect_stdout(out):
            try:
                appledore.main(["--vault", str(self.root), *argv])
            except SystemExit as e:
                code = e.code
        return out.getvalue(), code

    def small_vault(self):
        self.write("_-MOCs/Azure MOC.md", "---\nsummary: Azure.\ncreated: 2026-10-21\n---\n![[Children.base]]\n")
        self.write("_-MOCs/Children.base", "filters:\n  and:\n    - mocs.contains(this)\n")
        self.write("_Main Notes/Service Bus.md", note("A topic.", ["Azure MOC"], type="topic", status="learning")
                   + "## Learning graph\n%% derived %%\n- [[Old]]\n\n## Sources\n- x\n")
        self.write("_Main Notes/Queue.md", note("Queues.", ["Service Bus"], type="subtopic", builds_on=[]) + shaped(400))
        self.write("_Main Notes/Peek-lock.md", note("Locks.", ["Service Bus"], type="subtopic", builds_on=["[[Queue]]"]) + shaped(400))
        self.write("_Main Notes/Sessions.md", note("Sessions.", ["Service Bus"], type="subtopic", builds_on=["[[Queue]]"]) + shaped(400))
        self.write("Stubs/AMQP.md", note("The wire protocol.", ["Queue"]))


class FrontmatterTests(unittest.TestCase):
    def test_block_and_flow_lists_and_quotes(self):
        data = appledore.parse_yaml(textwrap.dedent('''\
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
        self.assertEqual(appledore.parse_yaml(appledore.dump_yaml(data)), data)


class ConvertTests(unittest.TestCase):
    def test_learning_template_note(self):
        old = ("\n**date**: 2025-06-23\n**source:** Chat gpt\n**MOCs**: [[Azure Cloud]], [[Server Less]]]]\n"
               "**tags:** #\n\n---\n\n\n\n# Summary\nText.\n")
        new = appledore.convert_text(old)
        fm, body = appledore.split_frontmatter(new)
        data = appledore.parse_yaml(fm)
        self.assertEqual(data["mocs"], ["[[Azure Cloud]]", "[[Server Less]]"])
        self.assertEqual(data["created"], "2025-06-23")
        self.assertNotIn("tags", data)
        self.assertTrue(body.startswith("# Summary\nText."))
        self.assertIn("## Sources\n- Chat gpt", body)

    def test_variants(self):
        self.assertIn('  - "[[Front End]]"', appledore.convert_text("**MOCs*: [[Front End]]\n\nThe code.\n"))
        self.assertIn("mocs: []", appledore.convert_text("**date**: 2025-06-19\n**MOCs**: [[]]\n**tags:** #\n\n---\n"))
        moved = appledore.convert_text('---\nReferences: "[[Web Protocols]]"\n---\n\nHTTP/2.\n')
        self.assertIn('mocs:\n  - "[[Web Protocols]]"', moved)
        self.assertNotIn("References", moved)
        self.assertNotIn("Sources", appledore.convert_text('**source:** "" # Book, article\n**MOCs**: [[A]]\n'))

    def test_nothing_to_convert(self):
        self.assertIsNone(appledore.convert_text("Just a body with **bold**: text.\n"))
        self.assertIsNone(appledore.convert_text(note("x", ["A"])))


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
        self.assertEqual(lines, ["- [[Queue]]", "  - [[Peek-lock]]", "  - [[Sessions]]", "  - [[AMQP]] · left out"])
        self.assertEqual(warnings, [])

    def test_planned_stubs_sit_in_the_tree_and_next_sorts_them(self):
        self.small_vault()
        self.write("Stubs/Dead-letter.md", note("Dead letters.", ["Service Bus"], builds_on=["[[Peek-lock]]"]))
        self.write("Stubs/Replay.md", note("Replay.", ["Service Bus"], builds_on=["[[Dead-letter]]"]))
        self.write("Stubs/Topics.md", note("Topics.", ["Service Bus"], builds_on=[]))
        v = self.vault()
        lines, _ = v.learning_graph(v.get("Service Bus"))
        self.assertEqual(lines, ["- [[Queue]]", "  - [[Peek-lock]]", "    - [[Dead-letter]] · stub",
                                 "      - [[Replay]] · stub", "  - [[Sessions]]", "  - [[AMQP]] · left out",
                                 "- [[Topics]] · stub"])
        out, _ = self.run_cli("next", "Service Bus")
        self.assertIn("Service Bus: 3 subtopics written, 3 planned, 1 left out", out)
        ready = out.split("ready:")[1].split("waiting:")[0]
        self.assertIn("Dead-letter  [stub]  Dead letters.  (builds on: Peek-lock)", ready)
        self.assertIn("Topics  [stub]  Topics.  (builds on: nothing)", ready)
        self.assertIn("Replay  [stub]  Replay.  (waits for: Dead-letter)", out.split("waiting:")[1])
        self.assertIn("AMQP  [stub]  The wire protocol.  (left out by: Queue)", out.split("left out:")[1])
        self.run_cli("graph", "Service Bus", "--write")
        self.assertEqual(appledore.check(self.vault()), ([], []))

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
        self.assertIn(appledore.GRAPH_COMMENT + "\n- [[Queue]]\n  - [[Peek-lock]]", text)
        self.assertNotIn("[[Old]]", text)
        self.assertTrue(text.endswith("## Sources\n- x\n"))
        errors, warnings = appledore.check(self.vault())
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])


class TreeTests(VaultTest):
    LOOSE = ("outside every chain:\n"
             "  - Loose child  [note]  _Main Notes/Loose child.md\n"
             "  - Loose  [note]  _Main Notes/Loose.md\n")

    def setUp(self):
        super().setUp()
        self.small_vault()
        self.write("_-MOCs/Messaging MOC.md", note("Messaging services.", ["Azure MOC"]) + "![[Children.base]]\n")
        self.write("_Main Notes/Event Grid.md", note("Events.", ["Messaging MOC"], type="note"))
        self.write("_Main Notes/Push delivery.md", note("Push.", ["Event Grid"], type="note"))
        self.write("_Main Notes/Compute.md", note("Run code.", ["Azure MOC"], type="note"))
        self.write("_Main Notes/Container Apps.md", note("Containers.", ["Compute", "Azure MOC"], type="note"))
        self.write("_Main Notes/Functions.md", note("Functions.", ["Compute"], type="note"))
        self.write("_Main Notes/Triggers.md", note("Triggers.", ["Functions"], type="note"))
        self.write("_Main Notes/Durable Functions.md", note("Workflows in code.", ["Functions"], type="topic", status="learning"))
        self.write("_Main Notes/Loose.md", note("Nowhere.", type="note"))
        self.write("_Main Notes/Loose child.md", note("Under Loose.", ["Loose"], type="note"))

    def test_the_whole_tree(self):
        out, _ = self.run_cli("tree")
        self.assertEqual(out, "Azure MOC  [moc]\n"
                              "  - Messaging MOC  [moc]\n"
                              "    - Event Grid  [note]\n"
                              "      - Push delivery  [note]\n"
                              "  - Compute  [note]\n"
                              "    - Container Apps  [note]\n"
                              "    - Functions  [note]\n"
                              "      - Durable Functions  [topic]\n"
                              "      - Triggers  [note]\n"
                              "  - Container Apps  [note]  (main place: Compute  [note])\n"
                              "  - Service Bus  [topic]\n"
                              "    - Peek-lock  [subtopic]\n"
                              "    - Queue  [subtopic]\n"
                              "      - AMQP  [stub]\n"
                              "    - Sessions  [subtopic]\n" + self.LOOSE)

    def test_depth_cuts_the_drawing_but_not_the_chains(self):
        # Notes below the cut-off still sit in a chain, so only the real orphans are outside one.
        out, _ = self.run_cli("tree", "--depth", "1")
        self.assertEqual(out, "Azure MOC  [moc]\n"
                              "  - Messaging MOC  [moc]\n"
                              "  - Compute  [note]\n"
                              "  - Container Apps  [note]  (main place: Compute  [note])\n"
                              "  - Service Bus  [topic]\n" + self.LOOSE)

    def test_mocs_keeps_the_mocs_the_topics_and_the_notes_directly_under_a_moc(self):
        out, _ = self.run_cli("tree", "--mocs")
        self.assertEqual(out, "Azure MOC  [moc]  Azure.\n"
                              "  - Messaging MOC  [moc]  Messaging services.\n"
                              "    - Event Grid  [note]\n"
                              "  - Compute  [note]\n"
                              "    - Functions  [note]\n"
                              "      - Durable Functions  [topic]  Workflows in code.\n"
                              "  - Container Apps  [note]  (main place: Compute  [note])\n"
                              "  - Service Bus  [topic]  A topic.\n" + self.LOOSE)

    def test_one_notes_subtree_with_summaries(self):
        out, _ = self.run_cli("tree", "Compute", "--summary")
        self.assertEqual(out, "Compute  [note]  Run code.\n"
                              "  - Container Apps  [note]  Containers.\n"
                              "  - Functions  [note]  Functions.\n"
                              "    - Durable Functions  [topic]  Workflows in code.\n"
                              "    - Triggers  [note]  Triggers.\n")


class CheckTests(VaultTest):
    def messages(self):
        errors, warnings = appledore.check(self.vault())
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
        self.write("_Main Notes/Session state.md", note("State.", ["Service Bus"], type="subtopic", builds_on=["[[Sessions]]"]) + shaped(200))
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

    def test_a_summary_past_25_words(self):
        self.small_vault()
        self.write("Stubs/Long.md", note(" ".join(["word"] * 26), ["Queue"]))
        self.write("Stubs/Linked.md", note(" ".join(["word"] * 24) + " [[Queue|it]]", ["Queue"]))  # a link counts as its shown text
        self.run_cli("graph", "Service Bus", "--write")
        self.assertEqual(self.messages(), ([], ["summary has 26 words; one sentence of at most 25"]))

    def test_subtopic_shape(self):
        self.small_vault()
        self.write("_Main Notes/Sessions.md", note("Sessions.", ["Service Bus"], type="subtopic", builds_on=["[[Queue]]"])
                   + "**In short:** one.\n\n## Locks\n- **Lock:** a.\n- **Renewal:** b.\n- **Timeout:** c, not **always**.\n"
                   + "words " * 200 + "\n\n## Left out on purpose\n- a\n- b\n- c\n- d\n- e\n")
        self.write("_Main Notes/Session state.md", note("State.", ["Sessions"], type="subtopic", builds_on=[])
                   + "- **Sticky:** e.\n")  # part of the Sessions subtopic, so its bold term counts there
        self.run_cli("graph", "Service Bus", "--write")
        shape = [m for m in self.messages()[1] if "words" not in m]
        self.assertEqual(shape, [
            "no **Example:**, ## In an interview; a subtopic opens with **In short:** and **Example:** "
            "and ends with ## In an interview and ## Left out on purpose",
            "5 topics under Left out on purpose; list 2–4",
            "5 bold terms across 2 note(s); a subtopic bolds only its new concepts, at most 3"])
        # Writing rule 10: a goal that isn't interviews names the closing section after its own use.
        topic = (self.root / "_Main Notes/Service Bus.md").read_text()
        self.write("_Main Notes/Service Bus.md", topic.replace("## Learning graph", "## Scope\n- **Goal:** run queues at work.\n\n## Learning graph"))
        self.assertIn("no **Example:**; a subtopic opens with **In short:** and **Example:** "
                      "and ends with ## In an interview and ## Left out on purpose", self.messages()[1])

    def test_children_base_only_on_a_moc_or_a_note(self):
        self.small_vault()
        topic = (self.root / "_Main Notes/Service Bus.md").read_text()
        self.write("_Main Notes/Service Bus.md", topic.replace("## Learning graph", "![[Children.base]]\n\n## Learning graph"))
        self.write("_Main Notes/Queue.md", note("Queues.", ["Service Bus"], type="subtopic", builds_on=[])
                   + shaped(400) + "\n![[Children.base]]\n")
        self.write("_Main Notes/Hub.md", note("A hub.", ["Azure MOC"], type="note") + "![[Children.base]]\n")
        self.write("_Main Notes/Spoke.md", note("Under the hub.", ["Hub"], type="note"))
        self.run_cli("graph", "Service Bus", "--write")
        self.assertEqual([m for m in self.messages()[1] if "Children.base" in m], [
            "embeds Children.base, which only a MOC or a type: note needs; its Left out list already shows its children",
            "embeds Children.base, which only a MOC or a type: note needs; its Learning graph already shows its children"])

    def test_empty_and_untitled_bases(self):
        self.small_vault()
        self.write("Stubs/Untitled.base", "")
        self.write("_-MOCs/Untitled 1.base", "views:\n  - type: table\n")
        self.write("_-MOCs/Unused.base", " \n")
        self.run_cli("graph", "Service Bus", "--write")
        out, code = self.run_cli("check")
        self.assertEqual(code, 0, out)
        self.assertIn("6 notes, 0 errors, 3 warnings\n", out)
        self.assertIn("  Stubs/Untitled.base: an empty Untitled Base: delete it\n", out)
        self.assertIn("  _-MOCs/Untitled 1.base: an Untitled Base: name it for what it lists, or delete it\n", out)
        self.assertIn("  _-MOCs/Unused.base: an empty Base: delete it\n", out)
        self.assertNotIn("Children.base:", out)

    def mentions_vault(self, body):
        self.small_vault()
        self.run_cli("graph", "Service Bus", "--write")
        self.write("Home.md", "# Home\n")
        self.write("_Main Notes/Graph.md", note("Nodes and edges.", ["Azure MOC"], type="note"))
        self.write("_Main Notes/Lock.md", note("One thread at a time.", ["Azure MOC"], type="note"))
        self.write("_Main Notes/Blocking queue.md", note("Waits while empty.", ["Azure MOC"], type="note"))
        self.write("_Main Notes/Service Bus queue.md", note("A queue in Service Bus.", ["Azure MOC"], type="note"))
        self.write("_Main Notes/Dead-letter queue.md", note("Dead letters.", ["Azure MOC"], type="note", aliases=["DLQ"]))
        self.write("_Main Notes/Message queues.md", note("Queues and their Dead-letter queue.", ["Azure MOC"], type="note")
                   + textwrap.dedent(body))
        _, warnings = appledore.check(self.vault())
        return [(rel, m) for rel, m in warnings if "never links" in m]

    def test_unlinked_mention_warns_once_at_its_first_mention(self):
        mentions = self.mentions_vault("""\
            ## Why a dead-letter queue
            - A message that keeps failing moves to the dead-letter queue.
            - The DLQ keeps it until you read it.
            - A Graph of the flow helps.
            """)
        self.assertEqual(mentions, [
            ("_Main Notes/Message queues.md", 'mentions "dead-letter queue" (line 9) but never links [[Dead-letter queue]]'),
            ("_Main Notes/Message queues.md", 'mentions "Graph" (line 11) but never links [[Graph]]'),
        ])

    def test_an_alias_counts_and_the_longest_name_wins(self):
        mentions = self.mentions_vault("""\
            - The DLQ keeps a message that keeps failing.
            - Each Service Bus queue has its own.
            """)
        self.assertEqual(mentions, [
            ("_Main Notes/Message queues.md", 'mentions "DLQ" (line 8) but never links [[Dead-letter queue]]'),
            ("_Main Notes/Message queues.md", 'mentions "Service Bus queue" (line 9) but never links [[Service Bus queue]]'),
        ])

    def test_hyphenated_compounds_dont_name_a_note(self):
        mentions = self.mentions_vault("""\
            - Lock-free code needs a non-blocking queue.
            - A message that keeps failing moves to the dead-letter queue.
            """)
        self.assertEqual(mentions, [
            ("_Main Notes/Message queues.md", 'mentions "dead-letter queue" (line 9) but never links [[Dead-letter queue]]'),
        ])

    def test_linked_mentions_code_and_common_words_dont_warn(self):
        mentions = self.mentions_vault("""\
            - A message that keeps failing moves to the [[Dead-letter queue|DLQ]]; read the dead-letter queue daily.
            - Message queues sit under the Azure MOC; `Queue` and [Peek-lock docs](https://x.y/Peek-lock) aren't mentions.
            - Draw the flow as a graph, as https://x.y/Graph does. %% Graph %%
            - ![[Lock]]
            - A Lock blocks; Home lists every topic.
            ```
            Sessions and AMQP
            ```

            ## Sources
            - The Peek-lock page
            """)
        self.assertEqual(mentions, [])


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
        self.write("_Main Notes/Topics.md", note("Topics.", ["Queue"], type="note"))
        self.run_cli("mv", "Topics", "Stubs/")
        self.assertEqual(self.vault().get("Topics").kind, "stub")
        out, code = self.run_cli("mv", "Peek-lock", "peek-lock")
        self.assertEqual(code, 0, out)
        self.assertIn("peek-lock.md", [p.name for p in (self.root / "_Main Notes").iterdir()])

    def test_refuses_a_move_that_check_would_reject(self):
        # A stub in _Main Notes/ has no type: appledore promote is the way to make it a written note.
        self.small_vault()
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            out, code = self.run_cli("mv", "AMQP", "_Main Notes/")
            self.assertEqual(self.run_cli("mv", "Queue", ".Queue")[1], 2)
        self.assertEqual(code, 2, out)
        self.assertIn("a stub becomes a written note with appledore promote 'AMQP'", err.getvalue())
        self.assertIn("can't start with a dot", err.getvalue())
        self.assertTrue((self.root / "Stubs/AMQP.md").exists())

    def test_refuses_a_clash(self):
        self.small_vault()
        out, code = self.run_cli("mv", "Queue", "sessions")
        self.assertEqual(code, 2)


TEMPLATES = Path(__file__).resolve().parent / "templates"  # the vault's templates, kept apart from the evals' fixture
NOW = appledore.datetime.datetime(2026, 10, 29, 9, 30)


class WriteTest(VaultTest):
    """A small vault with the vault's own templates, which the write commands fill in, and a clock
    that stands still."""

    def setUp(self):
        super().setUp()
        self.small_vault()
        for template in TEMPLATES.iterdir():
            self.write(f"__templates/{template.name}", template.read_text(encoding="utf-8"))
        self.run_cli("graph", "Service Bus", "--write")
        clock = mock.patch.object(appledore, "now", lambda: NOW)
        clock.start()
        self.addCleanup(clock.stop)

    def run_err(self, *argv, stdin=""):
        """Run the command line with stdin, as UTF-8, on its standard input, which reports cp1252, as
        a pipe does on Windows; return (stdout, stderr, exit code)."""
        err = io.StringIO()
        pipe = io.TextIOWrapper(io.BytesIO(stdin.encode("utf-8")), encoding="cp1252")
        with contextlib.redirect_stderr(err), mock.patch.object(appledore.sys, "stdin", pipe):
            out, code = self.run_cli(*argv)
        return out, err.getvalue(), code

    def read(self, rel):
        return (self.root / rel).read_text(encoding="utf-8")

    def snapshot(self):
        """Every file in the vault, and its bytes."""
        return {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}

    def assertClean(self):
        errors, _ = appledore.check(self.vault())
        self.assertEqual(errors, [])

    def assertRefused(self, argv, message, stdin=""):
        before = self.snapshot()
        out, err, code = self.run_err(*argv, stdin=stdin)
        self.assertEqual(code, 2, (argv, out))
        self.assertIn(message, err, argv)
        self.assertEqual(self.snapshot(), before, argv)


class NewTests(WriteTest):
    def test_a_stub_from_the_template_with_values_from_stdin(self):
        # A quoted heredoc passes $ and backticks, which the shell would expand inside double quotes.
        out, err, code = self.run_err("new", "stub", "Dead-letter queue", "-", "mocs=Service Bus", stdin=(
            "summary=Where a message goes after `maxDeliveryCount` tries, at $0.\n"
            "builds_on=[[Peek-lock]]\nbuilds_on=queue\n\n"
            "source=[Dead-letter queues](https://learn.microsoft.com/dlq)\nsource+=- [Settling](https://x.y/settle)\n"))
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "created Stubs/Dead-letter queue.md\n"
                              "redrew the learning graph in _Main Notes/Service Bus.md\n")
        self.assertEqual(self.read("Stubs/Dead-letter queue.md"),
                         "---\nsummary: Where a message goes after `maxDeliveryCount` tries, at $0.\n"
                         'mocs:\n  - "[[Service Bus]]"\nbuilds_on:\n  - "[[Peek-lock]]"\n  - "[[Queue]]"\n'
                         'aliases: []\ncreated: "2026-10-29"\n---\n## Sources\n'
                         "- [Dead-letter queues](https://learn.microsoft.com/dlq)\n- [Settling](https://x.y/settle)\n")
        self.assertIn("    - [[Dead-letter queue]] · stub", self.read("_Main Notes/Service Bus.md"))
        self.assertClean()

    def test_stdin_is_utf_8_and_a_dash_must_read_something(self):
        out, err, code = self.run_err("set", "Queue", "-", stdin="summary=A cache in a café keeps a copy — for an hour.\n")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.vault().get("Queue").summary, "A cache in a café keeps a copy — for an hour.")
        self.assertRefused(["set", "Queue", "-"], "read no key=value line", stdin="\n")

    def test_a_child_from_the_child_template(self):
        out, code = self.run_cli("new", "child", "Session state", "summary=State kept per session.", "mocs=Sessions",
                                 "source=[State](https://x.y/state)")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.read("_Main Notes/Session state.md"),
                         '---\nsummary: State kept per session.\ntype: subtopic\nmocs:\n  - "[[Sessions]]"\n'
                         'builds_on: []\naliases: []\ncreated: "2026-10-29"\n---\n\n\n'
                         "## Sources\n- [State](https://x.y/state)\n")
        self.write("_Main Notes/Hub.md", note("A hub.", ["Azure MOC"], type="note"))
        self.run_cli("new", "child", "Spoke", "summary=Part of the hub.", "mocs=Hub")
        self.assertIn("type: note\nmocs:\n", self.read("_Main Notes/Spoke.md"))
        # A planned stub is a subtopic still being written, so its part is a subtopic too.
        self.write("Stubs/Topics.md", note("Topics.", ["Service Bus"], builds_on=["[[Queue]]"]))
        self.run_cli("new", "child", "Subscriptions", "summary=Where a topic's copies wait.", "mocs=Topics")
        self.assertIn("type: subtopic\n", self.read("_Main Notes/Subscriptions.md"))
        self.assertClean()

    def test_a_topic_and_a_moc(self):
        out, code = self.run_cli("new", "moc", "Messaging MOC", "summary=Messaging services.", "mocs=Azure MOC")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.read("_-MOCs/Messaging MOC.md"), "---\nsummary: Messaging services.\nmocs:\n"
                                                               '  - "[[Azure MOC]]"\ncreated: "2026-10-29"\n---\n![[Children.base]]\n')
        out, code = self.run_cli("new", "topic", "Event Grid", "summary=Events pushed to handlers.", "mocs=Messaging MOC",
                                 "builds_on=Service Bus")
        self.assertEqual(code, 0, out)
        text = self.read("_Main Notes/Event Grid.md")
        self.assertIn("type: topic\nstatus: learning\nmocs:\n", text)
        self.assertIn("## Learning graph\n" + appledore.GRAPH_COMMENT, text)
        self.assertNotIn("{{", text)
        self.assertClean()

    def test_refuses_a_name_that_is_taken(self):
        self.write("_Main Notes/Topics.md", note("Topics.", ["Service Bus"], type="note", aliases=["Pub-sub"]))
        decomposed = unicodedata.normalize("NFD", "Café cache")  # how some tools write é to disk
        self.write(f"Stubs/{decomposed}.md", note("A cache in a café.", ["Queue"]))
        for title, message in (("peek lock", "already a note: _Main Notes/Peek-lock.md"),
                               ("pub sub", "already an alias of a note: _Main Notes/Topics.md"),
                               ("Café cache", "already a note: Stubs/Café cache.md")):
            self.assertRefused(["new", "stub", title, "summary=s.", "mocs=Queue"], message)

    def test_never_overwrites_a_file(self):
        self.write("Stubs/Kept.md", "kept\n")
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            appledore.write_note(self.root / "Stubs/Kept.md", "new\n", create=True)
        self.assertEqual(self.read("Stubs/Kept.md"), "kept\n")
        appledore.write_note(self.root / "Stubs/Kept.md", "swapped\n")
        self.assertEqual(self.read("Stubs/Kept.md"), "swapped\n")
        self.assertEqual(sorted(p.name for p in (self.root / "Stubs").iterdir()), ["AMQP.md", "Kept.md"])

    def test_refuses_what_check_would_reject(self):
        for argv, message in ((["topic", "DNS", "summary=s.", "mocs=Azure MOC", "status="], "DNS.md: missing status"),
                              (["stub", "Resolver", "summary=s.", "mocs=Queue", "created="], "Resolver.md: missing created"),
                              (["stub", "X", "mocs=Queue"], "X.md: missing summary"),
                              (["stub", "X", "summary=s."], "X.md: no mocs"),
                              (["stub", "X", "summary=s.", "mocs=Queue", "aliases=Sessions"], "alias 'Sessions' is the title"),
                              (["stub", "X", "summary=s.", "mocs=Missing"], "no note named 'Missing'"),
                              (["moc", "Messaging", "summary=s."], "ends in ' MOC'"),
                              (["stub", "A/B", "summary=s.", "mocs=Queue"], "a title can't hold"),
                              (["note", ".NET", "summary=s.", "mocs=Queue"], "can't start with a dot"),
                              (["note", "X", "summary=s.", "mocs=Queue", "type=topic"], "the kind sets the type"),
                              (["stub", "X", "summary=s.", "mocs=Queue", "colour=red"], "unknown property 'colour'")):
            self.assertRefused(["new", *argv], message)

    def test_names_a_close_spelling(self):
        out, code = self.run_cli("new", "stub", "Queues", "summary=s.", "mocs=Queue")
        self.assertEqual(code, 0, out)
        self.assertIn("names already close to it: Queue (_Main Notes/Queue.md)", out)

    def test_dry_run_prints_the_diff_and_writes_nothing(self):
        before = self.snapshot()
        out, code = self.run_cli("new", "stub", "Topics", "--dry-run", "summary=Fan-out.", "mocs=Service Bus")
        self.assertEqual(code, 0, out)
        self.assertTrue(out.startswith("dry run, so nothing was written:\ncreated Stubs/Topics.md\n"
                                       "redrew the learning graph in _Main Notes/Service Bus.md\n"), out)
        self.assertIn("--- /dev/null\n+++ b/Stubs/Topics.md\n", out)
        self.assertIn("+- [[Topics]] · stub\n", out)
        self.assertEqual(self.snapshot(), before)

    def test_fills_obsidians_placeholders(self):
        self.assertEqual(appledore.fill_template("{{title}} {{date}} {{date:DD/MM/YY}} {{ time }} {{time:HH:mm:ss}} "
                                                 "{{content}}|{{fromTitle}}|100%", "Note", NOW, {"fromTitle": "Hub"}),
                         "Note 2026-10-29 29/10/26 09:30 09:30:00 |Hub|100%")
        for fmt in ("dddd, MMMM Do YYYY", "YYYY-MM-DD[T]HH"):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                appledore.fill_template("{{date:%s}}" % fmt, "Note", NOW)


class PromoteTests(WriteTest):
    def test_a_stub_becomes_a_subtopic(self):
        self.write("Stubs/Dead-letter.md", '---\nsummary: Dead letters.\nmocs:\n  - "[[Service Bus]]"\n'
                                           'builds_on: ["[[Peek-lock]]"]\ncreated: "2026-10-21"\n---\n'
                                           "## Sources\n- [DLQ](https://x.y/dlq)\n  - part 2\n")
        self.write("_Main Notes/Other.md", note("o", ["Azure MOC"], type="note")
                   + "| a | [[Stubs/Dead-letter\\|it]] |\n\n[[dead-letter]] stays as written.\n")
        self.run_cli("graph", "Service Bus", "--write")
        out, code = self.run_cli("promote", "Dead-letter", "subtopic")
        self.assertEqual(code, 0, out)
        self.assertEqual(out, "Stubs/Dead-letter.md → _Main Notes/Dead-letter.md: now a subtopic\n"
                              "redrew the learning graph in _Main Notes/Service Bus.md\n")
        self.assertFalse((self.root / "Stubs/Dead-letter.md").exists())
        self.assertEqual(self.read("_Main Notes/Dead-letter.md"),
                         '---\nsummary: Dead letters.\ntype: subtopic\nmocs:\n  - "[[Service Bus]]"\n'
                         'builds_on: ["[[Peek-lock]]"]\naliases: []\ncreated: "2026-10-21"\n---\n'
                         "**In short:**\n\n**Example:**\n\n## In an interview\n-\n\n## Left out on purpose\n-\n\n"
                         "## Sources\n- [DLQ](https://x.y/dlq)\n  - part 2\n")
        self.assertIn("| a | [[Dead-letter\\|it]] |\n\n[[dead-letter]] stays as written.", self.read("_Main Notes/Other.md"))
        self.assertIn("  - [[Dead-letter]]\n", self.read("_Main Notes/Service Bus.md"))
        self.assertClean()

    def test_a_stub_keeps_the_text_written_into_it(self):
        self.write("Stubs/Dead-letter.md", note("Dead letters.", ["Service Bus"], builds_on=["[[Peek-lock]]"])
                   + shaped(200) + "\n## Sources\n- [DLQ](https://x.y/dlq)\n")
        out, err, code = self.run_err("promote", "Dead-letter", "subtopic", "-",
                                      stdin="summary=A message that keeps failing waits in the dead-letter queue.\n")
        self.assertEqual(code, 0, err)
        text = self.read("_Main Notes/Dead-letter.md")
        self.assertIn("summary: A message that keeps failing waits in the dead-letter queue.\ntype: subtopic\n", text)
        self.assertTrue(text.endswith("---\n" + shaped(200) + "\n## Sources\n- [DLQ](https://x.y/dlq)\n"), text)

    def test_a_note_keeps_its_body(self):
        self.write("_Main Notes/Topics.md", note("Topics.", ["Azure MOC"], type="note") + "Fan-out to subscriptions.\n")
        out, code = self.run_cli("promote", "Topics", "subtopic", "mocs=Service Bus", "builds_on=Queue")
        self.assertEqual(code, 0, out)
        text = self.read("_Main Notes/Topics.md")
        self.assertIn('type: subtopic\nmocs:\n  - "[[Service Bus]]"\nbuilds_on:\n  - "[[Queue]]"\n', text)
        self.assertTrue(text.endswith("---\nFan-out to subscriptions.\n"))
        self.assertIn("  - [[Topics]]", self.read("_Main Notes/Service Bus.md"))

    def test_never_replaces_another_note(self):
        self.write("_Main Notes/Vary header.md", note("Written.", ["Service Bus"], type="note") + "Text.\n")
        self.write("Stubs/Vary header.md", note("A stub.", ["Queue"]))
        self.write("Stubs/sessions.md", note("A stub named like a note but for its case.", ["Queue"]))
        self.assertRefused(["promote", "Stubs/Vary header", "subtopic"], "'Vary header' already exists: _Main Notes/Vary header.md")
        self.assertRefused(["promote", "Stubs/sessions", "note"], "'sessions' already exists: _Main Notes/Sessions.md")

    def test_refuses_a_moc(self):
        self.assertRefused(["promote", "Azure MOC", "topic"], "only a stub or a note")


class SetTests(WriteTest):
    def test_lists_and_values(self):
        self.write("_Main Notes/Topics.md", '---\nsummary: Topics.  # fan-out\ntype: note\nmocs: ["[[Azure MOC]]"]\n'
                                            'aliases:\n  - Pub-sub\ncreated: "2026-10-21"\n---\nBody stays.\n')
        out, code = self.run_cli("set", "Topics", "builds_on=Queue", "builds_on=[[Sessions|s]]", "aliases+=Fan-out",
                                 "aliases-=pub sub")
        self.assertEqual(code, 0, out)
        self.assertEqual(out, "_Main Notes/Topics.md: set builds_on, aliases\n")
        self.assertEqual(self.read("_Main Notes/Topics.md"),
                         '---\nsummary: Topics.  # fan-out\ntype: note\nmocs: ["[[Azure MOC]]"]\n'
                         'builds_on:\n  - "[[Queue]]"\n  - "[[Sessions]]"\naliases:\n  - Fan-out\n'
                         'created: "2026-10-21"\n---\nBody stays.\n')
        out, _ = self.run_cli("set", "Topics", "builds_on-=sessions", "type=subtopic", "mocs=Service Bus", "aliases=")
        self.assertIn("redrew the learning graph in _Main Notes/Service Bus.md", out)
        text = self.read("_Main Notes/Topics.md")
        self.assertIn('type: subtopic\nmocs:\n  - "[[Service Bus]]"\nbuilds_on:\n  - "[[Queue]]"\naliases: []\n', text)
        self.run_cli("set", "Service Bus", "--dry-run", "status=done")
        self.assertIn("\nstatus: learning\n", self.read("_Main Notes/Service Bus.md"))
        self.run_cli("set", "Service Bus", "status=done")
        self.assertIn("\nstatus: done\n", self.read("_Main Notes/Service Bus.md"))
        out, _ = self.run_cli("set", "Service Bus", "status=done")
        self.assertEqual(out, "_Main Notes/Service Bus.md: already set\n")

    def test_an_empty_value_removes_a_property(self):
        self.run_cli("set", "Queue", "aliases+=FIFO", "url=https://x.y/queues")
        self.assertEqual(self.vault().get("Queue").fm["url"], "https://x.y/queues")
        self.run_cli("set", "Queue", "url=", "aliases=")
        self.assertNotIn("url", self.vault().get("Queue").fm)
        self.assertEqual(self.vault().get("Queue").fm["aliases"], [])

    def test_refuses_what_check_would_reject(self):
        self.write("_Main Notes/Topics.md", note("Topics.", ["Azure MOC"], type="note"))
        for argv, message in ((["Topics", "mocs=Missing"], "no note named 'Missing'"),
                              (["Topics", "builds_on=Topics"], "builds_on cycle: Topics → Topics"),
                              (["Topics", "aliases+=queue"], "alias 'queue' is the title of _Main Notes/Queue.md"),
                              (["Topics", "type=hub"], "type must be one of topic, subtopic, note"),
                              (["Topics", "summary="], "missing summary"),
                              (["Service Bus", "status=finished"], "status must be one of done, learning"),
                              (["Topics", "summary+=more"], "summary holds one value"),
                              (["Topics", "builds_on-=Queue"], "isn't in builds_on"),
                              (["Topics", "summary"], "isn't key=value"),
                              (["Topics", "source=[x](https://x.y)"], "only to a new note"),
                              (["AMQP", "type=note"], "appledore promote")):
            self.assertRefused(["set", *argv], message)

    def test_an_error_the_note_already_had_is_not_blamed_on_the_write(self):
        # Each write moves an unresolved link the vault already had to another line, or, for the
        # merge, into the note kept; neither adds an error, so both go ahead.
        self.write("_Main Notes/URL.md", note("A web address.", ["Azure MOC"], type="note") + "See [[Percent-encoding]].\n")
        out, err, code = self.run_err("set", "URL", "aliases+=URI")
        self.assertEqual(code, 0, err)
        self.write("_Main Notes/Topics.md", note("Topics.", ["Azure MOC"], type="note") + "Fan-out.\n\n## Sources\n- [[Gone]]\n")
        out, err, code = self.run_err("merge", "URL", "Topics")
        self.assertEqual(code, 0, err)
        errors, _ = appledore.check(self.vault())
        self.assertEqual(sorted((rel, appledore.LINE_NUMBER.sub("", m)) for rel, m in errors),
                         [("_Main Notes/Topics.md", "unresolved link [[Gone]] ()"),
                          ("_Main Notes/Topics.md", "unresolved link [[Percent-encoding]] ()")])
        self.assertRefused(["set", "Topics", "builds_on=[[Gone]]"], "no note named 'Gone'")

    def test_lines_it_cant_parse_stay(self):
        self.write("_Main Notes/URL.md", '---\n# kept\nsummary: Old.\ndate modified: 2026-10-01\ntype: note\n'
                                         'reading.time: 3\n"quoted key": x\nmocs:\n  - "[[Azure MOC]]"\n'
                                         'created: "2026-10-21"\n---\nBody\n')
        out, code = self.run_cli("set", "URL", "summary=New.", "mocs=Queue", "aliases+=URI", "status=")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.read("_Main Notes/URL.md"),
                         '---\n# kept\nsummary: New.\ndate modified: 2026-10-01\ntype: note\nreading.time: 3\n'
                         '"quoted key": x\nmocs:\n  - "[[Queue]]"\naliases:\n  - URI\ncreated: "2026-10-21"\n---\nBody\n')
        text = '---\nsummary: >-\n  Folded\n  text.\ncreated: "2026-01-02"\nlocal: x\n---\nBody'
        self.assertEqual(appledore.set_frontmatter(text, {"summary": "New.", "mocs": ["[[A]]"], "local": appledore.DELETE}),
                         '---\nsummary: New.\nmocs:\n  - "[[A]]"\ncreated: "2026-01-02"\n---\nBody')
        self.assertEqual(appledore.set_frontmatter("Body\n", {"tags": []}), "---\ntags: []\n---\nBody\n")


class MergeTests(WriteTest):
    def test_links_names_and_prerequisites_move_to_the_note_kept(self):
        self.write("Stubs/Dead-letter.md", note("Dead letters.", ["Service Bus"], builds_on=["[[Peek-lock]]"], aliases=["DLQ"]))
        self.write("_Main Notes/Poison messages.md", note("Messages that keep failing.", ["Azure MOC"], type="note",
                                                          builds_on=["[[Queue]]"]))
        self.write("_Main Notes/Other.md", note("o", ["Dead-letter"], type="note",
                                                builds_on=["[[Dead-letter]]", "[[Poison messages]]"])
                   + "See [[Dead-letter]], [[Stubs/Dead-letter#Why|why]] and ![[Dead-letter]].\n"
                   + "| a | [[Dead-letter]] |\n")
        self.run_cli("graph", "Service Bus", "--write")
        out, code = self.run_cli("merge", "Dead-letter", "Poison messages")
        self.assertEqual(code, 0, out)
        # Six links in Other, and one in the learning graph, which is then redrawn.
        self.assertEqual(out, "merged Stubs/Dead-letter.md into _Main Notes/Poison messages.md: 7 link(s) in 2 note(s) "
                              "now point at 'Poison messages', which takes 'Dead-letter' as an alias; "
                              "Stubs/Dead-letter.md is deleted\n"
                              "its summary and text sit under '## Merged from Dead-letter' in "
                              "_Main Notes/Poison messages.md: fold them in\n"
                              "not kept from 'Dead-letter': mocs: [[Service Bus]]; created: 2026-10-21\n"
                              "redrew the learning graph in _Main Notes/Service Bus.md\n")
        self.assertFalse((self.root / "Stubs/Dead-letter.md").exists())
        kept = self.vault().get("Poison messages")
        self.assertEqual(kept.aliases, ["Dead-letter", "DLQ"])
        self.assertEqual(kept.values("builds_on"), ["[[Queue]]", "[[Peek-lock]]"])
        self.assertEqual(kept.values("mocs"), ["[[Azure MOC]]"])
        self.assertTrue(kept.text.endswith("---\n\n## Merged from Dead-letter\nSummary: Dead letters.\n"), kept.text)
        other = self.read("_Main Notes/Other.md")
        self.assertIn('mocs:\n  - "[[Poison messages]]"\n', other)
        self.assertIn('builds_on:\n  - "[[Poison messages]]"\n', other)  # listed once
        self.assertIn("See [[Poison messages|Dead-letter]], [[Poison messages#Why|why]] and ![[Poison messages]].\n"
                      "| a | [[Poison messages\\|Dead-letter]] |", other)
        self.assertNotIn("Dead-letter]]", self.read("_Main Notes/Service Bus.md"))
        self.assertClean()

    def test_its_summary_text_and_sources_are_kept(self):
        self.write("_Main Notes/Topics.md", note("Topics.", ["Azure MOC"], type="note")
                   + "Fan-out to [[Topics|them]].\n\n## Sources\n- [Topics](https://x.y/topics)\n  - part 2\n"
                   + "- [Queues](https://x.y/q)\n")
        self.write("_Main Notes/Pub-sub.md", note("Pub-sub.", ["Azure MOC"], type="note")
                   + "One sender, many readers.\n\n## Sources\n- [Queues](https://x.y/q)\n")
        out, code = self.run_cli("merge", "Topics", "Pub-sub")
        self.assertEqual(code, 0, out)
        text = self.read("_Main Notes/Pub-sub.md")
        self.assertTrue(text.endswith("---\nOne sender, many readers.\n\n## Merged from Topics\nSummary: Topics.\n\n"
                                      "Fan-out to [[Pub-sub|them]].\n\n## Sources\n- [Queues](https://x.y/q)\n"
                                      "- [Topics](https://x.y/topics)\n  - part 2\n"), text)
        _, warnings = appledore.check(self.vault())
        self.assertIn(("_Main Notes/Pub-sub.md", "'## Merged from Topics' still holds text appledore merge moved in: "
                                                 "fold it into the note and delete that heading"), warnings)

    def test_refuses_a_merge_that_loses_a_place(self):
        self.write("_-MOCs/Messaging MOC.md", note("Messaging.", ["Azure MOC"]))
        for argv, message in ((["Sessions", "AMQP"], "'AMQP' is a stub and 'Sessions' is a written subtopic"),
                              (["Queue", "AMQP", "--force"], "'AMQP' sits only under 'Queue'"),
                              (["Service Bus", "Queue"], "'Service Bus' is a topic"),
                              (["Messaging MOC", "Azure MOC"], "'Messaging MOC' is a moc"),
                              (["Queue", "queue"], "can't merge into itself")):
            self.assertRefused(["merge", *argv], message)
        self.write("Stubs/Ordering.md", note("Ordering.", ["Peek-lock"]))
        out, err, code = self.run_err("merge", "Sessions", "Ordering", "--force")
        self.assertEqual(code, 0, err)

    def test_dry_run_lists_every_change(self):
        before = self.snapshot()
        out, code = self.run_cli("merge", "Sessions", "Peek-lock", "--dry-run")
        self.assertEqual(code, 0, out)
        self.assertTrue(out.startswith("dry run, so nothing was written:\n"
                                       "merged _Main Notes/Sessions.md into _Main Notes/Peek-lock.md"), out)
        self.assertIn("not kept from 'Sessions': type: subtopic; created: 2026-10-21\n", out)
        self.assertIn("+++ b/_Main Notes/Peek-lock.md\n", out)
        self.assertIn("+++ b/_Main Notes/Service Bus.md\n", out)
        self.assertIn("delete _Main Notes/Sessions.md\n", out)
        self.assertEqual(self.snapshot(), before)


class GraphRedrawTests(WriteTest):
    def setUp(self):
        super().setUp()
        topic = self.read("_Main Notes/Service Bus.md")
        self.write("_Main Notes/Service Bus.md", topic.replace("## Sources", "### Reading order\nQueues first.\n\n## Sources"))
        self.write("Stubs/Topics.md", note("Topics.", ["Service Bus"], builds_on=["[[Queue]]"]))  # so its graph is stale
        self.write("_Main Notes/Event Grid.md", note("Done, with nothing to draw.", ["Azure MOC"], type="topic", status="done"))
        self.write("_Main Notes/Loose.md", note("In no graph.", ["Azure MOC"], type="note"))

    def test_check_writes_nothing(self):
        before = self.snapshot()
        out, code = self.run_cli("check")
        self.assertEqual(code, 0, out)
        self.assertIn("_Main Notes/Service Bus.md: the learning graph is out of date", out)
        self.assertEqual(self.snapshot(), before)

    def test_a_write_redraws_only_the_topics_it_touches(self):
        topics = {rel: self.read(rel) for rel in ("_Main Notes/Service Bus.md", "_Main Notes/Event Grid.md")}
        out, code = self.run_cli("set", "Loose", "summary=Still in no graph.")
        self.assertEqual((code, out), (0, "_Main Notes/Loose.md: set summary\n"))
        self.assertEqual({rel: self.read(rel) for rel in topics}, topics)
        out, code = self.run_cli("set", "Topics", "summary=Fan-out to subscriptions.")
        self.assertEqual(code, 0, out)
        self.assertIn("redrew the learning graph in _Main Notes/Service Bus.md", out)
        text = self.read("_Main Notes/Service Bus.md")
        self.assertIn("  - [[Topics]] · stub\n", text)
        self.assertIn("· left out\n\n### Reading order\nQueues first.\n\n## Sources", text)
        self.assertEqual(self.read("_Main Notes/Event Grid.md"), topics["_Main Notes/Event Grid.md"])

    def test_mv_redraws_the_order(self):
        out, _ = self.run_cli("mv", "Sessions", "Batching")
        self.assertIn("redrew the learning graph", out)
        self.assertIn("- [[Queue]]\n  - [[Batching]]\n  - [[Peek-lock]]", self.read("_Main Notes/Service Bus.md"))


class OpenTests(VaultTest):
    """appledore open builds the commands; subprocess.run and Popen are mocked, so nothing launches."""

    LINK = "obsidian://open?vault=Mind%20palace&file=_Main%20Notes%2FPeek-lock"
    CLI_OPEN = ["obsidian", "vault=Mind palace", "open", "path=_Main Notes/Peek-lock.md"]
    HANGS = object()

    def setUp(self):
        super().setUp()
        self.small_vault()
        env = mock.patch.dict(appledore.os.environ)
        env.start()
        self.addCleanup(env.stop)
        for name in ("APPLEDORE_OPEN", "PALACE_OPEN", "DISPLAY", "WAYLAND_DISPLAY"):
            appledore.os.environ.pop(name, None)

    def open(self, outputs=None, which=("obsidian", "open", "xdg-open"), platform="darwin", name="Peek-lock"):
        """Run appledore open with the given programs on PATH; outputs maps a program to its stdout, to
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

        with mock.patch.object(appledore.shutil, "which", lambda name: f"/bin/{name}" if name in which else None), \
                mock.patch.object(appledore.subprocess, "run", side_effect=fake_run), \
                mock.patch.object(appledore.subprocess, "Popen", side_effect=fake_popen), \
                mock.patch.object(appledore.sys, "platform", platform):
            out, code = self.run_cli("open", name)
        self.assertEqual(code, 0, out)
        return out.splitlines(), commands

    def test_the_link_is_url_encoded(self):
        self.assertEqual(appledore.obsidian_uri(self.vault(), self.vault().get("Peek-lock")), self.LINK)
        root = Path(self.tmp.name) / "Notes & ideas #2"
        (root / "_Main Notes").mkdir(parents=True)
        (root / "_Main Notes/Café + tea & 100% = yes.md").write_text(note("x", ["A"], type="note"), encoding="utf-8")
        v = appledore.Vault(root)
        self.assertEqual(appledore.obsidian_uri(v, v.get("Café + tea & 100% = yes")),
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
        appledore.os.environ["WAYLAND_DISPLAY"] = "wayland-0"
        _, commands = self.open(which=("xdg-open",), platform="linux")
        self.assertEqual(commands, [["xdg-open", self.LINK]])

    def test_the_opener_runs_detached_and_may_stay_in_the_foreground(self):
        # An app the opener starts would otherwise hold its output open until the timeout.
        appledore.os.environ["DISPLAY"] = ":0"
        lines, _ = self.open({"xdg-open": self.HANGS}, which=("xdg-open",), platform="linux")
        self.assertEqual(self.opener_kwargs, {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL,
                                              "stderr": subprocess.DEVNULL, "start_new_session": True})
        self.assertEqual(lines[1], "opened through the obsidian:// link")

    def test_windows_uses_start(self):
        with mock.patch.object(appledore.os, "startfile", create=True) as startfile:
            lines, commands = self.open(which=(), platform="win32")
        startfile.assert_called_once_with(self.LINK)
        self.assertEqual(lines[1], "opened through the obsidian:// link")

    def test_only_the_link_when_turned_off_or_nothing_opens(self):
        appledore.os.environ["APPLEDORE_OPEN"] = "0"
        lines, commands = self.open()
        self.assertEqual((lines, commands), ([self.LINK, "not opened: APPLEDORE_OPEN=0"], []))
        del appledore.os.environ["APPLEDORE_OPEN"]
        appledore.os.environ["PALACE_OPEN"] = "0"  # the old name, read with a notice until the next version
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            lines, commands = self.open()
        self.assertEqual((lines, commands), ([self.LINK, "not opened: APPLEDORE_OPEN=0"], []))
        self.assertIn("PALACE_OPEN is now APPLEDORE_OPEN", err.getvalue())
        del appledore.os.environ["PALACE_OPEN"]
        lines, commands = self.open(which=("xdg-open",), platform="linux")  # no desktop
        self.assertEqual((lines, commands), ([self.LINK, "not opened: no desktop (DISPLAY and WAYLAND_DISPLAY are unset)"], []))
        appledore.os.environ["DISPLAY"] = ":0"
        lines, _ = self.open(which=(), platform="linux")
        self.assertEqual(lines[0], self.LINK)
        self.assertTrue(lines[1].startswith("not opened"))
        lines, _ = self.open({"version": None, "open": None})
        self.assertTrue(lines[1].startswith("not opened"))
        with mock.patch.object(appledore.os, "startfile", create=True, side_effect=OSError):
            lines, _ = self.open(which=(), platform="win32")
        self.assertTrue(lines[1].startswith("not opened"))

    def test_a_reply_that_isnt_utf_8_or_never_comes(self):
        reply = [sys.executable, "-c", "import sys; sys.stdout.buffer.write(b'Opened: \\x81')"]
        self.assertEqual(appledore.try_run(reply), "Opened: \ufffd")
        self.assertIsNone(appledore.try_run([sys.executable, "-c", "import time; time.sleep(10)"], timeout=0.2))


class VaultVariableTests(VaultTest):
    """APPLEDORE_VAULT, and PALACE_VAULT, the old name, read with a notice until the next version."""

    def setUp(self):
        super().setUp()
        self.small_vault()
        env = mock.patch.dict(appledore.os.environ)
        env.start()
        self.addCleanup(env.stop)
        for name in ("APPLEDORE_VAULT", "PALACE_VAULT"):
            appledore.os.environ.pop(name, None)

    def find_queue(self):
        """Run appledore find with no --vault, and return (stdout, stderr)."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            appledore.main(["find", "Queue"])
        return out.getvalue(), err.getvalue()

    def test_the_new_name(self):
        appledore.os.environ["APPLEDORE_VAULT"] = str(self.root)
        self.assertEqual(self.find_queue(), ("_Main Notes/Queue.md  [subtopic]  Queues.\n", ""))

    def test_the_old_name_with_a_notice(self):
        appledore.os.environ["PALACE_VAULT"] = str(self.root)
        out, err = self.find_queue()
        self.assertEqual(out, "_Main Notes/Queue.md  [subtopic]  Queues.\n")
        self.assertIn("PALACE_VAULT is now APPLEDORE_VAULT", err)

    def test_the_new_name_wins(self):
        appledore.os.environ["APPLEDORE_VAULT"] = str(self.root)
        appledore.os.environ["PALACE_VAULT"] = str(self.root / "missing")
        self.assertEqual(self.find_queue(), ("_Main Notes/Queue.md  [subtopic]  Queues.\n", ""))


if __name__ == "__main__":
    unittest.main()
