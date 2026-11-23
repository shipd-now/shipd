# Tasks — docs-plan-group

Write every page through `/s:document` (load the `s:document` skill, or read
`plugins/s/skills/document/SKILL.md` and follow it). `plan.md`
§Implementation holds the binding type, cap, shape, fact-owner, command, and
link rules. Take facts only from the source files that section names.

## 1. Reshape the PRD pages

- [x] 1.1 [req: prd-user-docs] Edit `docs/prd-reference.md`: in the section
      "The epic's `PRD:` link", replace the closing paragraph that starts
      "The link runs one way only" with one sentence saying the link runs one
      way, linking `prd.md`. Keep `## See also` and every other fact. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/prd-reference.md`
      until it exits 0.
- [x] 1.2 [req: prd-user-docs] Rewrite `docs/prd.md` into the main-page
      shape, keeping `<!-- doc-type: concept -->` on line 1: keep the
      opening, `## The hierarchy` with its mermaid fence, and
      `## Where a PRD lives`; add `## When to use it` (write a PRD when the
      problem, its users, or the success measure are unsettled before a
      feature is decomposed; go straight to `/s:epic` or `/s:plan` when they
      are settled), sourced from `plugins/s/skills/prd/SKILL.md`; rename
      `## Writing one` to `## How to run it`; delete `## Lifecycle and tiers`
      and `## See also`; close with `## Reference`, which links
      `prd-reference.md` and names the three statuses and the three tiers in
      one sentence each. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/prd.md`
      until it exits 0 at 100 lines or fewer.

## 2. Write the new pages

- [x] 2.1 [req: research-user-docs] Create `docs/research.md` with
      `<!-- doc-type: how-to -->` on line 1 and the title `# Research`,
      covering every item the `research-user-docs` requirement lists, in the
      main-page shape. Source: `plugins/s/skills/research/SKILL.md`. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/research.md`
      until it exits 0 at 150 lines or fewer.
- [x] 2.2 [req: video-ingest-user-docs] Create `docs/video-ingest.md`
      with `<!-- doc-type: how-to -->` on line 1 and the title
      `# Video ingest`, covering every item the `video-ingest-user-docs`
      requirement lists, in the main-page shape, with one sentence linking
      `plan.md` for planning from a recording. Source:
      `plugins/s/skills/video-ingest/SKILL.md`. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/video-ingest.md`
      until it exits 0 at 150 lines or fewer.
- [x] 2.3 [req: duck-user-docs] Create `docs/duck.md` with
      `<!-- doc-type: how-to -->` on line 1 and the title `# Rubber duck`,
      covering every item the `duck-user-docs` requirement lists, in the
      main-page shape, with the exit map as the `## Reference` table.
      Source: `plugins/s/skills/duck/SKILL.md`. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/duck.md`
      until it exits 0 at 150 lines or fewer.
- [x] 2.4 [req: plan-user-docs] Create `docs/plan.md` with
      `<!-- doc-type: how-to -->` on line 1 and the title `# Plan a change`,
      covering every item the `plan-user-docs` requirement lists, in the
      main-page shape. Under `## How to run it` use the level-3 headings
      `### Plan a change`, `### Enrich a rejected change`, and
      `### Walk a risky plan`. Sources: `plugins/s/skills/plan/SKILL.md`,
      `plugins/s/skills/plan-deep/SKILL.md`,
      `plugins/s/skills/status/SKILL.md`, and `README.md` lines 303-403 (the
      directory tree and "Lifecycle"). Link `oracle.md`, `video-ingest.md`,
      `research.md`, `duck.md`, `prd.md`, and `../.shipd/README.md`; write
      `/s:build`, `/s:epic`, and `/s:autopilot` as inline code with no link.
      Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/plan.md`
      until it exits 0 at 150 lines or fewer.

## 3. Verify the group

- [x] 3.1 [req: *] Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/prd.md docs/prd-reference.md docs/research.md docs/video-ingest.md docs/duck.md docs/plan.md`
      and confirm exit 0. Confirm every relative link in the six files
      resolves to a file in the worktree. Run
      `grep -nE "spec_(status|emit|gate)\.py|video_ingest\.py" docs/prd.md docs/prd-reference.md docs/research.md docs/video-ingest.md docs/duck.md docs/plan.md`
      and confirm no match. Run `git status --short` and confirm only those
      six files under `docs/` changed outside the content directory.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 110 | 40.2k |
| Write | 15 | 22.7k |
| SubagentHandback | 4 | 7.5k |
| Read | 30 | 3.5k |
| Agent | 7 | 3.4k |
| Edit | 8 | 2.1k |
| Monitor | 2 | 935 |
| ToolSearch | 3 | 643 |
| (no tool) | 0 | 597 |
| **Total** | 179 | 81.6k |
