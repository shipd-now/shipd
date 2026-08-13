# initiative-skill
Status: verified
Epic: workspace-projects
Profile: lite
Theme: spec-engine

## Idea

Every initiative primitive now exists — briefs, the `--initiative` lint mode,
the show/sync/set-status verbs, project scoping — but there is no guided way
to use them: creating a brief means hand-authoring markdown, reviewing means
manual checkbox edits, and attaching an initiative to an epic means editing a
header line by hand. The epic's last member wraps the CLIs in an
`/s:initiative` skill.

This change adds the skill (markdown-only, no engine code):

- `plugins/s/skills/initiative/SKILL.md` handling four verbs by argument:
  **new** (workspace-first interview → emit a lint-clean brief at
  `Status: open`), **list** (statuses, requirement progress, project scopes),
  **review** (walk requirements with the user, tick achieved outcomes, then
  `initiative-sync`), and **set** (tag an epic with exactly one initiative).
- An updated `AGENTS.md` lifecycle line naming `/s:epic` and
  `/s:initiative` beside the existing skills.
- The plugin version bump (0.2.6 → 0.2.7).

### Non-goals

- No engine or CLI changes — the skill drives what already exists.
- No brief projection/sync to any central service.
- No `set` on standalone changes — plans carry `Initiative:` via `/s:plan`;
  the skill's `set` verb targets epics only.

Affected capabilities: `shipd-initiative` (new). Impact:
`plugins/s/skills/initiative/SKILL.md` (new), `AGENTS.md`,
`plugins/s/.claude-plugin/plugin.json`.

## Implementation

- **One skill, four verbs by argument** (`/s:initiative new mvp-readiness`),
  mirroring how `am:plan`/`am:epic` take arguments — not four separate
  skills; the plugin namespace stays flat and discovery stays simple.
- **Briefs are written directly at the workspace root — no worktree, no PR.**
  Briefs live outside the repo (`<ws>/initiatives/<slug>/brief.md`), so the
  repo's PR workflow does not apply to `new`/`review`; the skill resolves the
  workspace like the CLIs do and refuses with the CLI's "no workspace found"
  behavior when none exists. Rejected: requiring the workspace to be a git
  repo — nothing else in the workspace layer assumes that.
- **`set` edits the repo, so it ships via PR.** Tagging an epic writes the
  `Initiative:` line into `am/epics/<slug>/epic.md` — an in-repo edit — so
  the skill runs it through a small worktree + auto-merge PR per the
  constitution (never commit to main). Before writing it verifies the epic
  exists, the initiative resolves (`spec_lint.py --epic` after the edit
  catches both via the CI-safe rule), and replaces any existing
  `Initiative:` line (exactly one initiative per epic).
- **Refusal rule.** Asked to tag a *change* that carries `Epic:`, the skill
  refuses and points at the epic (initiative derives through the epic) —
  mirroring the lint exclusivity rule interactively.
- **Interview discipline** matches the sibling skills: workspace-first
  investigation (`workspace-show`, existing briefs, declared project slugs
  offered when asking about scope), one batched question round for the goal,
  the outcome requirements, and the optional `Project:` scope; emit at
  `Status: open`; lint via `--initiative`; requirements phrased as outcomes,
  not tasks.
- **Docs-only change, so no engine tests** (the constitution's test rule
  binds engine changes); verification is the suite staying green plus change
  lint. Risk: skill instructions drifting from CLI behavior — mitigated by
  naming the exact commands (`spec_status.py initiative-*`,
  `spec_lint.py --initiative/--epic`) rather than paraphrasing them.
