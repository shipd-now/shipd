# Tasks — docs-workspaces-group

Every docs task follows `plan.md` §Implementation: read
`plugins/s/skills/document/references/standard.md` first, write through the
`/s:document` flow, apply the main-page shape and the fact-owner table, move
content without re-deriving it, and link only files present under `docs/` on
the branch. "Lint" means
`python3 plugins/s/skills/document/scripts/docs_lint.py <file>` exits 0.

## 1. Guard test

- [x] 1.1 [req: workspaces-doc, workspaces-doc-examples] In
      `plugins/s/skills/build/tests/test_workspace_team.py`, class
      `WorkspaceGuideDriftTests`: rename
      `test_teams_and_multi_workspace_repos_name_the_team_verb` to
      `test_teams_page_names_the_team_verb` and make it read only
      `teams.md`. Add `test_part_pages_are_the_six_named`, asserting that the
      sorted `.md` names in `WORKSPACES_DOCS_DIR` equal
      `["external-stores.md", "getting-started.md", "headless.md",
      "member-map.md", "nesting.md", "teams.md"]`. Change the class
      docstring to say `teams.md` names the wizard. Run
      `python3 -B -m unittest plugins/s/skills/build/tests/test_workspace_team.py`
      and observe the new test fail.

## 2. Split nesting and stores

- [x] 2.1 [req: workspaces-doc] Create `docs/workspaces/nesting.md`, titled
      `# Nesting job workspaces`, with `<!-- doc-type: how-to -->` on line 1
      and the back link `[← Workspaces](../workspaces.md)`. Source:
      `docs/workspaces/nesting-and-stores.md` section "Nesting job
      workspaces". Opening: that section's first paragraph. Add
      `## When to use it`: nest when a job must inherit a base workspace's
      knowledge; one sentence linking `teams.md` for the team layout; one
      sentence that a base outside the chain uses `wiki_base`. Under
      `## How to run it` put the `mkdir` and `shipd workspace init ...
      --nested --git` block, the layout tree, and the text of `### --nested`
      as plain paragraphs. Under `## Reference` put, as level-3 sections,
      "What inherits across the chain", "What stays nearest-only", and
      "`wiki_base` alongside nesting", text unchanged. Name no `store_root`
      behaviour. Lint the file and confirm 150 lines or fewer.
- [x] 2.2 [req: workspaces-doc, merged-dependency-check, store-repo-folder-name]
      Create `docs/workspaces/external-stores.md`, titled
      `# External stores`, with `<!-- doc-type: reference -->` on line 1 and
      the back link. Source: `docs/workspaces/nesting-and-stores.md` section
      "Storing artifacts outside the member repos". Opening: that section's
      first paragraph. Add `## When to use it`: use a store when member repos
      are not yours to fill with plans, or when plans must sit in one place;
      one sentence that CI then sees no artifacts, linking
      `#known-limitations`. Under `## How to run it` put the "declare the key
      once" paragraph, the JSON block, the tree with its lead-in and the
      paragraph after it, then `### A dedicated artifacts repo` and
      `### Check what resolved`. Under `## Reference` put, as level-3
      sections in this order, "Where the store lands", "Per-repo folder
      naming", "Auto-commit", "Dependencies between epic members", and
      "Known limitations", text unchanged. Keep the anchors
      `#per-repo-folder-naming` and `#check-what-resolved` resolving. Lint
      the file and confirm 250 lines or fewer.
- [x] 2.3 [req: workspaces-doc] Run
      `git rm docs/workspaces/nesting-and-stores.md`. In
      `docs/workspaces/getting-started.md`, change both
      `nesting-and-stores.md#nesting-job-workspaces` links to `nesting.md`.

## 3. Merge the team pages

- [x] 3.1 [req: workspaces-doc, workspaces-doc-examples, workspaces-doc-store-sync, workspace-universe-discovery]
      Rewrite `docs/workspaces/teams.md` as the merged page. Sources: the
      current `teams.md` and `docs/workspaces/multi-workspace-repos.md`. Set
      line 1 to `<!-- doc-type: reference -->`; keep the title and the back
      link. Opening: today's intro without its clone command, then the
      "Members are machine-local", "The shared surfaces", and "The ignore
      block" paragraphs. Add `## When to use it`: several engineers on one
      workspace; several teams in one repository, which calls for the nested
      team layout; a group that needs isolation, which calls for its own
      repository. Under `## How to run it` put three level-3 sections:
      `### Join a shared workspace` (the `/s:workspace clone` command, one
      sentence linking `getting-started.md`); `### Build the team layout`
      (the multi page's "Setup" section, with its `shipd workspace team`
      commands and paragraph); `### Clone and use the team layout` (the
      multi page's "Cloning and day-to-day use" section, holding the plain
      `git clone` rule and the `shipd board` folder rule). Under
      `## Reference` put these level-3 sections in order: `### The team
      layout` (the multi page's tree and its "What lives where" table);
      `### What the layout costs` (one sentence that reads fall through and
      writes land nearest, linking `nesting.md`, then the multi page's two
      cost paragraphs); `### Enterprise guidance` (the opening scenario
      paragraph, then "Projects are systems, not teams", "Nobody
      materializes everything", and the isolation paragraph);
      `### Inherited worktree hooks need your consent` and
      `### Concurrency expectations`, text unchanged. State the wizard, the
      plain `git clone` rule, the `shipd board` rule, and the isolation
      boundary once each. Delete the link to `multi-workspace-repos.md`.
      Lint the file and confirm 250 lines or fewer.
- [x] 3.2 [req: workspaces-doc-examples] Run
      `git rm docs/workspaces/multi-workspace-repos.md`.

## 4. Reshape the remaining pages

- [x] 4.1 [req: workspaces-doc] Reshape
      `docs/workspaces/getting-started.md`. Add an opening sentence after
      the back link: the page takes a machine from nothing to a working job
      workspace. Add `## When to use it`: starting a job that spans several
      repos, or loading an existing workspace on a new machine. Add
      `## How to run it` and demote "Set up the machine once", "Create a job
      workspace", "Check it into git", "Load it on another machine", and
      "Day to day" to level 3 under it. Add `## Reference` and move "The
      mandated parent directory" under it as a level-3 section; leave one
      sentence in the machine setup section that links
      `#the-mandated-parent-directory`. In "Day to day", cut the `/s:ask`
      bullet to one line that links `nesting.md` for the store order, and
      the `/s:teach` bullet to one line. Rewrap prose to 100 columns where
      the page needs room. Keep every `workspaces_root` fact and the consent
      round. Lint the file and confirm 150 lines or fewer.
- [x] 4.2 [req: workspaces-doc] Reshape `docs/workspaces/member-map.md`.
      Keep the marker, title, back link, and opening. Add
      `## When to use it`: a member already has a checkout on this machine,
      or a checkout outside the workspace must find its workspace. Rename
      "Mapping members to existing checkouts" to `## How to run it`, keeping
      its text and its level-3 sections "The workspace-map verbs" and "The
      clone-source list". Add `## Reference` holding, as level-3 sections,
      "The machine-local file", "What a mapped member means", and "Resolving
      from outside the workspace"; demote "The pointer", "The origin-URL
      scan", and "What the rungs leave alone" to level 4 under the last.
      Rewrap prose to 100 columns where the page needs room; reword nothing
      else. Lint the file and confirm 250 lines or fewer.
- [x] 4.3 [req: workspaces-doc] Reshape `docs/workspaces/headless.md`. Keep
      the opening. Add `## When to use it`: a CI job, a bot, or a cloud
      agent must read a workspace with no members and no machine config. Add
      `## How to run it` with "The footprint" and "Run a read" as level-3
      sections. Add `## Reference` with "What a headless read guarantees" as
      a level-3 section. Lint the file and confirm 150 lines or fewer.
- [x] 4.4 [req: workspaces-doc] Reshape `docs/workspaces.md`. Keep the
      marker, the title, the opening, the layout tree, and the two
      paragraphs after it. Replace `## The guide` with three sections. `##
      When to use it`: one job touches several repos and its knowledge must
      travel with it. `## How to run it`: `shipd workspace init myapp --git`
      to create, `/s:workspace clone <url> <dir>` to load, `/s:workspace
      sync` to materialize members, and `shipd workspace` for the roster,
      one line each, with a link to `docs/workspaces/getting-started.md`.
      `## Reference`: a table with one row per part page
      (`getting-started.md`, `member-map.md`, `nesting.md`,
      `external-stores.md`, `teams.md`, `headless.md`), each row a relative
      link, one sentence, and one example command taken from today's entry
      (for `external-stores.md`, `shipd config`); then a table of the six
      `/s:workspace` arguments (`init`, `show`, `clone`, `sync`, `map`,
      `team`) and the four `shipd workspace` forms (bare, `init`, `sync`,
      `team`), each with what it does, from
      `plugins/s/skills/workspace/SKILL.md` and `plugins/s/bin/shipd --help`.
      Lint the file and confirm 100 lines or fewer.

## 5. Verify

- [x] 5.1 [req: *] Advance the plugin version in
      `plugins/s/.claude-plugin/plugin.json`. Run `git fetch origin main`.
      When `python3 plugins/s/skills/build/scripts/version_guard.py --help`
      lists `--advance`, leave the number to `/s:build`'s ship-time step;
      otherwise set `version` one patch above the one in
      `git show origin/main:plugins/s/.claude-plugin/plugin.json`.
- [x] 5.2 [req: *] Run the `Lint docs` step body from
      `.github/workflows/ci.yml` locally and confirm exit 0. Run
      `python3 -B -m unittest plugins/s/skills/build/tests/test_workspace_team.py 2>&1 | grep -E "^(OK|FAILED)"`
      and confirm `OK`. Confirm with `wc -l` that each of the seven pages
      sits within its cap. Confirm every relative link and every `](#...)`
      anchor in the seven pages resolves. Run
      `git grep -nE "nesting-and-stores|multi-workspace-repos" -- docs README.md AGENTS.md plugins`
      and confirm no match. Run `grep -c '^## ' ` on each of the seven pages
      and confirm 3. Confirm `grep -c '```mermaid'` reports 0 for each.
      Confirm `git status --short` lists only the nine files under `docs/`,
      the test file, `plugin.json`, and the change's own artifacts. Run
      `plugins/s/bin/shipd lint docs-workspaces-group` and confirm it
      reports the change clean.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 156 | 105.3k |
| Write | 7 | 22.4k |
| SubagentHandback | 4 | 10.2k |
| Read | 24 | 4.8k |
| Agent | 7 | 4.2k |
| (no tool) | 0 | 771 |
| **Total** | 198 | 147.7k |
