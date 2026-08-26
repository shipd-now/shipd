# change-artefacts
Status: verified

## Idea

Give a planned change an optional `artefacts/` directory that holds the
standalone outputs of planning — a policy markdown, a block of verbatim text —
stored with the change, referenced from its artifacts, and enforced by the
engine.

### Motivation

Planning routinely produces standalone content that does not belong inside the
plan's ~2,000-token budget, and the change layout has no home for it: the only
existing escape hatch parks a design out of tree at `~/.shipd/designs/<change>/`,
so nothing travels with the change into the build, the review, or the archive.

### Details

- Recognize an optional `artefacts/` directory inside a change directory, holding
  standalone planning outputs, each referenced from `plan.md`, `tasks.md`, or a
  delta spec.
- Error in the linter — and therefore refuse the install — on an artefact file no
  artifact references.
- Resolve change-relative artefact references in `tasks.md` against the change
  directory in the context gate.
- List a change's artefacts at the end of `cat change`, paths and sizes only.
- Name artefacts as part of the sub-agent and validator artifact set, and document
  the convention in the content directory's README and the emission guide.

Affected capabilities: `shipd-spec-format`, `spec-io`, `context-gate`,
`shipd-spec-lint`, `shipd-plan`, `build-subagent-handoff` (modified; `context-gate`,
`shipd-spec-lint` and `shipd-plan` gain a requirement). Impact:
`plugins/s/skills/build/scripts/spec_lint.py`,
`plugins/s/skills/build/scripts/spec_gate.py`,
`plugins/s/skills/build/scripts/spec_status.py`, `.shipd/README.md`,
`plugins/s/skills/plan/references/emission.md`, `plugins/s/skills/build/SKILL.md`,
`plugins/s/agents/sub-agent.md`, `plugins/s/agents/validator.md`, and the plugin
version bump; no new dependencies.

### Non-goals

- No artefact directory for epics, research reports, or video briefs — a change
  only.
- No artefact tab in the delivery board's spec-detail modal (`dashboard.py`'s
  `change_artifacts` keeps its plan/spec/tasks tab list).
- No new `cat` verb for reading one artefact — the listing prints resolvable
  paths and readers open them.
- No dangling-reference check beyond the gate's existing task-path check; a plan
  naming an absent artefact is not a new finding.
- No change to `spec_emit.py` or `spec_merge.py` — both already carry an
  `artefacts/` directory (verified below).

## Implementation

- **Storage rides the existing paths untouched.** Verified premise:
  `spec_emit.py change` is a whole-directory `shutil.copytree`, so a staged
  `artefacts/` installs as-is (observed: `exit=0`, landing
  `planned/demo-change/artefacts/policy.md`); `spec_merge.py` archives with
  `shutil.move`, so it travels to `completed/<date>-<change>/artefacts/`
  (observed). Both stay unedited; the change adds a regression test pinning the
  behavior. Rejected: an engine allow-list of staged paths mirroring
  `emit_wiki` — cost without benefit, since nothing today refuses the directory.
- **References are change-relative, and the gate learns to resolve them.**
  Verified premise: a backticked `artefacts/policy.md` in `tasks.md` makes the
  gate exit 2 with "resolves to no existing file or directory", while the
  repo-relative form passes. The change-relative form is the stable one — the
  repo-relative form goes stale the moment the change archives — so
  `_check_task_paths` in `spec_gate.py` gains one narrow resolution step: a token
  beginning `artefacts/` that exists inside the change directory passes, checked
  after the root-relative existence test and before the parent/grandparent
  fallbacks. Narrow by design: only that prefix resolves against the change
  directory, so a mistyped repository path is still a finding. The delta adds a
  requirement rather than modifying the existing check: that check's normative
  text enumerates the placeholder markers the gate itself scans for, so a
  MODIFIED delta restating it would be rejected by the gate reading its own
  change (observed on the first emit attempt of this change).
- **An unreferenced artefact is a lint error, not a warning.** `spec_lint.py`
  gains `check_artefact_references(root, change, errors)`, called from
  `lint_change`: it walks the change's `artefacts/` tree and errors for every
  file whose change-relative POSIX path is absent from the concatenation of
  `plan.md`, `tasks.md`, and every delta spec. Because `spec_emit.py` is
  validate-then-commit, an orphan artefact fails the install outright. This
  follows `traceability-tag-enforcement` ("SHALL error — not warn") rather than
  `context-economy-warning`; the choice was the session's one open decision (see
  Q1). Rejected: a warning — an artefact nothing points at is invisible to every
  downstream reader, which is the failure this change exists to prevent.
- **`cat change` lists, never dumps.** After the existing plan/deltas/tasks
  output, `cmd_cat` prints a `--- artefacts` header and one
  `<root-relative-path> (<n> bytes)` line per artefact, sorted. Presence-based:
  a change with no `artefacts/` directory prints exactly what it prints today, so
  the existing separator scenarios hold unchanged. Rejected: printing contents —
  a verbatim policy text is precisely what the ~2,000-token context-economy
  budget keeps out of `plan.md`, and dumping it into every mediated read
  reintroduces the cost.
- **The name.** `artefacts/`, one letter from the "change artifact set" the repo
  already names — the spelling difference is the disambiguator (user-settled).

Risk: a reader that resolves an artefact by its `planned/<change>/` path finds it
moved after archive. Guarded by the change-relative reference form and by
`cat change`'s completed-fallback, which prints the listing from whichever
directory it resolved.

## Questions and answers

### Q1: How strictly is an unreferenced artefact enforced?
- **Question:** Should the engine enforce that every file in a change's
  `artefacts/` directory is referenced by at least one of `plan.md`, `tasks.md`,
  or a delta spec? Options: (1) lint error, refusing the install via
  validate-then-commit; (2) non-fatal lint warning; (3) no check, convention only.
  Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1 — a lint error. An artefact nothing references is
  invisible to every downstream reader, so it should fail the install exactly as
  a missing traceability tag does. The oracle reported that both candidate
  precedents live in `shipd-spec-lint` — `context-economy-warning` is explicitly
  never an error, `traceability-tag-enforcement` explicitly errors — and that
  neither adjudicates a new file class.
- **Queued:** none (no discoverable workspace to file into)
