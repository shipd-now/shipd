# initiative-briefs
Status: verified
Epic: workspace-projects
Theme: spec-engine

## Idea

The workspace can now be discovered, but an initiative is still just a
validated slug: nothing defines the brief behind it, `Initiative:` lines on
epics and standalone changes resolve to nothing, and there is no way to see
an initiative's progress. The "why" layer of the hierarchy has no artifact.

This change makes initiative briefs real, per the epic's Decisions:

- A **brief artifact** at `<workspace-root>/initiatives/<slug>/brief.md`:
  `# <slug>` title, `Status:` (`open` | `achieved` | `dropped`), an optional
  metadata block recognizing only `Project:`, free prose stating the goal,
  and a required `## Requirements` section of `- [ ]` checkboxes — outcomes
  ticked over time, not tasks.
- **CI-safe `Initiative:` resolution** in lint: when a workspace root is
  discoverable from the repo, an `Initiative:` line on an epic or a
  standalone change must resolve to an existing brief (error otherwise);
  when no workspace exists (bare CI checkout), the check is silently
  skipped.
- A **`--initiative <slug>` lint mode** validating one brief's structure
  (requires a workspace; briefs are never part of repo/library lint).
- **Initiative status verbs** on the status CLI: `initiative-show`,
  `initiative-sync`, `initiative-set-status`, mirroring the epic verbs.
- `am/README.md` docs and the plugin version bump (0.2.2 → 0.2.3).

### Non-goals

- No `Project:` validation against the registry — the key is recognized on a
  brief but its semantics land with the `project-groups` member.
- No `/s:initiative` skill (new/list/review interviews) — that is the
  `initiative-skill` member; until then briefs are authored by hand.
- No brief walking in library lint and no CI dependence on workspace files.
- No epic↔initiative back-links or reporting.

Affected capabilities: `shipd-workspace` (modified via ADDED requirements),
`shipd-spec-lint` (modified via ADDED), `spec-status` (modified via ADDED).
Impact: `plugins/s/skills/build/scripts/{spec_common,spec_lint,spec_status}.py`
and their tests, `am/README.md`, `plugins/s/.claude-plugin/plugin.json`.

## Implementation

- **Brief grammar reuses the header machinery.** `parse_plan_metadata` reads
  the brief's header; new constants in `spec_common.py`:
  `INITIATIVE_STATUSES = ("open", "achieved", "dropped")` and
  `BRIEF_METADATA_KEYS = ("Project",)`, plus
  `initiative_brief_path(ws_root, slug)` returning
  `<ws_root>/initiatives/<slug>/brief.md`. Status vocabulary rationale: an
  initiative is a goal — it is `open` while pursued, `achieved` when its
  requirement checkboxes are all ticked, `dropped` when abandoned (manual
  only). Rejected: reusing the five change statuses — goals have no
  draft/ready pipeline.
- **`Project:` is recognized but not validated.** Same seam as
  workspace-discovery's tolerant registry: the key parses and lints as a
  kebab slug now; registry-existence validation is `project-groups`' job.
  Rejected: rejecting the key until then — briefs authored with a scope
  would break on upgrade.
- **Resolution wiring.** `spec_lint.py` gains
  `check_initiative_reference(root, metadata, errors)` used by both
  `lint_change` (standalone changes carrying `Initiative:`) and `lint_epic`:
  it calls `find_workspace_root(root)`; on `None` it returns without any
  finding (CI-safe silent skip); with a workspace, a missing brief file is
  an **error** naming the expected path. The Epic:/Initiative: exclusivity
  rule is untouched.
- **`--initiative <slug>` mode** in `spec_lint.py` (mutually exclusive with
  `--epic`/change args, like `--epic`): errors immediately when no workspace
  is discoverable from `--root`; otherwise validates the brief — title
  matches slug, status in `INITIATIVE_STATUSES`, metadata keys within
  `BRIEF_METADATA_KEYS` with kebab values, `## Requirements` present with at
  least one checkbox.
- **Status verbs in `spec_status.py`**, mirroring the epic verbs and
  resolving the workspace the same way (error `no workspace found` when
  absent): `initiative-show <slug>` prints status, metadata, and
  `done/total` requirement counts plus each requirement line;
  `initiative-sync <slug>` derives `achieved` when all requirements are
  ticked (at least one exists) and `open` otherwise, never touching
  `dropped`; `initiative-set-status <status> <slug>` validates the value
  (writes via the same header-rewrite helper used for plans/epics).
  Checkbox counting reuses the tasks.md checkbox conventions (`- [ ]` /
  `- [x]`; `[~]` counts as unticked).
- **Risk:** a repo inside an unrelated stray workspace would suddenly
  enforce `Initiative:` resolution. Accepted — the stray-marker caveat is
  already documented in the README's Workspace section; error messages name
  both the workspace root and the expected brief path so the cause is
  visible.
