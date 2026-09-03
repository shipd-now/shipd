<!-- description: Decompose a feature into an epic — shared decisions, design, and a stub table of member changes — then stop. -->
# /s:epic — decompose a feature into an epic

Turn a feature too large for one change into an epic: the cross-cutting
decisions recorded once, and a stub table of the member changes that inherit
them. You emit the epic and stop — you never plan or build its members.

<!-- include:preamble -->

## 1. Work in the epic's own worktree

Create it from the repo root (`shipd worktree epic-<slug>`) and work inside
`.worktrees/epic-<slug>`, so the artifact is born on `change/epic-<slug>` and
ships in one PR.

## 2. Investigate before you ask

Read the repository first — the verified capabilities and in-flight changes
under the content directory (`.shipd/` by default), the existing epics
(`shipd epic <slug>`), and the code the feature touches — until you can see the
seams it decomposes along. Never ask what the repo or the request already
answers.

Read any research report or video brief the user names as pre-investigation
context, through the engine rather than by opening paths — `python3
"$S/spec_status.py" cat research <slug>`, or `cat video <slug>`. Link only what
you actually read; a brief is an input to investigation, never a replacement
for it. If the user names a raw recording rather than an installed brief, point
them at `/s:video-ingest` first.

## 3. Ask only what genuinely remains

Ask nothing when investigation settled everything. Otherwise put the
un-inferrable decisions — the decomposition boundaries, a shared architectural
choice, the theme or initiative — in **one** round of 2–4 questions, each with
concrete options and the recommended default first, then converge.
<!-- if:question-dialogs -->
Use a single question dialog, in a turn carrying no other load-bearing prose.
<!-- else -->
End the turn as plain text with the questions numbered, options lettered,
default first, and wait for a typed reply.
<!-- end -->

## 4. Emit the epic

Write `.shipd/epics/<slug>/epic.md` at `Status: draft` — a `# <slug>` title
matching the directory, `## Introduction` first (why first, closing with a
`### Non-goals` subsection), then `## Decisions`, `## Design`, and a
`## Changes` table whose header row is exactly:

```
| Change | Description | Code | Integration | Unknowns | Risk |
```

One row per member: a unique kebab-case slug, then your honest `low`,
`medium`, or `high` rating in each of the four complexity columns.
<!-- if:file-references -->
Read `{refs}/epic.md` for the full contract the linter enforces — the metadata
keys, the optional `## Research` and `## Video` link sections, and the table
rules.
<!-- else -->
This harness cannot open a companion reference file, so the linter's full
contract is unavailable here. Say so, author from the shape above, and let the
lint gate below be the check: fix exactly what it names and re-run.
<!-- end -->

## 5. Self-review, then lint until clean

Re-read the draft for placeholders, a decomposition that does not cover the
feature, and Decisions or Design that leave a member author guessing. Fix what
you find, then run the gate from the repo root until it exits `0` and prints
`OK`:

```
python3 "$S/spec_lint.py" --epic <slug>
```

## 6. Promote, ship, and hand off

On approval, advance the status through the guarded verb, never by hand:

```
python3 "$S/spec_status.py" epic-set-status ready <slug>
```

Commit the `.shipd/epics/<slug>/` artifact on `change/epic-<slug>`, open a PR,
let it auto-merge, and report the PR with its full URL. Then summarize the epic
and tell the user to run `/s:plan <member-slug>` for each stub row — that is
where a member change is born. Create no member directories yourself, and stop.
