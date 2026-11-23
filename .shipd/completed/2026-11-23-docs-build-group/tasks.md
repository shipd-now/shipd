# Tasks — docs-build-group

Every task follows `plan.md` §Implementation: read
`plugins/s/skills/document/references/standard.md` first, apply the main-page
shape, state only behaviour confirmed in the named source, and link only to
files present under `docs/`. "Lint" means
`python3 plugins/s/skills/document/scripts/docs_lint.py <file>` exits 0.

## 1. Reshape the existing pages

- [x] 1.1 [req: guardrails-key-docs] Reorder `docs/guardrails.md` into the
      main-page shape, moving content without re-deriving it: keep the intro;
      add `## When to use it` holding the deny-for-certain /
      remind-for-fuzzy guidance; add `## How to run it` with add, edit, and
      override as numbered steps; put hook events, the rule file format with
      its worked example, sources with the built-ins table, cooldown,
      kill-switches with `SHIPD_GUARDRAILS=off` and the superseded `rules`
      note, and token cost as level-3 sections under `## Reference`; move the
      `## See also` links into `## Reference` and drop that heading. Keep `<!-- doc-type: reference -->` on line 1.
      Lint the file and confirm 250 lines or fewer.
- [x] 1.2 [req: supersession-gate-doc] Reorder `docs/supersession-gate.md`
      into the main-page shape: keep the intro; rename the Phase-0 section to
      `## When to use it`, keeping the three steps and three outcomes; rename
      `## Running the check yourself` to `## How to run it`, keeping the `check-base` invocation and
      sample output; move the findings table and the exit codes under
      `## Reference`. Keep `<!-- doc-type: concept -->` on line 1 and add no
      diagram. Lint the file and confirm 100 lines or fewer.

## 2. Write the new pages

- [x] 2.1 [req: worktree-user-docs] Create `docs/worktrees.md`, titled
      `# Worktrees and hooks`, with `<!-- doc-type: how-to -->` on line 1,
      from `plugins/s/bin/shipd worktree --help` and
      `plugins/s/skills/worktree-hooks/SKILL.md`, covering the content
      `plan.md` lists for it. Put the verb table (`remove`, `prune-branches`,
      `sweep`, `hooks list|add|remove|run|trust`) under `## Reference`. Give
      each config key one sentence and a link to `customise.md`. Add no
      diagram. Lint the file and confirm 150 lines or fewer.
- [x] 2.2 [req: fix-user-docs] Create `docs/fix.md`, titled `# Fix a bug`,
      with `<!-- doc-type: how-to -->` on line 1, from
      `plugins/s/skills/fix/SKILL.md`, covering the content `plan.md` lists
      for it. Put the report parts under `## Reference`. Add no diagram. Lint
      the file and confirm 150 lines or fewer.
- [x] 2.3 [req: drive-demo-user-docs] Create `docs/drive-and-demo.md`,
      titled `# Drive a browser and record a demo`, with
      `<!-- doc-type: how-to -->` on line 1, from
      `plugins/s/skills/drive/SKILL.md`, `plugins/s/skills/demo/SKILL.md`,
      and `python3 plugins/s/skills/drive/scripts/drive.py --help`, covering
      the content `plan.md` lists for it. Put a `drive.py` verb table under
      `## Reference`, naming only verbs the help output lists. Add no
      diagram. Lint the file and confirm 150 lines or fewer.
- [x] 2.4 [req: build-user-docs] Create `docs/build.md`, titled
      `# Build a change`, with `<!-- doc-type: how-to -->` on line 1, from
      `plugins/s/skills/build/SKILL.md`, covering the content `plan.md` lists
      for it, with the run as numbered steps and exactly one `mermaid`
      flowchart of the branched lifecycle. Under `## Reference` put a PR
      mode table (`auto`, `draft`) with a link to `customise.md` for the
      `pr-mode` key, and links to `supersession-gate.md`, `guardrails.md`,
      `worktrees.md`, and `fix.md`. Lint the file and confirm 150 lines or
      fewer.
- [x] 2.5 [req: supersession-gate-doc] In `docs/supersession-gate.md`, add
      one link to `build.md` where the page first names `/s:build`. Lint the
      file and confirm 100 lines or fewer.

## 3. Verify

- [x] 3.1 [req: *] Run the `Lint docs` step body from
      `.github/workflows/ci.yml` locally and confirm exit 0. Confirm with
      `wc -l` that each of the six pages sits within its cap. Confirm every
      relative link in the six pages resolves to an existing file. Confirm
      `git status --short` lists only the six files under `docs/` plus the
      change's own artifacts. Run `plugins/s/bin/shipd lint docs-build-group`
      and confirm it reports the change clean.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 126 | 47.1k |
| Write | 15 | 22.7k |
| SubagentHandback | 5 | 10.4k |
| Agent | 8 | 3.9k |
| Read | 31 | 3.7k |
| Edit | 8 | 2.1k |
| Monitor | 2 | 935 |
| ToolSearch | 3 | 643 |
| (no tool) | 0 | 597 |
| **Total** | 198 | 92.0k |
