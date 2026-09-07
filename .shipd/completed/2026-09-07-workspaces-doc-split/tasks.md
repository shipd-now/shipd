## 1. Create the part pages

- [x] 1.1 [req: workspaces-doc] Create `docs/workspaces/getting-started.md`:
      `# Getting started` title, a `[← Workspaces](../workspaces.md)`
      breadcrumb line, then move current `docs/workspaces.md` §1–§5 (lines
      29–184: "One-time machine setup" through "Day to day") verbatim,
      dropping each heading's `<n>. ` numbering prefix (e.g.
      `## 1. One-time machine setup` → `## One-time machine setup`). Update
      in-file anchors to the new heading slugs (the §2→§1 link at current
      line 82 stays in-file); rewrite the §1→§6 links (current lines 49, 59)
      to `nesting-and-stores.md#nesting-job-workspaces` and the §1→§9 link
      (line 70) to `headless.md`, and the §3→§8 link (line 146) to
      `teams.md`.
- [x] 1.2 [req: workspaces-doc] Create `docs/workspaces/nesting-and-stores.md`:
      `# Nesting and external stores` title, the breadcrumb line, then move
      §6–§7 (current lines 185–335) verbatim, dropping heading numbering.
      Rewrite the §6→§2 link (current line 192) to
      `getting-started.md#create-a-job-workspace`; the `wiki_base (§1)`
      textual reference near current line 215 becomes
      `[`wiki_base`](getting-started.md#one-time-machine-setup)`-style
      wording preserving the sentence.
- [x] 1.3 [req: workspaces-doc] Create `docs/workspaces/teams.md`:
      `# Sharing a workspace with a team` title, the breadcrumb line, then
      move §8 (current lines 336–460) verbatim, dropping heading numbering.
      Rewrite the §8→§4 link (current line 340) to
      `getting-started.md#load-it-on-another-machine` and the §8→§3 link
      (current line 455) to `getting-started.md#check-it-into-git`.
- [x] 1.4 [req: workspaces-doc] Create `docs/workspaces/headless.md`:
      `# Headless consumers` title, the breadcrumb line, then move §9
      (current lines 461–517) verbatim, dropping heading numbering. This is
      the only page allowed to show `spec_status.py` invocations.
- [x] 1.5 [req: workspaces-doc-examples] Create
      `docs/workspaces/multi-workspace-repos.md`:
      `# Practical examples: multi-workspace repos` title, the breadcrumb
      line, then move §10 (current lines 518–666, including the Shape A/B
      subsections, tables, and pros/cons) verbatim, dropping the `10. `
      heading prefix. Rewrite the §10→§2 links (current lines 532, 568) to
      `getting-started.md#create-a-job-workspace`, the §10→§4 link (line
      630) to `getting-started.md#load-it-on-another-machine`, the §10→§6
      links (lines 580, 610) to
      `nesting-and-stores.md#nesting-job-workspaces`, and the §10→§8 link
      (line 645) to `teams.md`.

## 2. Rewrite the index

- [x] 2.1 [req: workspaces-doc] Rewrite `docs/workspaces.md` as the index:
      keep the `# Workspaces` title, the concept intro, and the labeled
      layout diagram (current lines 1–28) verbatim; delete the moved
      sections; then add a `## The guide` section with one entry per part in
      order (getting-started, nesting-and-stores, teams, headless,
      multi-workspace-repos), each entry being exactly: one descriptive
      sentence, one short fenced usage example (`shipd workspace init
      documents-linking --git`; `shipd workspace init
      ~/workspaces/acme-base/documents-linking --nested --git`; `git pull` at
      session start / `git push` at session end; `python3
      <plugin>/skills/build/scripts/spec_status.py --root /tmp/ws
      workspace-show`; `git clone git@github.com:acme/company-workspaces.git
      ~/workspaces/company` then `shipd workspace sync` inside a member), and
      a `[Details →](workspaces/<part>.md)` link.

## 3. Verify

- [x] 3.1 [req: workspaces-doc, workspaces-doc-examples] From the worktree
      root run `python3 plugins/s/skills/build/scripts/spec_lint.py
      workspaces-doc-split` and confirm exit 0. Then check links: for each of
      the six guide files, every `](#...)` anchor must match a heading slug
      in that same file, and every relative `](...)` link must name an
      existing file (check with grep plus `ls`). Confirm
      `grep -ri "portable workspace" docs/workspaces.md docs/workspaces/`
      finds nothing, `grep -rn "~/jobs" docs/workspaces.md docs/workspaces/`
      finds nothing, and `grep -rn "spec_status.py" docs/workspaces.md
      docs/workspaces/` hits only `docs/workspaces/headless.md` and the
      index's headless example entry. Confirm `git status --porcelain` shows
      only `docs/workspaces.md`, `docs/workspaces/`, and `.shipd/` paths.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 45 | 11.5k |
| Write | 7 | 7.3k |
| (no tool) | 0 | 1.2k |
| Read | 13 | 322 |
| Agent | 2 | 9 |
| **Total** | 67 | 20.3k |
