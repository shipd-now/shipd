# board-project-cards
Status: verified

## Idea

Show each board card's owning project, let the filter strip narrow the board
to one project, and scope a board run from a project folder to that project's
repos.

### Motivation

A workspace member running `shipd board` from a project folder such as
`workspaces/shipd` sees every project in the registry and cards that name no
project, so they cannot tell which repo a ticket belongs to or narrow the
board to the project they stand in.

### Details

- Add a muted `[<project>]` marker to every task card whose member comes from
  a declared project universe, in all three grouping modes, and a
  `project: <slug>` badge to the member detail modal.
- Carry a standalone row's own project onto its card and into the lane
  signature, so project standalone rows are marked and repaint on change.
- Add a `project` filter kind to the filter picker and the chip matcher.
- Teach `workspace_project_roots` a third case: an invocation root inside the
  registry root that is neither the registry root nor inside a declared repo
  yields only the declared repos beneath it.
- Update the two workspace doc sentences that describe the board's scope.

Affected capabilities: `delivery-dashboard` (one requirement added, one
modified), `shipd-workspace` (one requirement modified). Impact:
`plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/scripts/spec_common.py`, their test files,
`docs/workspaces/teams.md`, `docs/workspaces/multi-workspace-repos.md`, and
the plugin version in `plugins/s/.claude-plugin/plugin.json`. No new
dependencies.

### Non-goals

- No two-row card or right-aligned corner label. The lane-row-presentation
  requirement pins one terminal row per card.
- No `--project` flag on the `board` or `tui` verbs; the folder you stand in
  and the filter chip are the two scoping tools.
- No change to retention, the text board's epic rows, or the epic detail
  modal, which already carry the project marker.
- No change to `project_of` or to `show`, `epic-show`, and `locate` beyond
  what they inherit from the shared seam.

## Implementation

- **Trailing muted marker on the one-row card.** `TaskCard._card_text`
  computes its existing text, then appends ` [$fg-muted]\[<project>][/]` when
  the card's project is non-null. One append point serves the risk, shipped,
  signalling, driving, and live-build branches. The escape and tier copy
  `epic_group_title`, so the marker paints identically on header and card.
  Rejected: a `Horizontal` with a right-aligned label, which turns a `Static`
  card into a container and breaks the chrome sweep's single-line assertion.
- **The card's project is `epic_project or member.get("project")`.** Epic
  members take the epic's project from the card spec; standalone rows carry
  their own on the row, which `build_board` already sets. The spec's fifth
  element stays the epic identity, so `_find_epic` and group folding are
  untouched and standalone rows still fold into one `standalone` group.
- **Lane signature folds `member.get("project")`.** The epic's project is
  already in the tuple; the row's own project joins it so a standalone card
  whose universe changes repaints.
- **Modal badge, not a title change.** `MemberDetailScreen` takes a `project`
  keyword defaulting to `None` and yields a muted `project: <slug>` badge after
  the epic badge when set. `TaskCard.action_select` passes the card's project.
  Every existing constructor call stays valid.
- **`project` is a fourth filter kind.** `_filter_matches` takes a `project`
  argument the caller resolves the same way the card does, and a null project
  never matches a chip. `_filter_options` appends each distinct project slug
  after the initiative slugs, walking epics in board order and then standalone
  rows. Picker labels read `project: <slug>` through the existing formatter.
- **Descendant filter in the seam, not a new seam.** After the registry root
  and `project_of` checks pass, `workspace_project_roots` compares real paths:
  when the invocation root is inside the registry root and is not the registry
  root itself, only repos whose real path lies beneath the invocation root are
  returned. The registry root and any root outside it keep every declared
  repo. Rejected: consulting the `focus` key, which names a job's primary
  project rather than the folder the user stands in.
- **Version bump** to `0.6.243` in `plugins/s/.claude-plugin/plugin.json`.

Risk: the filter-strip requirement is replaced wholesale, so every base
scenario must be restated; the delta restates all fourteen and adds three.

## Readiness attestation

### Problem and motivation

Running the board from a project folder shows every project in the registry,
and cards carry no project, so a member cannot tell which repo a ticket
belongs to or scope the board to the project they stand in.

Evidence:

- `plugins/s/skills/build/scripts/dashboard.py:2817-2861` renders glyph,
  slug, and stage only; `dashboard.py:927-935` passes a null project for
  every standalone row.
- `plugins/s/skills/build/scripts/spec_common.py:2565-2567` returns every
  declared repo for any root outside a declared repo.
- Capability `delivery-dashboard`, requirement `board-aggregation`, marks
  headers only; requirement `board-filter-strip` names three chip kinds.

### Scope and non-goals

The change covers card and modal markers, a project filter kind, the seam's
project-folder case, two doc sentences, tests, and the version bump; two-row
cards, a `--project` flag, retention, and the epic modal stay out.

Evidence:

- In scope: `dashboard.py:1495-1542` (filter helpers),
  `dashboard.py:1426-1475` (lane signature), `dashboard.py:2084-2147` (modal
  badge row), `spec_common.py:2537-2602`.
- Out of scope: requirement `lane-row-presentation` fixes one row per card;
  requirement `board-completed-retention` already carries the hidden count.

### Affected capabilities and files

Two capabilities and seven files are affected, because the card, modal,
filter, and signature live in `dashboard.py`, the seam in `spec_common.py`,
and the scope rule in two docs.

Evidence:

- Capability `delivery-dashboard`: `board-filter-strip` (base 95bbdec877e9)
  modified; `board-card-project-marker` added.
- Capability `shipd-workspace`: `workspace-universe-discovery` (base
  39577ac6a61a) modified.
- Files: `plugins/s/skills/build/scripts/dashboard.py`,
  `plugins/s/skills/build/scripts/spec_common.py`,
  `plugins/s/skills/build/tests_textual/test_dashboard.py`,
  `plugins/s/skills/build/tests/test_spec_common.py`,
  `docs/workspaces/teams.md:150`, `docs/workspaces/multi-workspace-repos.md:80`,
  `plugins/s/.claude-plugin/plugin.json`.
- Runnable premise: `shipd board text --json` from `workspaces/shipd` → exit
  0, 12 epics from projects cai, fresh-careers, and shipd, 5 standalone rows,
  22 hidden; from `workspaces/shipd/shipd-now-website` → 0 epics, 3 hidden.
- Runnable premise: `sc.aggregation_universes("workspaces/shipd")` → the
  folder itself plus seven declared repos across three projects.
- Runnable premise: headless `BoardApp.run_test` from `workspaces/shipd` →
  group titles carry `\[cai]`, `\[fresh-careers]`, `\[shipd]`; card text
  carries none.
- Runnable premise: `wc -l docs/workspaces/teams.md` → 150, the how-to cap.

### No open task-shaping decision

Every task-shaping decision is settled by investigation or the user's
acceptance of the prior write-up; none remain.

Evidence:

- Marker placement (trailing muted tag on one row): settled by the user's
  acceptance of the write-up proposing it and by `lane-row-presentation`.
- Marker form (escaped muted brackets): settled by investigation of
  `epic_group_title`.
- Scope rule (descendants of the invocation root): settled by investigation
  of `project_of`'s containment rule and the `focus` requirement.
- Filter kind name (`project`): settled by the existing `kind: value` picker
  label convention.
