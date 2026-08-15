# worktree-epic-discovery
Status: verified

## Idea

Epic discovery in the delivery board and the status CLI becomes
worktree-aware: an epic authored in a `.worktrees/<name>` worktree appears
everywhere the root's epics do, marked with its hosting worktree.

### Motivation

The one-change-one-worktree workflow births every epic inside its own
worktree, but `shipd board`, `shipd epic <slug>`, and the bare `shipd status`
report only discover epics under the invocation root's content directory —
so a freshly authored epic is invisible from the main checkout until its PR
merges, breaking the board's full-picture promise.

### Details

- Add a shared root-first epic discovery seam to `spec_status.py`:
  `_epic_hosting_root(root, slug)` and `all_epic_slugs_with_roots(root)`,
  probing the invocation root first, then each `.worktrees/<name>` in sorted
  order, resolving each candidate's content directory independently and
  skipping unreadable configurations — mirroring `_member_state_with_root`.
- Board aggregation (`dashboard.py`) consumes it: worktree-authored epics
  join the board with a `location` field, their epic file, status,
  heartbeat, and report read from the hosting root; the text board and the
  TUI mark them `[worktree]`; the epic-detail modal reads the epic markdown
  from the hosting root.
- Status CLI read surfaces consume it: the `status`/`show` epic fallback,
  `epic-show` (which gains a `worktree: <name>` line after the metadata
  lines), and the bare-`show` workspace board report totals and rows.
- Mutating epic verbs are untouched and stay invocation-root-only.

Affected capabilities: `delivery-dashboard` (modified), `spec-status`
(modified). Impact: `plugins/s/skills/build/scripts/spec_status.py`,
`plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests/test_spec_status.py`,
`plugins/s/skills/build/tests_textual/test_dashboard.py`, plugin version
bump. No new dependencies.

### Non-goals

- No change to mutating verbs (`epic-set-status`, `epic-sync`,
  `epic-set-initiative`): a worktree-hosted epic is mutated inside its
  worktree, per the guarded-write workflow.
- No newest-wins or mtime-based dedupe: the invocation root always shadows
  a worktree copy of the same slug.
- No `shipd list` changes (already worktree-aware), no metrics changes, and
  no marker on the board HTML page (worktree epics appear there via the
  shared board data; the marker is text/TUI only).
- One probe level only — `.worktrees/*` of the invocation root — matching
  every existing probe.

## Implementation

- **The discovery seam lives in `spec_status.py`**, beside
  `_member_state_with_root` (`spec_status.py:741`), and `dashboard.py`
  consumes it through its existing `ss` import. Rejected: duplicating the
  worktree walk in `dashboard.py` — two walkers drift.
- **Root-first slug dedupe.** Worktrees are full-tree branches, so every
  root epic also exists in each worktree; `all_epic_slugs_with_roots`
  returns the root's epics (sorted) first, then worktree-only epics
  (sorted), the invocation root winning any slug clash. Rejected:
  newest-mtime-wins — nondeterministic and contradicts the spec'd
  "invocation root wins" member precedent.
- **Interfaces.** `_epic_hosting_root(root, slug) -> str | None` returns
  the first candidate root whose content dir holds `epics/<slug>/epic.md`;
  `all_epic_slugs_with_roots(root) -> list[(slug, hosting_root)]` in the
  order above. Candidates resolve `sc.specs_dir` independently; a
  `sc.ConfigError` skips that candidate.
- **Board data shape.** Each aggregated epic dict gains
  `location` (absolute hosting root), mirroring the member rows'
  `location`. `_epic_board` reads the epic file, `read_epic_status`, the
  heartbeat, and the run report from the hosting root — a worktree-run
  autopilot writes its heartbeat inside the worktree's content dir. The
  text renderer and the TUI epic group header append `[worktree]` when
  `location` differs from the board root; the epic-detail modal calls
  `epic_markdown(epic["location"], slug)`.
- **`epic-show` output stays parse-compatible.** The `<slug>: <status>`
  first line is unchanged (the autopilot parses it); the new
  `worktree: <name>` line prints after the metadata lines, only for a
  worktree-hosted epic.
- **Runnable premises (verified before planning):**
  `plugins/s/bin/shipd epic shipd-dx` from the root exits 1 with
  `Error: epic 'shipd-dx' not found (...)`; bare `plugins/s/bin/shipd
  status` prints `60 specs · 10 epics · 1 initiatives` while
  `.worktrees/epic-shipd-dx` hosts an 11th epic; `plugins/s/bin/shipd list
  --all` already lists worktree-hosted changes.
- **Risk:** a large worktree count makes discovery O(worktrees × listdir);
  bounded — the walk matches what member derivation already does per
  member, and runs once per board build. Guard: none needed beyond the
  existing sorted single-level walk.
