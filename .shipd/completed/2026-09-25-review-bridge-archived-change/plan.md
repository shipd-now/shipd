# review-bridge-archived-change
Status: verified

## Idea

Let `semdiff change <name>` resolve a change the build flow has already archived under `completed/`, and let the review guidance trigger on a change the diff itself carries.

### Motivation

The build flow archives a change into `completed/<date>-<slug>/` in the same pull request that ships it, so a gate review of that pull request finds nothing under `planned/` and `semdiff change` exits 1. The reviewer then loses the engine's structured parse of scenarios and tasks and has to read the delta specs from the raw diff by hand, as happened on talky pull request 83.

### Details

- `semdiff change <name>` resolves `planned/<name>/` first and falls back to the newest `completed/*-<name>/`, the same order `spec_status.py cat change` already uses.
- The JSON gains a top-level `location` (`planned` or `completed`) and `dir` (content-relative change directory). An archived change reports `lint.findings` as an empty list plus a `lint.skipped` sentence, because the linter only runs over `planned/` and an archive's deltas are already merged.
- The unknown-change error names both directories.
- The spec-aware trigger in `references/spec-aware.md`, the `SKILL.md` references table, and the gate body `plugins/s/harness/bodies/review.md` also fire when the diff adds or edits a change directory under `planned/` or `completed/`, with the slug read from the `files` output.

Affected capabilities: `semantic-review` (modified). Impact: `plugins/s/skills/review/scripts/semdiff.py`, `plugins/s/skills/review/tests/test_semdiff_change.py`, `plugins/s/skills/review/references/spec-aware.md`, `plugins/s/skills/review/SKILL.md`, `plugins/s/harness/bodies/review.md`. No new dependencies.

### Non-goals

- No lint over archived changes: `spec_lint.lint_change` stays planned-only.
- No change to the lifecycle verbs of `spec_status.py`, which keep resolving `planned/` only.
- No change to `diff`, `files`, `lint`, `context`, or `doctor`.
- No new trigger for a change that lives outside the diff and outside `planned/`; the reviewer still names such a change explicitly.

## Implementation

- **Resolution lives in semdiff, mirroring the status CLI.** Add a `_resolve_change_dir(root, content_dir, change)` helper in `plugins/s/skills/review/scripts/semdiff.py` beside `cmd_change` that returns `(location, absolute_dir)`: `planned/<change>` when that directory exists, else the lexicographically last directory matching `completed/*-<change>` via `glob.glob`, else `(None, None)`. Rejected: importing `_readable_change_dir` from `spec_status.py`, because it is a private helper of a CLI module and semdiff's established import is `spec_common` plus `spec_lint` only.
- **Error message.** When resolution returns `None`, `die` with `change '<name>' not found under <content_dir>/planned/ or <content_dir>/completed/.` so the existing unknown-change test still finds the name on stderr.
- **JSON shape.** Insert `"location"` and `"dir"` after `"change"` in the dumped object. `dir` is the path relative to the repo root, for example `.shipd/completed/2026-09-23-workspace-team-setup`. Every existing key keeps its position and meaning.
- **Lint on an archive.** When `location` is `completed`, do not call `sl.lint_change`; emit `{"findings": [], "skipped": "archived change: its deltas are already merged into verified/ and the linter runs over planned/ only"}`. When `location` is `planned`, the lint block is unchanged. Rejected: linting the archive directory in place, because `lint_change` resolves paths from the change name under `planned/` and would need a parallel code path for one advisory value.
- **Status parsing is shared.** The `Status:` regex, delta parsing, task parsing, and impact-file extraction operate on the resolved directory and need no change; an archive reports its stored status, typically `complete` or `verified`.
- **Tests.** In `plugins/s/skills/review/tests/test_semdiff_change.py`, add a test that moves the temp copy's `planned/sample-change` to `completed/2026-01-01-sample-change`, commits, runs `change sample-change`, and asserts exit 0, `location` equals `completed`, `dir` ends with `completed/2026-01-01-sample-change`, the deltas still carry the `rate-limit-login` scenario text, `tasks.total` is 4, and `lint.skipped` is present. Add a second test with two archives, `2026-01-01-sample-change` and `2026-02-01-sample-change`, asserting `dir` names the newer one. Extend the existing planned test to assert `location` equals `planned` and `lint` carries no `skipped` key. Extend the unknown-change test to assert stderr names `completed/`.
- **Guidance surfaces.** The trigger sentence becomes: the user named a change, exactly one change exists under `planned/`, or the diff adds or edits a change directory under `planned/` or `completed/`, whose slug is the directory name with any leading `YYYY-MM-DD-` date prefix stripped. `spec-aware.md` states it in its own load condition and in the trigger paragraph; the `SKILL.md` references table row states it in the Load-when cell; the gate body's step 8 states it in one sentence and keeps reading through `cat change`. The gate body's closing lint sentence is scoped to a change under `planned/`, because `spec_lint.py` resolves `planned/` only and would report spurious missing-plan errors for an archive. The gate body and the copilot skill keep naming no file under `plugins/s/skills/review/references/`.
- **Table cell length.** The `SKILL.md` line count stays under 300, so the row edit must stay on one table line.

Risk: a repository with several archives of one slug. Guard: newest date prefix wins, matching the status CLI, and the returned `dir` makes the pick visible to the reviewer.

## Readiness attestation

### Problem and motivation

The review bridge cannot load a change once the build flow has archived it, so gate reviews of shipped pull requests lose the engine's structured scenario parse.

Evidence:

- `plugins/s/skills/review/scripts/semdiff.py:1094-1097` joins `planned/<change>` only and dies otherwise.
- Requirement `change-bridge` in capability `semantic-review` states the verb exits non-zero when the change is absent under `planned/`.
- Runnable premise: `python3 plugins/s/skills/review/scripts/semdiff.py change workspace-team-setup` in the main checkout printed `change 'workspace-team-setup' not found under .shipd/planned/.` and exited 1, while `.shipd/completed/2026-09-23-workspace-team-setup/` exists.

### Scope and non-goals

The change touches the `change` verb's resolution and JSON, its test module, and the three guidance surfaces naming the trigger; lint over archives and the lifecycle verbs stay out.

Evidence:

- In scope: `plugins/s/skills/review/scripts/semdiff.py:1092-1149`, `plugins/s/skills/review/tests/test_semdiff_change.py:31-84`, `plugins/s/skills/review/references/spec-aware.md:3-7`, `plugins/s/skills/review/SKILL.md:44`, `plugins/s/harness/bodies/review.md:54-56`.
- Out of scope: `plugins/s/skills/build/scripts/spec_lint.py:1720-1745` (`lint_change` resolves `planned/` only) and `plugins/s/skills/build/scripts/spec_status.py:317-323` (`_is_change` documents that lifecycle helpers stay planned-only).

### Affected capabilities and files

One capability and five files are affected: the engine and its test change behaviour, and three prose surfaces carry the widened trigger.

Evidence:

- Capability `semantic-review`: requirement `change-bridge` (base 8bf1fc0f7172) and requirement `spec-aware-review` (base fc88b7c23c3c), hashes from `spec_status.py base-hash`.
- Files: `plugins/s/skills/review/scripts/semdiff.py:1092`, `plugins/s/skills/review/tests/test_semdiff_change.py:52`, `plugins/s/skills/review/references/spec-aware.md:3`, `plugins/s/skills/review/SKILL.md:44`, `plugins/s/harness/bodies/review.md:54`.
- Runnable premise: `python3 plugins/s/skills/build/scripts/spec_status.py cat change workspace-team-setup` exited 0 and printed the archived `plan.md` headed `Status: verified`, confirming the planned-then-completed fallback pattern the fix mirrors.
- Runnable premise: `python3 -m unittest discover -s plugins/s/skills/review/tests` ran 176 tests and reported OK, the baseline the new tests extend.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- Fallback order (planned first, newest archive second): settled by investigation against `spec_status.py:268-283`.
- Lint handling for an archive (skip with a `skipped` sentence): settled by investigation of `spec_lint.py:1720-1745`.
- JSON additions (`location`, `dir`, additive only): settled by investigation of the existing consumers, which read `status`, `deltas`, `tasks`, `lint`, and `impact_files` by key.
- Trigger wording across the three guidance surfaces: settled by investigation of requirement `review-skill-references`, whose scenarios forbid the gate body from naming a reference file but not from restating the trigger.
