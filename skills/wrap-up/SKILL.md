---
name: wrap-up
description: >-
  Step of the appledore study loop: end a study session by reviewing the MOC chains it touched
  (MOCs too big or too small, notes that now have children, duplicates, orphans, a topic that is
  finished), proposing each restructure for the user's yes, then committing and pushing the vault.
  Use only inside a study session that the appledore study skill started, when the user says "wrap
  up", "done for today" or wants to stop.
---

# Wrap up

This runs inside an appledore study session. If the `study` skill isn't loaded, load it first: it
sets up `palace` and holds the rules every step follows.

A session adds notes faster than anyone tidies them, so each one ends with a review of the parts
of the vault it touched. Small fixes made every session keep the MOC chains short enough to
navigate, which a big clean-up months later can't.

## 1. Find what the session touched

1. `git -C "<vault>" status --porcelain` lists the notes changed since the last commit, and so
   since the last wrap-up.
2. `palace related` on each, for its chain up to a root MOC. The MOCs and parent notes on those
   chains are what you review.

## 2. Review

- **`palace check`:** every warning on a touched note or chain: a MOC with two children or fewer
  (dissolve it), a note with more than 30 children (split it, or group some under a MOC), a
  subtopic outside 150–450 words (over: split it; under: merge it, never pad), a learning graph
  out of date.
- **New children:** a note that now has children gets `![[Children.base]]` at the end of its body,
  before Sources, so they're listed. One with five or more might be better as a MOC.
- **Duplicates:** `palace find` on each new note's title, aliases and key words. Two notes on one
  concept are merged.
- **Orphans:** the notes `palace tree` lists outside every chain.
- **A finished topic:** `palace next "<topic>"` shows no planned stubs left, or the user says the
  topic is done. Ask whether its `status` becomes `done`. The stubs left out don't count, because
  they wait for a deep dive: the session ends with their list (step 4).

## 3. Propose, then apply

Give every change as one numbered list, each with its reason in a few words, and apply the ones
the user says yes to: renames with `palace mv`, and merges as the `study` skill's rule 6 says.
Then `palace check` must show no errors. If nothing needs changing, say so in one line.

## 4. Commit and push

1. If a rename changed only the letter case of a file name, run `git -C "<vault>" rm --cached
   "<old path>"` first, because the vault repo ignores case and would otherwise miss the rename.
2. `git -C "<vault>" add -A`, then commit with a message that names the topic and what the session
   added, such as "Study Azure Blob Storage: access tiers, lifecycle rules".
3. `git -C "<vault>" push`. If the push fails, say why, and leave the commit in place.

End with one line: what the session added (notes written, answers filed, stubs added) and what's
ready next. For a finished topic, follow it with the topic's stubs to explore, as
`palace next "<topic>" --left-out` prints them (each linked, with its summary, under the note that
left it out), and end with how to pick one: "deep dive <stub>".
