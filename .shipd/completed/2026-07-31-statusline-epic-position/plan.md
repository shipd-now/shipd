# statusline-epic-position
Status: verified

## Idea

Enrich the statusline's `(EPIC)` marker to
`(EPIC: <epic-slug>, spec <pos>/<total>)`, naming the epic and the picked
change's position among its members.

### Motivation

The bare `(EPIC)` marker says a change belongs to an epic but not which one
or how far through the roster it sits, so a multi-member delivery reads as a
sequence of unrelated changes. The epic slug and the member table are already
on disk next to the change; the marker just doesn't surface them.

### Details

- Replace the literal `(EPIC)` with `(EPIC: <slug>, spec <pos>/<total>)`,
  where `<pos>` is the picked change's 1-based row position in its epic's
  `| Change | ... |` members table and `<total>` the member row count.
- Resolve the epic file relative to the candidate's own content dir
  (`<base>/.shipd/epics/<slug>/epic.md`, where the candidate lives at
  `<base>/.shipd/planned/<change>/`), so worktree candidates read their own
  epic snapshot.
- Degrade gracefully: epic file missing or the change absent from the
  table → the plain `(EPIC)` marker as today.

Affected capabilities: `statusline` (modified: `statusline-rendering`).
Impact: `plugins/s/integrations/statusline.sh`,
`plugins/s/skills/build/tests/test_statusline.py`,
`plugins/s/.claude-plugin/plugin.json` (version bump).

### Non-goals

- No shipped/total progress semantics — position in the table only (no
  member-state derivation in bash).
- No truncation/abbreviation of the epic slug.
- No epic info for changes without an `Epic:` header, and no change to the
  dot, position bracket, or any other segment.

## Implementation

- **Position extraction** — a new `epic_position()` helper: given the epic
  file and the change name, filter table rows with
  `grep '^|' | grep -v '^|[[:space:]]*---'`, drop the header row (first
  cell literally `Change`), then number the remaining rows and match the
  row whose first cell equals the change name (sed to strip `| cell |`
  padding). Emits `pos total` (space-separated) or nothing on any miss.
  Pure sed/grep/while-read — bash 3.2, no runtimes (constitution).
- **Epic file path** — derive from the candidate dir with suffix stripping:
  `base="${d%%/planned/*}"` is wrong for nested names; use
  `base="${d%/planned/"$name"/}"` — the candidate dir always ends
  `/planned/<name>/` — giving `<base>/epics/<slug>/epic.md` (the content
  dir root). Rejected: always reading the workspace root's epic file — a
  worktree's epic snapshot can differ from the root's.
- **Render** — in the render section, when the picked candidate's epic is
  non-empty: call `epic_position`; on a hit render
  ` (EPIC: <slug>, spec <pos>/<total>)`, otherwise ` (EPIC)`. The marker
  still sits after the name and before any `(1 of X)` bracket, inside the
  name color segment. The epic lookup runs only for the picked candidate
  (once per render), not per candidate.
- **Storage** — `add_candidate` already stores `cand_epic[$i]`; also store
  `cand_dir` (exists) — the render section derives the epic path from
  `${cand_dir[$pick]}` and `${cand_epic[$pick]}`. No new parallel array.
- **Tests** — extend `test_statusline.py`: fixture epics get a members
  table; assert the enriched marker (`(EPIC: some-epic, spec 2/3)`) for a
  mid-table member, the plain `(EPIC)` fallback when the epic file is
  absent and when the change is missing from the table, and no marker for
  a standalone change (regression).
- **Version bump** — `plugins/s/.claude-plugin/plugin.json` to the next
  free patch above `origin/main` at ship time (0.6.7 as of planning; the
  in-flight mikk-knowledge autopilot may claim patches concurrently, so
  re-check at ship).

Risk: table drift (a future epic format change) silently downgrades the
marker to `(EPIC)` — acceptable, the fallback is the pre-change behavior.
