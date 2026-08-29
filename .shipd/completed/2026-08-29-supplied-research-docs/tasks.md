# Tasks — supplied-research-docs

## 1. Engine — conditional citation skeleton

- [x] 1.1 [req: research-report-validation] Add tests to
      `plugins/s/skills/build/tests/test_spec_lint.py`: a report whose first
      line is a non-empty `# <title>` with no `## Sources` section and no
      `[n]` markers produces no findings from `lint_research`; a report with
      markers but no `## Sources` section still produces the missing-section
      finding; a cited report with an unresolved `[4]` marker still produces
      the naming finding; the existing library-lint-ignores-research behavior
      stays covered.
- [x] 1.2 [req: research-report-validation] Rework `lint_research` in
      `plugins/s/skills/build/scripts/spec_lint.py`: always check the title
      line; compute the citation signal (a `## Sources` section present, or
      at least one marker from `_citation_markers_outside_code`); run the
      Sources/marker/resolution checks only when the signal is present.
      Update the docstring to state the conditional rule. Stdlib-only.
- [x] 1.3 [req: research-report-format] Add an emit-level test to
      `plugins/s/skills/build/tests/test_spec_emit.py`: `spec_emit.py
      research <slug> --from <file>` on a titled, uncited document exits 0
      and installs `research/<slug>/report.md`; an untitled document still
      fails with the title finding.

## 2. Skills — provenance note, epic install step, build handoff

- [x] 2.1 [req: research-report-content] In
      `plugins/s/skills/research/SKILL.md`, add the provenance note to the
      report grammar: directly under the title line, compose
      `> Prepared by the shipd research skill (/s:research).` — and adjust
      the citation-skeleton wording to note the engine accepts uncited
      documents while `/s:research` reports are always fully cited.
- [x] 2.2 [req: epic-supplied-document-install] In
      `plugins/s/skills/epic/SKILL.md`, extend the supplied-research
      pre-read: a supplied document not already under the content
      directory's `research/` folder is installed via `spec_emit.py research
      <slug> --from <file>` with a kebab-case slug from its title (filename
      when untitled, staging a copy that prepends `# <title>` and leaving
      the original untouched), then linked in `## Research` like any other
      consumed report. Never a raw copy into the spec tree.
- [x] 2.3 [req: artifact-compiled-context-handoff] In
      `plugins/s/skills/build/SKILL.md`'s handoff contract (the "named
      artifact set" paragraph), add the research-report sentence: a research
      report `plan.md` names by its content-directory `research/` path is
      part of the named artifact set, read as a read-only reference,
      traveling by that path and never as spawn-message content.

## 3. Ship

- [x] 3.1 [req: epic-supplied-document-install] Bump
      `plugins/s/.claude-plugin/plugin.json` version to `0.6.163` (plugin
      cache snapshot is keyed by version; `plugins/s/` changed, and the epic
      install step goes live only through a snapshot refresh).
- [x] 3.2 [req: research-report-validation] Run
      `python3 -m pytest plugins/s/skills/build/tests/ -q` (no
      `textual`/`pydantic` installed) and fix any failure before shipping.

## 4. Follow-up — sub-agent surface

- [x] 4.1 [req: artifact-compiled-context-handoff] In
      `plugins/s/agents/sub-agent.md`, add a named-artifact-set bullet
      mirroring the design-scratch and `artefacts/` bullets: when `plan.md`'s
      `## Implementation` names an installed research report by its
      content-directory `research/` path, read it as a **read-only**
      reference; where none is named, this step is a no-op.
- [x] 4.2 [req: artifact-compiled-context-handoff] In
      `plugins/s/skills/build/SKILL.md`'s handoff paragraph, qualify the
      research-report sentence to match the requirement and the sibling
      design-scratch sentence: a report `plan.md`'s `## Implementation` names
      by its content-directory `research/` path (not a mention anywhere in
      `plan.md`) is the one that joins the named artifact set.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 171 | 25.3k |
| (no tool) | 0 | 5.4k |
| Edit | 19 | 5.3k |
| Read | 37 | 2.1k |
| Agent | 6 | 1.7k |
| SendMessage | 3 | 961 |
| ToolSearch | 3 | 238 |
| Monitor | 2 | 33 |
| **Total** | 241 | 41.0k |
