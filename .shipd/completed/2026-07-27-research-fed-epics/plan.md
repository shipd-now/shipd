# research-fed-epics
Status: verified
Epic: autonomous-delivery

## Idea

Epics have no way to carry the research behind them. The autonomous-delivery
epic reserves `.shipd/research/` for cited research reports, but an epic cannot
reference them, so research context is invisible to member planning and to
readers of the epic — and `/s:epic` has no door for consuming a report as
pre-investigation context.

This change associates research with epics, deliberately minimally:

- Epics gain an **optional `## Research` section**: a markdown list of links
  to files under the content dir's `research/` folder.
- Epic lint validates the section when present: every link must resolve to an
  existing research file; an empty section is an error.
- `/s:epic` reads any supplied or listed reports as pre-investigation
  context and records them in the section.

### Non-goals

- No `Research:` header key, no setter verb — the section is ordinary epic
  content authored through the existing emission path.
- No research report *format* definition and no producer — the report
  grammar and the `/s:research` skill belong to the `deep-research-skill`
  member; any file under `research/` is linkable.
- No lint walking of `research/` itself — files there are validated only
  when an epic links them.

Affected capabilities: `shipd-spec-format` (modified — new requirement),
`shipd-spec-lint` (modified — new requirement), `shipd-epic` (modified — new
requirement). Impact: `plugins/s/skills/build/scripts/spec_lint.py` and its
tests, `plugins/s/skills/epic/SKILL.md`, `.shipd/README.md` epic grammar
blurb, plugin version bump.

## Implementation

- **Section grammar.** `## Research` is optional. When present it holds at
  least one markdown list entry (`- [title](path)`, trailing annotation
  prose allowed after the link). Rejected: a `Research:` header key — forces
  single-value grammar and a dedicated header-write verb; the section
  supports many reports with zero new machinery.
- **Link resolution.** Lint resolves each link target first relative to the
  epic's own directory (standard markdown semantics, GitHub-clickable),
  then relative to the repo root as a convenience; the resolved file must
  exist under `<content-dir>/research/`. Unresolvable or out-of-tree links
  are errors naming the link. A `## Research` section with no link entries
  is an error.
- **Where it lands in the linter.** A new check in `spec_lint.py`'s epic
  validation path (runs in both `--epic` mode and library linting), beside
  the existing section/stub-table checks; resolution uses the existing
  `specs_dirname` config helpers — no new path convention is hardcoded.
- **Skill consumption is path-legal.** `/s:epic` reads the files the
  section links; the path comes from authored artifact content, not from
  convention, so the spec-io no-constructed-paths rule is satisfied without
  a new `cat` mode.
- **Docs ride along**: epic SKILL.md gains the section in its epic contract
  plus the read-reports-first instruction; `.shipd/README.md`'s epic grammar
  mentions the optional section; plugin version bumps one patch.

Risk: link-resolution ambiguity between epic-relative and root-relative
forms; guarded by trying both deterministically (epic dir first) and by
tests covering each form plus the failure modes.
