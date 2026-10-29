# Behavioural evals

These cases start real Claude Code sessions with the plugin loaded and grade what the study loop does, so a change to a skill's wording that breaks a behaviour shows up before it ships. The unit tests in `tests/` cover the script, but not what an agent does with the skills.

## Run them

From the repo root:

```sh
claude plugin eval . --scaffold --trust-plugin --allow-tools Bash Write Edit --runs 1 --no-publish
```

- `--scaffold` runs each case's `scaffold.sh`, which sets up the fixture vault. Without it every case starts in an empty folder and fails.
- `--allow-tools Bash Write Edit` grants the tools the loop needs: it runs the script and writes notes. A run only grants the read-only tools by default.
- `--runs 1` runs each case once, enough to see a break. Leave it off for 3 runs a case, which separates a real regression from one unlucky session.
- `--case <name>` runs one case, such as `--case next-writes-subtopic`.

Each run is a real session, so a full pass of 8 cases costs real usage: add `--max-cost-usd <amount>` to cap it. Results land in `evals/results/`, which git ignores.

## The cases

| Case | The behaviour it protects |
|---|---|
| `01-next-writes-subtopic` | "next" with one ready node writes that subtopic in the fixed shape, with its properties kept |
| `02-subject-question-offers-filing` | a question about the subject gets an answer and a one-line offer to file it, and nothing is written yet |
| `03-appledore-question-no-offer` | a question about appledore gets a direct answer and no offer |
| `04-just-answer-turns-offer-off` | after "just answer", an answer comes with no offer |
| `05-oversized-subtopic-splits` | a subtopic pushed past 450 words gets a new planned subtopic proposed, never a child note |
| `06-deep-dive-proposes-and-waits` | a deep dive proposes 1–4 nodes and writes nothing before a yes |
| `07-sources-dont-cover` | a question the sources don't cover gets "the agreed sources don't cover it", never an answer from memory |
| `08-plan-asks-in-one-message` | a new topic's plan asks for sources, goal and placement in one message |

Every case also checks that the session loaded the `study` skill. The graders check behaviour (the reply, the notes written, the tools used), not the skills' file layout, so they hold when skills move or are renamed. A tool check accepts the script under either name, `palace` or `appledore`.

## The fixture vault

`_fixture/` holds a small made-up vault on one topic, HTTP caching: two written subtopics, one ready stub, three waiting and four left out, plus the two pages that are its agreed sources. `_fixture/setup.sh` copies them into each run's empty workspace, so every case starts from the same vault.

- **It never reaches your vault.** Each run has a temporary home folder, so the default vault path points into it, and the agent's shell can write only inside the run's folders.
- **The vault's path reaches the agent through the shell.** The runner passes a session no variables except `EVAL_*` ones, so `setup.sh` exports `APPLEDORE_VAULT` and `PALACE_VAULT` from the temporary home's profile files, with opening notes in Obsidian turned off.
- **The sources are local pages**, linked by absolute path from the topic note, so the agent reads them without network access. They sit beside the vault, never in it.
- **Freshness sits at 448 words**, 2 under the limit, so case 05's filed answer always pushes it over.

After changing the fixture, check it is still sound: copy it into an empty folder with the copy and link steps of `setup.sh`, then run the script's `check` on that folder with `--vault`. It must show 0 errors and 0 warnings, because a warning in the fixture gives the agent something to fix that no case asked for.
