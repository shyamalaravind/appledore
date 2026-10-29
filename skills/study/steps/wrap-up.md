# Wrap up

A session adds notes faster than anyone tidies them, so each one ends with a review of the parts
of the vault it touched. Small fixes made every session keep the MOC chains short enough to
navigate, which a big clean-up months later can't.

## 1. Find what the session touched

1. `git -C "<vault>" status --porcelain` lists the notes changed since the last commit, and so
   since the last wrap-up.
2. `appledore related` on each, for its chain up to a root MOC. The MOCs and parent notes on those
   chains are what you review.

## 2. Review

- **`appledore check`:** every warning on a touched note or chain: a MOC with two children or
  fewer (dissolve it), a note with more than 30 children (split it, or group some under a MOC), a
  subtopic outside 150–450 words (fix it as `writing-rules.md` rule 7 says), a learning graph out
  of date.
- **New children:** a note that now has children gets `![[Children.base]]` at the end of its body,
  before Sources, so they're listed. One with five or more might be better as a MOC.
- **Duplicates:** `appledore find` on each new note's title, aliases and key words. Two notes on
  one concept are merged.
- **Orphans:** the notes `appledore tree` lists outside every chain.
- **A finished topic:** `appledore next "<topic>"` shows no planned stubs left, or the user says
  the topic is done. Ask whether its `status` becomes `done`. The stubs left out don't count,
  because they wait for a deep dive: the session ends with their list (step 4).

## 3. Propose, then apply

Give every change as one numbered list, each with its reason in a few words, and apply the ones
the user says yes to: renames with `appledore mv`, and merges as study rule 6 says. Then
`appledore check` must show no errors. If nothing needs changing, say so in one line.

## 4. Commit and push

1. If a rename changed only the letter case of a file name, run `git -C "<vault>" rm --cached
   "<old path>"` first, because the vault repo ignores case and would otherwise miss the rename.
2. `git -C "<vault>" add -A`, then commit with a message that names the topic and what the session
   added, such as "Study Azure Blob Storage: access tiers, lifecycle rules".
3. `git -C "<vault>" push`. If the push fails, say why, and leave the commit in place.

End with one line: what the session added (notes written, answers filed, stubs added) and what's
ready next. For a finished topic, follow it with the topic's stubs to explore, as
`appledore next "<topic>" --left-out` prints them, and how to pick one: "deep dive <stub>".
