# epic-references-shelf
Status: verified
Epic: epic-knowledge

## Idea

Add the optional `## References` epic shelf — one section accepting research,
video, and docs links with resolve-lint — and wire `/s:epic` and `/s:plan` to
install arbitrary supplied documents through the `docs` artifact kind and link
them from that shelf.

### Motivation

An epic admits exactly two reference sections, so `/s:epic` installs supplied
documents through a research-kind workaround (`spec_emit.py research`,
`plugins/s/skills/epic/SKILL.md`) and `/s:plan` has no supplied-document path
at all — a mid-delivery document cannot be linked without pretending to be
research. The sibling `docs-artifact-kind` shipped the storage; this member
adds the shelf that links it (epic `epic-knowledge`).

### Details

- `spec_lint.py lint_epic` validates an optional `## References` section:
  at least one `- [title](path)` entry, each resolving (epic-dir-first, then
  repo-root) to an existing file under `research/`, `video/`, or `docs/`.
- `## Research` and `## Video` keep working unchanged; new authoring records
  consumed reports/briefs/documents under `## References` instead.
- `/s:epic` installs supplied documents via `spec_emit.py docs` (replacing the
  research-kind workaround) and links them from `## References`.
- `/s:plan` gains the same install path; when the change carries `Epic:`, the
  installed document is linked from that epic's `## References` shelf.

Affected capabilities: `shipd-spec-format`, `shipd-spec-lint`, `shipd-epic`,
`shipd-plan` (all modified). Impact:
`plugins/s/skills/build/scripts/spec_lint.py`,
`plugins/s/skills/build/tests/test_spec_lint.py`,
`plugins/s/skills/epic/SKILL.md`, `plugins/s/skills/plan/SKILL.md`,
`plugins/s/harness/references/epic.md`, `plugins/s/harness/bodies/epic.md`,
`plugins/s/harness/bodies/plan.md`, `.shipd/README.md`,
`plugins/s/.claude-plugin/plugin.json` (version bump).

### Non-goals

- No capture rubric and no consult wiring — sibling `epic-capture-rubric`.
- No amendment flow or `epic-amend-check` guard — sibling `epic-amend-flow`.
- No migration of existing epics: `## Research` and `## Video` stay valid
  forever, and no linter finding ever pushes them toward `## References`.
- No `## References` section on `plan.md` — the shelf is epic-only; a plan
  reaches it through its `Epic:` header.
- No exclusivity rules between `## References` and the legacy sections.

## Implementation

- **Lint: generalize the existing helper, no parallel copy.**
  `_check_epic_link_section` (`spec_lint.py:583`) takes its `folder` parameter
  as a tuple of folders; a link resolves when it lands under any of them. The
  two legacy calls pass one-element tuples and their error text stays
  byte-identical ("…under the content directory's research/ folder"); the new
  `lint_epic` call passes `("research", "video", "docs")` with noun
  "reference file" and renders "…under the content directory's research/,
  video/, or docs/ folders". Update the section-lint comment at
  `spec_lint.py:103` and the `lint_epic` docstring. Rejected: a separate
  References checker — three near-identical resolvers would drift.
- **Absent section walks nothing; empty section errors** — exactly the
  existing per-section semantics, inherited from the shared helper.
- **`/s:epic` retargets the supplied-document install** from
  `spec_emit.py research` to `spec_emit.py docs` (same slug-from-title rules,
  same staged-copy title fix for untitled files, originals never edited) and
  records the install under `## References`. Newly authored epics record
  consumed research reports and video briefs under `## References` too (the
  epic's "new authoring prefers `## References`" decision); a pre-existing
  `## Research`/`## Video` section may be extended in place. Template and
  rules blocks in `plugins/s/skills/epic/SKILL.md` gain the References
  contract, mirrored in `plugins/s/harness/references/epic.md` and
  `plugins/s/harness/bodies/epic.md` (lines 24-26 and 59).
- **`/s:plan` links through the parent epic.** A supplied document installs
  via the docs kind during investigation; when the change carries `Epic:`
  resolving in the repo, the skill appends a link entry to that epic's
  `## References` (creating the section when absent) — planning runs in the
  member worktree, so the shelf edit ships on `change/<change>` like any
  member artifact, consistent with the coming amend guard treating References
  as an accreting section. With no epic, the plan cites the document in its
  own prose and edits no epic. Rejected: a References section on `plan.md` —
  the member stub scopes the shelf to epics.
- **Docs kind invocation shape:** `--root` precedes the subcommand. Observed:
  `spec_emit.py --root <r> docs strategy-notes --from <f>` → exit 0,
  "installed docs strategy-notes at …/docs/strategy-notes/doc.md"; trailing
  `--root` is rejected (exit 2). `cat docs <slug>` prints the document.
  Observed: `spec_lint.py --epic demo` on an epic whose `## References`
  carries a dead link exits 0 today — the section is currently unvalidated,
  which is the gap the lint work closes.
- **Version bump** `plugins/s/.claude-plugin/plugin.json` 0.6.180 → 0.6.181,
  per AGENTS.md, in this change.
- Risk: two member branches adding shelf entries to the same epic can
  conflict on merge; accepted — same order of risk as epic status
  derivations, and the section is line-append shaped.
