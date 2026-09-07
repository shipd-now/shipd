# completed-retention
Status: verified
Theme: developer-experience

## Idea

Age completed work off the delivery board: a layered `completed_retention_days`
config key (default 30) under which the board hides complete epics and archived
standalone changes older than the window, with an honest one-line hidden count.

### Motivation

The board renders every complete epic and archived change forever — this repo
already shows 10 epics, most `[complete]` since July, over 273 archives — so
the signal (live work) drowns in shipped history. Nothing ages completed work
out today, and the user approved a retention window to fix that.

### Details

- New layered config key `completed_retention_days` in `.shipd-config.json`:
  default `30`, `0` or `null` meaning never hide, malformed values treated as
  undeclared (the `guardrails` precedent). Carried as a built-in default so
  `config-show` reports it with `default` provenance automatically.
- `dashboard.py`'s `build_board` hides, by default: epics with status
  `complete` whose completion date is older than the window, and standalone
  rows in state `archived` whose archive date is older. Both the `board` verb
  (text and `--json`) and the `tui` verb inherit the filter through that one
  seam.
- Honest hiding: the board object carries `hidden_completed` and
  `retention_days`; the text board ends with a one-line
  `N older completed hidden (completed_retention_days=D)` note; the TUI's
  shipped lane header carries the count. A `--all` flag on both verbs bypasses
  retention per invocation.

Affected capabilities: `shipd-config` (modified), `delivery-dashboard`
(modified). Impact: `plugins/s/skills/build/scripts/spec_common.py`,
`plugins/s/skills/build/scripts/dashboard.py`, tests under
`plugins/s/skills/build/tests/` and `tests_textual/`, plugin version bump in
`plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No change to `spec-status` report/list surfaces, the metrics view, the
  throughput chart, or `metrics.py` aggregates — they derive from ship events
  and transcripts, not the board's epic list, and stay unfiltered.
- No per-member hiding inside a retained epic: a live epic's member table stays
  whole; only whole complete epics and standalone archived rows hide.
- No deletion or archival relocation — hiding is display-only; every artifact
  stays on disk and reachable via `shipd list --archived`.
- No shipd-app dashboard work and no `shipd list epics` JSON change (see the
  downstream note in Implementation).

## Implementation

- **Epic completion-date source (decided): newest member archive-dir stamp.**
  Archive directories are named `YYYY-MM-DD-<slug>` (written from local
  `date.today()` by `spec_merge.py`). For each stub member, glob
  `<specs_dir(member location)>/completed/*-<slug>`, take the newest dirname,
  parse the leading date; the epic's completion date is the max across
  members. Rejected: the epic file's last git commit date — the board path is
  deliberately git-free (no subprocess calls), and epic-amend/close-out
  commits would falsify the date. A complete epic yielding no parseable date
  is never hidden (fail open, honest over tidy).
- **Config surface** (`spec_common.py`): `COMPLETED_RETENTION_KEY` /
  `DEFAULT_COMPLETED_RETENTION_DAYS = 30`; seed the key into `resolve_config`'s
  defaults dict beside `dir`, so `config-show` prints it with provenance
  unchanged. Accessor `completed_retention_days(config)` returns the window in
  days or `None` when disabled: positive int → itself; `0`/`null` → `None`;
  anything else (bool, negative, non-int) → the default, treated as undeclared
  rather than an error — mirroring the `guardrails` key.
- **Filter seam**: inside `build_board(root, epic=None, retention_days=<resolve>,
  today=None)` — a sentinel default resolves the window from the invocation
  root's layered config once (a viewer display preference, not per-universe
  data); `None` disables; `today` is injectable for tests. Epics are filtered
  before `_group_epics` runs, so `epics`, `groups`, and every lane derive from
  the survivors; standalone rows filter alongside. Hidden when
  `date < today - timedelta(days=N)` (strictly older, local dates). An
  `--epic`-scoped board skips retention entirely — an explicit request names
  the epic. Board gains `hidden_completed` (int) and `retention_days`
  (int or null).
- **Render surfaces**: `render_board_lines` appends the note line when
  `hidden_completed > 0` (covers `board` text mode and the TUI's text
  renderer); the TUI updates the shipped `Lane`'s docked `.lane-header` Static
  in `BoardApp._render_lanes` to append the count. `--all` on both verbs and a
  `show_all` param on `BoardApp` pass a disabled window through the
  `board_fn` seam.
- **Risk**: worktree candidates with unreadable configs during date probing —
  guard every `sc.specs_dir` call with the same `ConfigError` skip the state
  probe uses; a probe failure contributes no date and the item stays visible.
- **Downstream consumer note (recorded, not implemented):** the shipd-app
  dashboard will want the same retention semantics. The cheapest correct route
  is exposing a completion date on `shipd list epics --json` rows (an additive
  `completed: "YYYY-MM-DD" | null` field derived exactly as above), which under
  `schema-versioning` is an additive schema-minor bump of `SCHEMA_VERSION`
  `1.0.0 → 1.1.0`. That is a separate engine change the app-side work should
  pair with; this change deliberately keeps to the engine board/TUI.
