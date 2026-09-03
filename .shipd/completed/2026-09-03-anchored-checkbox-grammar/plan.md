# anchored-checkbox-grammar
Status: verified

## Idea

Anchor the checkbox-line grammar in the linter and the coordinator so a
checkbox-looking literal inside a task's prose is never counted as a task.

### Motivation

`spec_lint.py`'s `CHECKBOX_RE` and every `claim_task.sh` matcher find the
`- [ ]`/`- [~]`/`- [x]` marker anywhere in a line, so a backticked literal in
a wrapped task description is counted as a real task — observed live in this
repo (phantom "task N has no [req:] tag" lint errors, and ordinal drift that
would corrupt coordinator ids) — while `spec_status.py` already anchors its
regex, so the three surfaces can disagree about the same file.

### Details

- Anchor `spec_lint.py`'s `CHECKBOX_RE` to the line start (optional leading
  blanks, then the `- [<state>] ` marker) — the traceability check and the
  brief-requirements check both consume it.
- Anchor every matcher in `claim_task.sh` the same way: ordinal enumeration,
  readiness, in-progress resolution, status counts, the box rewrite, and the
  marker strip.
- The canonical grammar matches `spec_status.py`'s existing anchored
  behavior, so the linter's ordinals, the coordinator's ids, and the status
  CLI's counts can no longer disagree over prose literals.

Affected capabilities: `shipd-spec-lint` (modified:
`traceability-tag-enforcement`), `build-task-coordination` (modified:
`atomic-task-claiming-with-stable-ids`). Impact:
`plugins/s/skills/build/scripts/{spec_lint.py,claim_task.sh}`,
`tests/{test_spec_lint,test_claim_task}.py`,
`plugins/s/.claude-plugin/plugin.json` (→ 0.6.173).

### Non-goals

- No change to `spec_status.py` — its regex is already anchored and is the
  model for the others.
- No reconciliation of the pre-existing corner differences the bug is not
  about: `spec_status` tolerates `*`-bullet and uppercase-`[X]` boxes the
  other two never matched; that asymmetry predates this change and stays.
- No change to the tasks emission format, group tags, ids' 1-based ordinal
  semantics, or any coordinator verb's interface.

## Implementation

- **The canonical grammar**: a checkbox line's content begins — after
  optional leading blanks — with `- [<state>] ` where `<state>` is a space,
  `~`, or `x`. Anything after the marker is prose; a marker-shaped substring
  mid-line is prose. Rejected: column-0-only anchoring — `spec_status.py`
  already tolerates leading whitespace, and tolerating it everywhere keeps
  one shared definition instead of a third variant.
- **`spec_lint.py`**: `CHECKBOX_RE` becomes `^[ \t]*- \[[ ~x]\]` — the
  marker alone, no trailing-space requirement, so a degenerate text-free
  marker line counts exactly as the coordinator and `spec_status.py` count
  it (module constant at spec_lint.py:91, used with `.search`, which the
  `^` anchor makes position-fixed; both call sites — the brief-requirements presence
  check and the traceability walk — need no other edit). Update the constant's
  comment to state the anchored rule.
- **`claim_task.sh`** — every matcher gains the same anchor, POSIX bracket
  class `[[:blank:]]*` for the leading run (bash 3.2 / BRE / awk safe):
  `all_checkboxes` and `first_pending` greps; the `first_ready_line` awk
  line-filter (its inner `match()` for the box character is then safe, since
  the anchored marker is the line's first marker-shaped substring); the
  in-progress enumeration awk (the `resolve_line` seam) and the `status`
  count greps; `set_box`'s sed, which captures the leading blanks and
  rewrites `^\([[:blank:]]*\)- \[[ ~x]\]` to `\1- [<to>]`; and
  `strip_marker`, which strips `^[[:blank:]]*- \[[ ~x]\] *`. Update the
  header comment's ID-semantics paragraph to state the anchored rule.
- **Regression fixture**: a tasks.md whose wrapped task prose carries
  backticked checkbox literals on continuation lines (built by
  concatenation in the tests, never as raw markers in this change's own
  tasks.md). Runnable premise (observed 2026-09-03 in this repo): emitting
  a change whose task prose contained backticked checkbox literals produced
  `tasks.md task 2 has no [req: ...] traceability tag` (and 3, 4) from
  `spec_emit.py`'s lint pass despite every real task carrying a tag; the
  same file inflates `claim_task.sh status` counts under the current script.
- **Tests** (both stdlib-only): `test_spec_lint.py` — a tagged task whose
  prose contains a literal lints clean, ordinals in errors still match real
  tasks when a genuinely untagged task follows a literal-carrying one, an
  indented real checkbox still counts; `test_claim_task.py` — with a
  literal-carrying tasks.md, `status` counts only real tasks, `claim`
  ordinals map to the right lines (the box rewrite lands on the real task,
  not the literal's line), readiness/barrier evaluation ignores literals,
  and `complete <id>` targets the same line the claim marked.
- Risk: an existing repo whose tasks.md relies on mid-line matching (a
  marker not at line start being treated as a task) would lose that task —
  no emission path ever produced such a file, and the linter would have
  mis-ordinaled it anyway; accepted.
