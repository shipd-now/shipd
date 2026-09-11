# task-tag-satisfiability
Status: verified

## Idea

Refuse a tasks file whose group tags can never all become ready, and stop the build skill from advising the tagging that causes it.

### Motivation

A tasks file whose `[P<n>]` tags form a readiness cycle passes `spec_lint.py` clean while leaving the coordinator with nothing claimable — reproduced here at `pending=4` with `next` returning empty and the linter printing `OK`. That deadlocked a real build, and `build/SKILL.md:298`'s "when in doubt, leave a task untagged (a safe barrier)" is what steers an author into it.

### Details

- Implement the coordinator's readiness predicate in Python and drain it to a fixpoint to find tasks that can never become ready.
- Refuse such a tasks file in `spec_lint.py`, naming the tasks involved.
- Pin the Python predicate to the shell implementation with a differential parity test.
- Replace the "untagged is safe" advice with the two idioms that are actually safe.

Affected capabilities: `shipd-spec-lint` (new requirement), `build-task-coordination` (one requirement modified). Impact: `plugins/s/skills/build/scripts/spec_lint.py`, `plugins/s/skills/build/SKILL.md`, the two guarding test modules, and the plugin version bump.

### Non-goals

- No change to the coordinator's readiness semantics. Barriers and groups keep behaving exactly as they do; only the unsatisfiable *configuration* is refused, at authoring time.
- No change to `claim_task.sh`'s claiming path, lock protocol, or awk. It stays the runtime implementation.
- No auto-repair of a bad tag configuration. The linter refuses and names the tasks; an author or the orchestrator retags.
- No warning tier for this: an unsatisfiable file is an error, since nothing downstream can proceed.

## Implementation

- **Mirror the predicate in Python; do not delegate to it.** `claim_task.sh:197` implements `ready()` in awk, and it is called inside `claim_once` under the lock and again on every `--wait` retry. Routing that through a Python subprocess would add interpreter startup to the atomic claiming path for no correctness gain, so the awk stays the runtime implementation and Python gets a mirror. Rejected: making the shell delegate to a single Python implementation — it is the theoretically cleaner shape, and `claim_task.sh:157` shows Python is already spawned once in the resolution preamble, but the claiming hot path is the most safety-critical code in the engine and this change has no reason to touch it.
- **A differential parity test is what makes the mirror safe.** Rather than trusting the two to agree, the test enumerates tag configurations — including the deadlock shape, the barrier idiom, fully-grouped monotonic, fully sequential, and mixed box states — and asserts that for each one the Python predicate's ready set is identical to what `claim_task.sh next` reports. Drift becomes a failing test rather than a stalled build.
- **Satisfiability is a drain, not a predicate.** Readiness answers "can this task be claimed now"; the linter needs "can every pending task eventually be claimed". So the check repeatedly marks every ready pending task done and iterates until no further task becomes ready. Tasks still pending when the drain stalls are exactly the unsatisfiable set, and the error names them by the ordinal the coordinator uses.
- **The boundary is verified, so the check will not over-refuse.** Drained against the real coordinator: `P1 → untagged barrier → P2` completes 3/3, fully-grouped monotonic completes 4/4, fully sequential completes 2/2, and only non-monotonic groups around a barrier stalls at 0/3. The check must accept the first three and refuse the fourth.
- **The guidance names the two safe idioms.** `build/SKILL.md:298` becomes: either leave every task untagged (fully sequential), or tag every task with group numbers that never decrease down the file. The failure needs both a barrier and a non-monotonic group number, so either idiom alone is sufficient, and "untagged is safe" is only true when no groups surround it.
- **Version bump.** Everything lands under `plugins/s/`, so `plugins/s/.claude-plugin/plugin.json` goes `0.6.209` to `0.6.210`.

Risk: the mirror and the awk diverge on an input the parity corpus does not cover. Guarded by choosing the corpus from the semantics rather than from examples — every combination of barrier presence, group monotonicity, and box state that the rule distinguishes.
