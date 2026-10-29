# Behavioural evals

These cases start real Claude Code sessions with the plugin loaded and grade what the study loop does, so a change to a skill's wording that breaks a behaviour shows up before it ships. The unit tests in `tests/` cover the script, but not what an agent does with the skills.

## Run them

From the repo root:

```sh
claude plugin eval . --scaffold --trust-plugin --allow-tools Bash Write Edit --runs 1 --no-publish --max-cost-usd 8
```

- `--scaffold` runs each case's `scaffold.sh`, which sets up the fixture vault. Without it every case starts in an empty folder and fails.
- `--allow-tools Bash Write Edit` grants the tools the loop needs: it runs the script and writes notes. A run only grants the read-only tools by default.
- `--max-cost-usd` stops the run at that cost, because each run is a real session. Recorded full passes of cases 01–08 cost $3.57–3.69 at `--runs 1` and $10.44 at `--runs 3`; cases 09–11 add to that.
- `--runs 1` runs each case once, enough to see a break. With 3 runs a case, read each case's pass rate (`passRate` in `aggregate-result.json`) to tell a regression from one unlucky session, because at the default `--threshold` of 1.0 one failing run in three fails the case. A lower `--threshold` does the same.
- `--case <name>` runs one case, such as `--case next-writes-subtopic`.
- Cases 10 and 11 resume a recorded conversation, so they run only with the plugin. Add `--ablation with-without` to run them without it too.

Results land in `evals/results/`, which git ignores.

## The cases

| Case | The behaviour it protects |
|---|---|
| `01-next-writes-subtopic` | "next" with one ready node writes that subtopic in the fixed shape, with its properties kept |
| `02-subject-question-offers-filing` | a question about the subject gets an answer and a one-line offer to file it, and nothing is written yet |
| `03-appledore-question-no-offer` | a question about appledore gets a direct answer and no offer, and the answer says filing waits for the user's yes |
| `04-just-answer-turns-offer-off` | after "just answer", an answer comes with no offer, but still drawn from the agreed sources and naming them, because "just answer" turns off only the offer |
| `05-oversized-subtopic-splits` | a subtopic pushed past 450 words gets a new planned subtopic proposed, never a child note |
| `06-deep-dive-proposes-and-waits` | a deep dive proposes 1–4 nodes and writes nothing before a yes |
| `07-sources-dont-cover` | a question the sources don't cover gets "the agreed sources don't cover it", never an answer from memory |
| `08-plan-asks-in-one-message` | a new topic's plan asks for sources, goal and placement in one message |
| `09-next-writes-recommended-node` | "next" with two ready nodes writes the one `appledore next` recommends, without asking which |
| `10-just-answer-holds-next-turn` | "just answer" said in an earlier turn still holds: case 02's question gets its answer with no offer |
| `11-deep-dive-writes-after-yes` | a yes to a deep dive's proposal writes the new stub, moves the left-out stub into the learning graph and redraws it, and writes no subtopic yet |

In 03 and 04, a session without the plugin has no reason to offer to file, so a no-offer check alone can't show what the plugin adds. Each case also checks something only the plugin knows: in 03, that filing waits for the user's yes; in 04, that the answer names the agreed sources and nothing else. The no-offer check still guards against the plugin itself offering when it shouldn't.

Not covered yet:
- a question the vault already answers (give the note's link and make no offer);
- Start with no topic named;
- wrap-up's commit and push. The eval runner's sandbox denies git: its settings list the git binary and git's credential helpers under `sandbox.credentials.files` with `mode: deny`, so a session can't commit, and no flag of `claude plugin eval` allows it.

## The graders

- **One behaviour per grader file, named for it.** An LLM judge answers in one word, so a report says only "judge votes: FAIL FAIL FAIL"; with one behaviour per file, the failing grader's name says which behaviour broke.
- **Every grader counts in both arms**, with and without the plugin, except a `tool_used` grader on `Skill`. Every case but 10 has one, `loads-study-skill`, which reports whether the session loaded the `study` skill, as a sign the plugin ran, and doesn't count toward the score. Case 10 starts the skill by its command, which isn't a Skill tool call.
- **A regex checks what an LLM judge got wrong on correct replies.** In 02, `offer-is-last-line` checks that the reply ends on a line that links a note and asks a yes-or-no question, and the judge only checks what the offer asks. In 04 and 10, `no-outside-material` fails a reply that cites an RFC or a section number, or uses terms the agreed pages never use, which every recorded reply without the plugin did, because a judge can't see the pages to tell what is outside them.
- **File graders see only new files.** `file_exists` and a `regex` on `target: files` compare the workspace's file list before and after the run, never contents. So each case that must write nothing pairs `no-new-note` (no new file under `vault/`) with a `regex` on the note an answer would go into, which reads the file at the end of the run and so catches a note changed in place. Case 05's `no-new-written-note` passes while the session edits `Freshness.md`, because that file isn't new.
- **Tool graders see only the Write and Edit tools.** A note written through the shell, as `appledore mv` and `graph --write` do, shows only in the file graders.
- The graders check behaviour (the reply, the files written, the tools used), not the skill's file layout, so they hold when a step file moves or is renamed.

## The fixture vault

`_fixture/` holds a small made-up vault on one topic, HTTP caching: two written subtopics, one ready stub, three waiting and four left out, plus the two pages that are its agreed sources. `_fixture/setup.sh` copies them into each run's empty workspace, so every case starts from the same vault. A case that needs more adds it in its own `scaffold.sh` after running `setup.sh`, as 09 does to make a second node ready.

- **It never reaches your vault.** Each run has a temporary home folder, so the default vault path points into it, and the agent's shell can write only inside the run's folders. `setup.sh` refuses to run when HOME is your real home folder.
- **The vault's path reaches the agent through the shell.** The runner passes a session no variables except `EVAL_*` ones, so `setup.sh` exports `APPLEDORE_VAULT` from the temporary home's profile files, with `APPLEDORE_OPEN=0` so no run opens Obsidian.
- **The sources are local pages**, linked by absolute path from the topic note, so the agent reads them without network access. They sit beside the vault, never in it. Their facts follow RFC 9111 (HTTP Caching) and RFC 9110 (HTTP Semantics), but the pages name no other document, because case 04 fails an answer that cites one, and they don't say they belong to an eval, because that can change how the agent behaves.
- **Freshness sits at 448 words**, 2 under the limit, so case 05's filed answer always pushes it over.
- **Cases 10 and 11 resume a two-turn conversation** in `history.jsonl`: the user's first message and the plugin's reply, copied from a recorded run, in the shape of a Claude Code session file. The transcript holds no skill load, and a resumed session answers a plain question without loading one, so case 10's next turn starts the skill by its command.

`tests/test_eval_fixture.py` runs with the other unit tests. It sets up each case's workspace as the runner does, with a temporary home, and checks:
- that the script's `check` finds 0 errors and 0 warnings, because a warning gives the agent something to fix that no case asked for;
- that Freshness sits at 448 words;
- that each `regex` grader on a file gives the result an untouched vault should: a pass in a case tagged `read-only`, a fail in a case that must write.
