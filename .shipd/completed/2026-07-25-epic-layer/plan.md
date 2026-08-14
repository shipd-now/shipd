# epic-layer
Status: verified
Theme: spec-engine

## Idea

The plan-metadata foundation reserved an `Epic:` header key, but today it is a
dangling reference: nothing defines what an epic *is*, lint cannot resolve the
slug, and there is no way to decompose a feature into member changes and track
them as a group. The grouping layer of the Initiative → Epic → Change
hierarchy does not exist yet.

This change makes epics first-class:

- An **epic artifact** at `am/epics/<slug>/epic.md`: `# <slug>` title,
  `Status:` header (epic vocabulary: `draft`, `ready`, `active`, `complete`),
  an optional metadata block recognizing `Theme:` and `Initiative:`, required
  `## Decisions`, `## Design`, and `## Changes` sections, where `## Changes`
  holds the member stub table
  (`| Change | Description | Code | Integration | Unknowns | Risk |`).
- **Lint coverage**: epics validate during library lint and via a new
  `--epic <slug>` mode; a change's `Epic:` line must resolve to an existing
  epic (error), and a member change missing from its epic's stub table warns.
- **Status derivation**: `epic-show`, `epic-sync`, and `epic-set-status` verbs
  on the status CLI, deriving epic status from member-change states.
- An **`/s:epic` skill** that interviews the user, records Decisions and
  Design, and emits the stub table — member changes are planned later, one at
  a time, via `/s:plan`.
- `am/README.md` grammar docs and the plugin version bump (0.1.7 → 0.1.8).

### Non-goals

- No initiative briefs, workspace, or project machinery — the `Initiative:`
  key on an epic stays a location-agnostic slug (workspace-projects change).
- No stub directories and no pre-created `am/planned/` entries: stubs are
  table rows only; each member change is born in its own worktree via
  `/s:plan` (explicit user decision).
- No epic-level `verified` status and no epic archival/completion move —
  epics stay in `am/epics/` with a derived `complete` status.
- No `/s:build` or statusline epic awareness, and no theme/initiative
  reporting (theme-tooling change).

Affected capabilities: `shipd-spec-format`, `shipd-spec-lint`, `spec-status`
(modified via ADDED requirements); `shipd-epic` (new — the skill). Impact:
`plugins/s/skills/build/scripts/{spec_common,spec_lint,spec_status}.py` and
their tests, new `plugins/s/skills/epic/SKILL.md`, `am/README.md`,
`plugins/s/.claude-plugin/plugin.json`.

## Implementation

- **Epic header reuses the plan header machinery.** Same title/`Status:`/
  metadata-block grammar, parsed by the existing `parse_plan_metadata`; new
  constants `EPIC_STATUSES = ("draft", "ready", "active", "complete")` and
  `EPIC_METADATA_KEYS = ("Theme", "Initiative")` in `spec_common.py`.
  `Profile:` and `Epic:` are *not* recognized on an epic (a profile is
  change-level; epics do not nest) — an unrecognized key is a lint error,
  same as plans. `Theme:` validates against `valid_themes` exactly as on
  plans. Rejected: a separate epic metadata parser — one grammar, two key
  sets.
- **Stub table grammar.** `spec_common.py` gains `parse_epic_changes(text)`
  returning the `## Changes` table rows as (slug, description, ratings) —
  header row must match the six columns in order; every rating is one of
  `low` | `medium` | `high`; the Change cell is a kebab-case slug, unique
  within the table; at least one data row required. Rejected: free-form
  bullets — the complexity table is the point of the stub.
- **Lint wiring.** `spec_lint.py` gains `lint_epic(root, slug, errors,
  warnings)` covering header, status value, metadata keys/values, the three
  required sections, and the stub table. `lint_library` walks `am/epics/*/`
  (a repo with no `am/epics/` lints exactly as today); a new `--epic <slug>`
  CLI mode lints one epic. In `lint_change`, an `Epic:` value that does not
  resolve to `am/epics/<slug>/epic.md` is an **error**; a resolved epic whose
  stub table lacks the change's slug is a **warning** (the decomposition may
  legitimately grow, but drift should be visible).
- **Status derivation (per member stub slug).** A member is `archived` when
  any `am/completed/*-<slug>/` exists; else its `am/planned/<slug>/plan.md`
  status when that change exists; else `unplanned`. `epic-sync` derives: all
  members archived → `complete`; any member archived or carrying status
  `active`/`complete`/`verified` → `active`; otherwise → `ready`. Like plan
  `sync`, it never changes a `draft` epic (authoring in progress).
  `epic-show` prints the epic's status, metadata, and one line per member
  with its state. `epic-set-status` validates the value against
  `EPIC_STATUSES` and, when targeting `ready`, requires the epic to lint
  clean — mirroring plan guards; refusals print `Refused: ` and exit 3.
- **The `/s:epic` skill is markdown-only** (`plugins/s/skills/epic/
  SKILL.md`): codebase-first investigation, one batched AskUserQuestion round,
  record Decisions and Design, decompose into the stub table with per-change
  complexity ratings, emit the epic at `Status: draft`, lint via
  `spec_lint.py --epic`, promote to `ready` on approval via
  `epic-set-status`, and ship through the standard worktree + auto-merge PR
  flow (worktree name `epic-<slug>`). It never plans member changes — it
  points the user at `/s:plan <stub>` per member, which emits changes
  carrying `Epic: <slug>`.
- **Risks.** Member slugs can collide with unrelated archived changes
  (`am/completed/*-<slug>` matching a different change of the same name) —
  accepted for now: slugs are repo-unique by convention; noted in README.
  Derivation reads only the filesystem, so `epic-sync` stays correct as
  members merge in later PRs.
