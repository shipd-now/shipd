<!-- description: Drive workspace initiatives — author, list, review a brief, or attach one to an epic — through the engine's verbs. -->
# /s:initiative — guided initiative briefs and epic attachment

An initiative sits above epics: its brief captures **outcome requirements**,
ticked over time, and epics attach to it with an `Initiative:` line. Briefs
live in the workspace, not the repo. Interview, drive the exact verbs, stop —
never hand-write a brief's path, an epic's header, or a `Status:` line.

<!-- include:preamble -->

## Resolve the workspace first

Every verb needs one. Run `shipd workspace` before asking anything: it prints
the workspace root, the declared project slugs, and every initiative with its
status and scope — ground the goal, outcomes, and scope options in that. If no
workspace resolves, report the error verbatim, write nothing, and point the
user at `/s:workspace init`. Then dispatch the invocation to exactly one verb
below, run from the repo root so `--root` can be omitted.

## `new <slug>` — interview, then install a lint-clean brief

Ask one batched round for whatever the workspace did not settle: the **goal**,
the **outcome requirements**, and the optional **`Project:` scope** (the
declared project slugs plus "unscoped"), concrete options with the recommended
default first.
<!-- if:question-dialogs -->
Put the whole round in a single question dialog.
<!-- else -->
End the turn as plain text with the questions numbered, options lettered,
default first, and wait for a typed reply.
<!-- end -->
Author the brief in a staging file — never the workspace path, which the engine
owns — as `# <slug>`, `Status: open`, an optional `Project:` line, a sentence
of goal, and a `## Requirements` section of at least one `- [ ]` checkbox, each
an **outcome the initiative achieves** rather than a task, all unticked.
<!-- if:file-references -->
Read `{refs}/initiative.md` for the brief's shape and the linter's rules.
<!-- else -->
This harness cannot open a companion reference file, so the linter's full rule
set is unavailable here. Say so, author from the shape above, and let the
install below be the check — it names exactly what to fix.
<!-- end -->
Install through the engine, which resolves the path, validates, and on any
finding removes what it installed and exits non-zero:

```
python3 "$S/spec_emit.py" initiative <slug> --from <staging-file>
```

Fix the staged brief and re-run until it exits `0`. This lands in the
workspace, outside the repo, so there is no PR.

## `list` — status and progress, read-only

Run `shipd workspace` for the roster, then `python3 "$S/spec_status.py"
initiative-show <slug>` per brief. Summarize each initiative's status, its
`Requirements: done/total` progress, and its project scope. Change nothing.

## `review <slug>` — walk outcomes, tick, sync

Walk the brief's open (`- [ ]`) requirements with the user one by one. Tick
only what they confirm achieved, leave the rest, then let the engine derive the
status — never hand-write the `Status:` line:

```
python3 "$S/spec_status.py" initiative-sync <slug>
```

Report the status it prints: it reaches `achieved` only when every requirement
is ticked, and never touches a `dropped` brief.

## `set <epic> <initiative>` — attach exactly one, via a PR

Asked to attach an initiative to a **change** whose plan carries an `Epic:`
line, refuse — a member derives its initiative through the epic, and a plan
carrying both is a lint error. Name that epic as the attachment point instead.

Otherwise create a worktree (`shipd worktree initiative-set-<epic>`), work
inside it, and write the header through the engine rather than editing the epic
file:

```
python3 "$S/spec_status.py" epic-set-initiative <epic> <initiative>
python3 "$S/spec_lint.py" --epic <epic>
```

The lint checks the epic's structure and that the reference resolves to a real
brief; fix and re-run until it exits `0` and prints `OK`. Then commit on
`change/initiative-set-<epic>`, open a PR, let it auto-merge, and report the PR
with its full URL.

Every verb ends the moment its own work is done: report what it did, then point
the user at `/s:epic` to decompose the work the initiative now tracks.
