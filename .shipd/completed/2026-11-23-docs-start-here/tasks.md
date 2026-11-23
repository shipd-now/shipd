# Tasks — docs-start-here

Every task follows `plan.md` §Implementation: read
`plugins/s/skills/document/references/standard.md` first, write through the
`/s:document` flow, and keep the fact-owner table. "Lint" means
`python3 plugins/s/skills/document/scripts/docs_lint.py <file>` exits 0.

## 1. Check the link targets

- [x] 1.1 [req: *] Run `ls` on these twenty files and confirm each exists:
      `docs/plan.md`, `docs/research.md`, `docs/video-ingest.md`,
      `docs/duck.md`, `docs/build.md`, `docs/fix.md`, `docs/worktrees.md`,
      `docs/drive-and-demo.md`, `docs/epics.md`, `docs/epic-grill.md`,
      `docs/autopilot.md`, `docs/drift.md`, `docs/initiatives.md`,
      `docs/pr.md`, `docs/wiki.md`, `docs/memory.md`, `docs/harnesses.md`,
      `docs/statusline-and-telemetry.md`, `docs/doctor.md`, `docs/document.md`.
      Confirm
      `docs/room-run.md` exists and `docs/pr-room.md` does not. If any check
      fails, stop and report the missing file; the eight feature groups have
      not all merged, and no later task may run.

## 2. Write the new pages

- [x] 2.1 [req: install-user-docs] Create `docs/install.md`, titled
      `# Install`, with `<!-- doc-type: how-to -->` on line 1. Sources:
      `README.md` sections "Install mode", "Per-repo mode (vendor shipd into
      a repository)", and "Dev mode (working on shipd itself)";
      `plugins/s/bin/shipd install --help`; and the output of bare
      `plugins/s/bin/shipd vendor`. Use the level-2 headings
      `## When to use it`, `## How to run it`, and `## Reference`, and under
      `## How to run it` the five level-3 headings the `install-user-docs`
      requirement names, in its order. Cover every item that requirement
      lists. Under `## Reference` put the four-row table of surfaces
      `shipd vendor add` writes and a three-row verb table (`install`,
      `update [--check]`, `vendor [add|remove]`). Link `getting-started.md`,
      `doctor.md`, and `harnesses.md`. Leave out the launcher's
      version-ordering detail, `SHIPD_PLUGIN_CACHE`, the raw GitHub URL, and
      the animated wordmark. Add no diagram. Lint the file and confirm 150
      lines or fewer.
- [x] 2.2 [req: core-ideas-doc] Create `docs/core-ideas.md`, titled
      `# Core ideas`, with `<!-- doc-type: concept -->` on line 1. Sources:
      `docs/what-is-shipd.md`, `.shipd/README.md`, `README.md` section "The
      spec engine", and the pages this task links. Open with one paragraph
      that says the page defines shipd's terms and links
      `what-is-shipd.md` for the overview diagram. Then write the seven
      level-2 sections the `core-ideas-doc` requirement names, in its order,
      defining each listed term in three sentences or fewer and linking the
      page the requirement pairs with it. Link the content directory's
      `README.md` as `../.shipd/README.md`. Close the last section with one
      sentence that links `cheatsheet.md` as the command list. Add no table,
      no code fence, and no diagram. Lint the file and confirm 100 lines or
      fewer.

## 3. Update the existing pages

- [x] 3.1 [req: first-change-guide-owners, install-mode-docs, pipeline-follower-docs, harness-mode-docs]
      Edit `docs/getting-started.md`. Change the title to
      `# Your first change`. Keep every level-2 heading as it is. In
      `## 1. Install`, keep the `curl` command and the sentence that says
      what it sets up, add one sentence that links `install.md` for
      updates, harnesses, and the other install modes, and delete the PATH
      block, the auto-update paragraph, and the harness paragraph. In
      `## 2. Preflight: \`shipd doctor\``, keep the command, the closing
      `doctor: ok` line, and the rule that only a `fail` line blocks; replace
      the list of check names and the `--fix` sentence with one sentence
      that links `doctor.md`; keep the paragraph that shows
      `{"autonomous-pipeline": "eco"}` and links `customise.md`. In step 4
      add a link to `plan.md`; in step 5 a link to `build.md`; in step 6 a
      link to `statusline-and-telemetry.md` after the statusline paragraph.
      In `## Where to go next`, keep the three entries and add
      `[Core ideas](core-ideas.md)` with a one-line description. Lint the
      file and confirm 150 lines or fewer.
- [x] 3.2 [req: entry-docs-standard] Edit `docs/what-is-shipd.md`. In the
      mermaid fence change `subgraph ship [Ship]` to
      `subgraph ship [Review and merge]` and change nothing else in the
      fence. Change the link text `Getting started` to `Your first change`,
      and extend that sentence so it also links
      `[Core ideas](core-ideas.md)` as the page that defines the terms. Keep
      the paragraph that links `multi-agent-pr.md` and the closing "Today
      shipd builds itself" paragraph where they are. Lint the file and
      confirm 100 lines or fewer.
- [x] 3.3 [req: cheatsheet-page-links] Edit the rows of `docs/cheatsheet.md`.
      Add a `/s:demo` row after the `/s:build` row: description "Produce a
      branded demo video of a browser or terminal subject.", example
      `/s:demo Record the checkout flow`. Add `s:demo` after `s:drive` in
      the "Spec, build, ship" list entry. Add a `room <verb> <pr>` row after
      the `worktree` row: description "The pull request's room: `join`,
      `list`, `message`, `close`, `watch`, `whoami`, `run`. Needs a pull
      request and a signed-in `gh`.", example `shipd room list 412`. Add a
      `gate rules [apply]` row after the `copilot` row: description "Report,
      or apply, the repository's merge-rules ruleset.", example
      `shipd gate rules`. Change the `copilot` row's form to
      `copilot [add\|update\|remove] [--force]`, the `workspace` row's to
      `workspace [init\|sync\|team]` with "`team` builds a nested team
      workspace" added to its description, and the `config` row's to
      `config [set\|unset\|check]` with "`set` and `unset` change a key;
      `check` validates every layer" added to its description.
- [x] 3.4 [req: cheatsheet-page-links] In `docs/cheatsheet.md`, end each
      row's description cell with one link to the page the
      `cheatsheet-page-links` requirement assigns that command, written as
      `See [<the target page's level-1 title>](<file>).` Leave the `/s:room`
      row's existing `multi-agent-pr.md` link as it is and add no second
      link to it.
- [x] 3.5 [req: cheatsheet-page-links] In `docs/cheatsheet.md`, delete the
      `## \`doctor --fix\`` section and its body, and change the intro's link
      text `Getting started` to `Your first change`. Lint the file and
      confirm 250 lines or fewer.
- [x] 3.6 [req: feature-page-cross-links] Sweep the feature main pages for
      cross-group links. The pages are the twenty files task 1.1 lists, plus
      `docs/prd.md`, `docs/guardrails.md`, `docs/supersession-gate.md`,
      `docs/semantic-review.md`, `docs/copilot-review.md`,
      `docs/multi-agent-pr.md`, `docs/room-run.md`, `docs/agent-identity.md`,
      `docs/oracle.md`, `docs/customise.md`, `docs/workspaces.md`, and the
      part pages under `docs/workspaces/`. On each page, find the first
      mention, in prose or a table cell, of each `/s:` skill or `shipd`
      verb that another page owns under `cheatsheet-page-links`. Turn that
      mention into a link to the owner page, keeping the inline code as the
      link text. Skip headings, code fences, and a page's own commands. Add
      at most one link per owner page, and reword nothing else. When a link
      pushes a page over its cap, rewrap that paragraph to 100 columns; when
      that is not enough, leave that mention unlinked and name it in the
      build report. Lint every swept page.

## 4. Verify

- [x] 4.1 [req: *] Run the `Lint docs` step body from
      `.github/workflows/ci.yml` locally and confirm exit 0. Confirm with
      `wc -l` that each of the five pages sits within its cap. Confirm every
      relative link in the five pages resolves to an existing file. Compare
      the `/s:` table's rows with `ls plugins/s/skills` and the `shipd`
      table's rows with `plugins/s/bin/shipd --help`; confirm one row per
      name on each side. Run `plugins/s/bin/shipd gate rules` and confirm
      exit 0. Run
      `grep -n "autoUpdate\|shipd update\|harness add" docs/getting-started.md`
      and confirm no match. Run
      `python3 -m unittest plugins/s/skills/room/tests/test_room_skill.py plugins/s/skills/pr/tests/test_pr_skill.py plugins/s/skills/build/tests/test_init_skill_contract.py plugins/s/skills/build/tests/test_drift_skill_contract.py plugins/s/skills/build/tests/test_plan_deep_skill_contract.py`
      and confirm it passes. Confirm `git status --short` lists only files
      under `docs/` plus the change's own artifacts, and that
      `git diff --stat` shows the swept feature pages changing by link
      additions only. Run
      `plugins/s/bin/shipd lint docs-start-here` and confirm it reports the
      change clean.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 60 | 33.0k |
| SubagentHandback | 2 | 6.3k |
| Write | 2 | 3.1k |
| Agent | 3 | 2.1k |
| Read | 5 | 819 |
| Edit | 1 | 172 |
| (no tool) | 0 | 122 |
| **Total** | 73 | 45.6k |
