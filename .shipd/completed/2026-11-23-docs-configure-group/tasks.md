# Tasks — docs-configure-group

Every task follows `plan.md` §Implementation: read
`plugins/s/skills/document/references/standard.md` first, write through the
`/s:document` flow, apply the main-page shape and the fact-owner table, and
link only files present under `docs/` on the branch. "Lint" means
`python3 plugins/s/skills/document/scripts/docs_lint.py <file>` exits 0.

## 1. Write the new pages

- [x] 1.1 [req: harness-user-docs] Create `docs/harnesses.md`, titled
      `# Harnesses`, with `<!-- doc-type: how-to -->` on line 1. Sources:
      `README.md` section "Harness mode", `docs/customise.md` section "The
      harness", and `plugins/s/bin/shipd harness --help`. Cover every item
      the `harness-user-docs` requirement lists, with the run as numbered
      steps. Under `## Reference` put the verb table (`list`, `show`, `add`,
      `remove`, `status`), the flag table (`--all`, `--root`, `--user`,
      `--force`, `--json`), and a link to `harness-agents-reference.md`.
      Link `customise.md`. Write `shipd install` as inline code. Add no
      diagram and no table of every harness. Lint the file and confirm 150
      lines or fewer.
- [x] 1.2 [req: statusline-telemetry-user-docs] Create
      `docs/statusline-and-telemetry.md`, titled
      `# Statusline and telemetry`, with `<!-- doc-type: how-to -->` on line
      1. Sources: `README.md` sections "Statusline" and "Build telemetry",
      `plugins/s/bin/shipd statusline --help`,
      `plugins/s/bin/shipd metrics --help`, and requirement
      `statusline-rendering` in `.shipd/verified/statusline/spec.md` for the
      three segments. Cover every item the `statusline-telemetry-user-docs`
      requirement lists. Under `## How to run it` use the level-3 headings
      `### Register the statusline`, `### Read the build report`, and
      `### Read the delivery metrics`. Under `## Reference` put the segment
      table, the flag table, and the report settings table with defaults.
      Leave out the `spec_status.py use` command and the by-hand JSON
      registration. Link `customise.md`; write `/s:build` as inline code.
      Add no diagram. Lint the file and confirm 150 lines or fewer.
- [x] 1.3 [req: doctor-user-docs] Create `docs/doctor.md`, titled
      `# Doctor`, with `<!-- doc-type: how-to -->` on line 1. Sources:
      `plugins/s/skills/doctor/SKILL.md`, `plugins/s/bin/shipd doctor
      --help`, the lines of a `plugins/s/bin/shipd doctor` run, and
      `docs/cheatsheet.md` section "`doctor --fix`". Cover every item the
      `doctor-user-docs` requirement lists, with the `/s:doctor` run as
      numbered steps. Under `## Reference` put one table with a row per
      check the run reports, and one table of the findings `/s:doctor`
      remedies on consent, from the skill's remedy table rows marked
      "Runnable on consent". Link `copilot-review.md`,
      `statusline-and-telemetry.md`, and `customise.md`. Name no
      `semdiff.py` path; describe that remedy as the review engine's
      installer for `difft`. Add no diagram. Lint the file and confirm 150
      lines or fewer.
- [x] 1.5 [req: document-user-docs] Create `docs/document.md`, titled
      `# Write docs`, with `<!-- doc-type: how-to -->` on line 1. Sources:
      `plugins/s/skills/document/SKILL.md` (the flow, and "What this skill
      never does") and `plugins/s/skills/document/references/standard.md`
      (the doc types, the caps, the diagram rule). Cover every item the
      `document-user-docs` requirement lists, with the run as numbered
      steps. Under `## Reference` put the doc-type table with the three
      caps and the diagram rule. Name no `docs_lint.py` path; describe the
      lint as a step the skill runs. Add no diagram. Lint the file and
      confirm 150 lines or fewer.
- [x] 1.4 [req: statusline-telemetry-user-docs] In
      `docs/statusline-and-telemetry.md`, add one link to `doctor.md` where
      the page says the `statusline` check reports the registration. Lint
      the file and confirm 150 lines or fewer.

## 2. Reshape the existing pages

- [x] 2.1 [req: customisation-guide] Reorder `docs/customise.md` into the
      main-page shape, moving content without re-deriving it. Keep
      `<!-- doc-type: reference -->` on line 1, the title, and the intro.
      Add `## When to use it`: reach for this page to change where files
      live, which steps a delivery runs, or how a change ships. Add
      `## How to run it` holding, in order: `/s:init` with its seven section
      arguments (`layout`, `config`, `workspace`, `wiki`, `memory`, `hooks`,
      `gate`), from `plugins/s/skills/init/SKILL.md`; `shipd init` and
      `shipd init status`, from `plugins/s/bin/shipd --help`; then the two
      existing `shipd config` code blocks and the paragraph that starts
      "`config set` writes to the layer". Delete the sentence that names
      `spec_status.py config-show`. Add `## Reference` and demote these
      sections to level 3 under it: "The configuration file and its
      layering" (keeping its first paragraph and the sentence on a workspace
      root's config), "The recognized keys", "The
      delivery steps", "The file-authored surfaces", "The harness", "The
      environment overrides", and "The limits", in that order. Delete `## See also`; keep the links to `../.shipd/README.md`
      and `guardrails.md` inside the Reference prose that names them. Keep
      every row of the key table. Lint the file and confirm 250 lines or
      fewer.
- [x] 2.2 [req: customisation-guide] In `docs/customise.md`, replace the
      body of `### The harness` with one sentence: a harness registry decides
      which agent surfaces receive the `/s:` commands, linking
      `harnesses.md`. In the key table's `build` row, add a link to
      `statusline-and-telemetry.md` for the report settings and their
      defaults. In the `statusline` row, add the same link. Lint the file.
      Run
      `python3 -m unittest plugins/s/skills/build/tests/test_config_sample.py`
      and confirm it passes.
- [x] 2.3 [req: agent-surface-docs] In `docs/harness-agents-reference.md`,
      replace the intro sentence that links `customise.md` with one saying
      [Harnesses](harnesses.md) covers the registry and the command surface.
      In "The verbs", replace the paragraph that starts "When you install
      and enable the `s@shipd` plugin" with one sentence saying the plugin
      already provides the Claude Code user surface, linking `harnesses.md`.
      Keep every table, the `status` paragraph, and "Adding a harness". Lint
      the file and confirm 250 lines or fewer.

## 3. Verify

- [x] 3.1 [req: *] Run the `Lint docs` step body from
      `.github/workflows/ci.yml` locally and confirm exit 0. Confirm with
      `wc -l` that each of the six pages sits within its cap. Confirm every
      relative link in the six pages resolves to an existing file. Run
      `grep -nE "spec_status\.py|statusline\.sh|build_report\.py|metrics\.py|semdiff\.py" docs/harnesses.md docs/statusline-and-telemetry.md docs/doctor.md docs/document.md`
      and confirm no match. Confirm `grep -c '```mermaid'` reports 0 for
      each of the six pages. Run
      `python3 -m unittest plugins/s/skills/build/tests/test_config_sample.py`
      and confirm it passes. Confirm `git status --short` lists only the
      six files under `docs/` plus the change's own artifacts. Run
      `plugins/s/bin/shipd lint docs-configure-group` and confirm it reports
      the change clean.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 148 | 76.7k |
| Write | 7 | 13.2k |
| SubagentHandback | 6 | 12.4k |
| Read | 22 | 2.8k |
| Agent | 6 | 2.7k |
| Edit | 4 | 1.4k |
| (no tool) | 0 | 88 |
| Skill | 1 | 51 |
| **Total** | 194 | 109.4k |
