# Wrap up

A session adds notes faster than anyone tidies them, so each one ends with a review of what it
touched. Small fixes every session keep the MOC chains short enough to navigate, which a big
clean-up months later can't.

## 1. Review

Run `appledore review`. It lists the notes changed since the vault's last commit, the chains above
them, and each finding on them with its fix. A topic the user says is done counts as finished too:
ask whether its `status` becomes `done`.

## 2. Propose, then apply

Give the changes as one numbered list, each with its reason in a few words, and apply the ones the
user says yes to: renames with `appledore mv`, merges as study rule 6 says, and a subtopic's size
as `writing-rules.md` rule 7 says. Merge a likely duplicate only if both notes hold one concept,
because some only share words. If nothing needs changing, say so in one line.

## 3. Commit

Run `appledore commit "<message>"`, naming the topic and what the session added, such as
"Study Azure Blob Storage: access tiers, lifecycle rules". It pushes once, and refuses while git
needs the user (a merge in progress, say) or `appledore check` finds errors. If the user declines a
fix it needs, leave the work uncommitted and tell them, because committing with git yourself skips
these checks. If the push fails, tell the user why: the commit stays, and a retry is theirs,
because it may need a login or a fix on the remote.

End with one line: what the session added (notes written, answers filed, stubs added) and what's
ready next. For a finished topic, follow it with the topic's stubs to explore, as
`appledore next "<topic>" --left-out` prints them, and how to pick one: "deep dive <stub>".
