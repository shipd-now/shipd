# spec-lint-conflict-markers
Status: verified
Theme: spec-engine

## Idea

### Motivation

`.shipd/verified/delivery-dashboard/spec.md` has carried `<<<<<<< HEAD` at line
1212 and `>>>>>>> origin/main` at line 1607 since 2026-08-14, bracketing six of
its thirty-two requirements. `spec_lint.py` reported `OK: master library is
valid.` over it for nearly two months, because it has no conflict-marker check
of any kind.

That matters beyond the one file. Every change in this repository ships behind
a lint-clean claim, and the `ci` gate reads the exit code. A marker committed
mid-merge passes all of it. So every lint-clean claim made in that window was
weaker than it read, including the ones this series has been quoting.

The semantic review on PR 288 found it, unprompted, while checking something
else.

### Details

The linter rejects a git conflict marker at the start of a line, in every spec,
plan and task file it reads, and the two live markers are removed.

### Non-goals

- **No other `.shipd/verified/` repair.** The same review found three
  requirements restating wording another requirement owns, where the two now
  disagree, plus the abandoned-reader clause demanded a third time in
  `project-readme`. Each needs its own change; bundling them here would mean
  one PR nobody can review against one criterion.
- **No epic, initiative, PRD, research, docs or wiki coverage.** The check goes
  where the failure happened — spec, plan and task files. Widening it to every
  lint mode is a bigger change than the one this fixes, and naming the gap is
  better than quietly half-covering it.
- No change to any `/s:review` prose surface, so a ReviewBench measurement
  calibrated on v0.6.277's review prompt is unaffected.

## Implementation

### The check

`check_no_conflict_markers(text, location, errors)` in
`plugins/s/skills/build/scripts/spec_lint.py` reports every line starting
`<<<<<<<` or `>>>>>>>`, naming the file and line number. It is wired into
`lint_master_spec`, `lint_delta_spec`, and `lint_change`'s `plan.md` and
`tasks.md` reads.

**An error, not a warning.** A warning leaves the exit code clean, and the exit
code is what `ci` and every gate read — a warning would reproduce the exact
failure being fixed.

**`=======` is matched only as a whole line.** A markdown setext heading
underlines with repeated `=`, so a prefix match would reject valid documents.
That is the bug this check would otherwise introduce while fixing another, and
it is why the three markers are not treated uniformly.

### The repair

Both live markers sit **inside** requirement bodies — line 1212 at the end of
`board-metrics-view`, line 1607 at the end of `board-scrollbar-theme` — so
removing them changes those two requirements' content hashes. They are repaired
through a MODIFIED delta restating both without the marker line, not by editing
`.shipd/verified/` by hand, because the hash is what `base:` tracking reads.

No content is lost or duplicated: the file has no duplicate `id:`, so the six
bracketed requirements are intact and the markers are stray lines rather than
an unresolved conflict. Verified before planning.

### Version

`plugins/s/.claude-plugin/plugin.json` bumps 0.6.277 → 0.6.278.

## Readiness attestation

### Problem and motivation

The linter cannot detect a conflict marker, and the master library has carried
two for nearly two months while the linter called it valid.

Evidence, measured in this worktree: `grep -c "<<<<<<<\|conflict"
plugins/s/skills/build/scripts/spec_lint.py` was 0 before this change;
`git log -S'<<<<<<< HEAD'` dates the markers to commit `1afdd19`, 2026-08-14;
the markers bracket 6 of the file's 32 requirements; `grep "^id: " | uniq -d`
reports no duplicate, so nothing was lost; and with the check wired in but the
file unrepaired, the linter reports both markers by line number and **exits 1**,
where it previously printed `OK` and exited 0.

### Scope and non-goals

In scope: one new linter check and its wiring, one ADDED requirement, one
MODIFIED delta repairing two requirements, tests, the version bump.

Out of scope: the other library drifts the same review found, the lint modes
for epics and workspace artefacts, and every `/s:review` prose surface.

### Affected capabilities and files

Two capabilities. `shipd-spec-lint` gains `conflict-marker-rejection`.
`delivery-dashboard` has `board-metrics-view` (base `adc2bb6e425a`) and
`board-scrollbar-theme` (base `bdbd762a4163`) restated without their marker
lines, both hashes from `spec_status.py base-hash` here.

Files: `plugins/s/skills/build/scripts/spec_lint.py`,
`plugins/s/skills/build/tests/test_spec_lint.py`,
`plugins/s/.claude-plugin/plugin.json`.

### No open task-shaping decision

- Error or warning: error, because a warning leaves the exit code clean and
  the exit code is the gate — settled above.
- Whether `=======` is matched as a prefix: no, whole line only, because a
  setext heading underline would otherwise be rejected — settled above.
- Hand-edit `verified/` or ship a delta: a delta, because both markers sit
  inside requirement bodies and removing them moves two content hashes —
  settled above.
- How far the check reaches: spec, plan and task files, with the wider lint
  modes named as a non-goal rather than silently skipped — settled above.
