# supplied-research-docs
Status: verified

## Idea

Let any well-named document install into the content directory's `research/`
folder — citation checks apply only to reports that actually carry citations —
with `/s:epic` installing user-supplied context documents through the engine,
`/s:research` self-labeling its reports with a provenance note, and the build
handoff naming plan-referenced reports as part of the sub-agent's artifact set.

### Motivation

User-supplied context documents (strategy docs, verbatim briefs an epic's
members must build from) cannot enter `research/` through the engine today —
`lint_research` demands the full citation skeleton — so users hand-copy files
into the tree, where no engine verb can read them back. Provenance should not
gate installation: a document only needs to be well named, and `/s:research`
labels its own reports instead.

### Details

- Conditional citation skeleton in `lint_research`: the title check always
  runs; the `## Sources`/marker checks run only when the report carries a
  citation signal (a `## Sources` section or an inline `[n]` marker).
- `/s:research` report grammar gains a provenance note under the title.
- `/s:epic` installs a supplied document not already under `research/` via
  `spec_emit.py research` with a kebab-case slug, then links it in
  `## Research`.
- Build's handoff contract names plan-referenced research reports as part of
  the named artifact set.
- Plugin version bump (`plugins/s/` change).

Affected capabilities: `shipd-spec-lint`, `shipd-spec-format`,
`shipd-research`, `build-subagent-handoff` (modified), `shipd-epic` (added
requirement). Impact: `plugins/s/skills/build/scripts/spec_lint.py`, its
tests, `research/SKILL.md`, `epic/SKILL.md`, `build/SKILL.md`,
`plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No new emit flag, document kind, or content-directory surface —
  `spec_emit.py research <slug> --from <file>` keeps its exact interface.
- The `artefacts/` mechanism and the epic `## Research` link validation
  (`epic-research-link-validation`) are unchanged.
- No retroactive migration of files hand-copied into other repositories'
  `research/` folders.

## Implementation

- **Conditional skeleton rule.** Enforcement of the citation skeleton triggers
  when the report carries either signal: a `## Sources` section, or at least
  one inline `[n]` marker outside fenced code. Once triggered, every check
  runs exactly as today (section present with at least one numbered entry, at
  least one marker, all markers resolving). A titled report with neither
  signal installs clean. Rejected alternative: a `--supplied` emit flag — the
  caller would have to declare provenance, which the user explicitly ruled
  out as a gate ("it shouldn't matter where it's from").
- **Runnable premise (verified).** `spec_emit.py --root probe research
  supplied-doc --from doc.md` on a titled, uncited document exits 1 today
  with the findings "report.md has no `## Sources` section" and "report.md
  has no inline `[n]` citation markers", installing nothing. This change
  flips that invocation to a clean exit-0 install.
- **Provenance note.** The research skill composes
  `> Prepared by the shipd research skill (/s:research).` directly under the
  title line. Skill convention only — the linter never checks it, so nothing
  blocks reports composed before this change.
- **Epic install step.** Slug derived from the document's level-1 title, or
  from the filename when untitled — kebab-case, matching
  `research-report-emission`'s convention. An untitled document is staged as
  a copy with a prepended `# <title>` derived from the filename (the user's
  original file is never edited). Install goes through the engine; a raw copy
  into the spec tree stays forbidden.
- **Handoff sentence.** A research report `plan.md`'s `## Implementation`
  names (by its content-directory `research/` path) joins the named artifact
  set as a read-only reference, traveling by path — same pattern and same
  section-qualifier as the design scratch directory: `## Implementation` is
  where binding references live, so a mention under `### Motivation` or the
  Q&A ledger stays provenance, not a forced read.
- **Version bump** `plugins/s/.claude-plugin/plugin.json` 0.6.162 → 0.6.163,
  same PR, per AGENTS.md.

Risk: an uncited document now lands in `research/` silently, so a buggy
`/s:research` run that drops its `## Sources` section would install. Guard:
the skill contract (`research-report-content`) still mandates the full
skeleton for composed reports, and any report that cites at all still gets the
full checks — only a report with zero citation signals skips them.
