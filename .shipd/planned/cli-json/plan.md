# cli-json
Status: complete
Epic: shipd-dx

## Idea

Add `--json` machine output to the read/inspect verbs — `status`, `show`,
`locate`, `epic-show`, `workspace-show` in the status CLI, the in-binary
`shipd list`, and `spec_lint.py` — for scripting and future surfaces.

### Motivation

Every read verb is human-text-only today, so scripts and future surfaces
must screen-scrape aligned columns; the `shipd-dx` epic's conventions
decision reserves `--json` for exactly these read verbs.

### Details

- `spec_status.py`: a `--json` flag on `show`, `status`, `locate`,
  `epic-show`, and `workspace-show` emitting one JSON document on stdout.
- `plugins/s/bin/shipd`: `list --json` emits the rows as a JSON array.
- `spec_lint.py`: `--json` emits `{"ok", "errors", "warnings"}`.
- Rendering-only: exit codes, error stderr, and the flagless text output
  stay byte-identical.

Affected capabilities: `spec-status`, `shipd-cli`, `shipd-spec-lint` (all
modified via added requirements). Impact: `spec_status.py`, `spec_lint.py`,
`plugins/s/bin/shipd`, tests (`test_spec_status.py`, `test_spec_lint.py`,
`test_shipd_cli.py`), plugin version bump. No new dependencies.

### Non-goals

- No `--json` on mutating or guarded verbs (`set-status`, `sync`, `emit`,
  `merge`, epic mutators) — the epic reserves machine output for reads.
- No change to `dashboard.py board --json` or `metrics.py` (already
  machine-readable).
- No text-output changes of any kind without the flag.
- No JSON schema files or versioned envelope — keys mirror the text reports.

## Implementation

- **ADDED requirements only, no MODIFIED blocks** — the sibling
  `shipd-doctor` change modifies `shipd-cli`'s `cli-dispatch`; expressing
  this change as additive requirements in each capability avoids any
  `base:` collision whichever member merges first. Rejected: folding
  `--json` wording into the five existing requirements — five stale-base
  risks for zero expressive gain.
- **Shapes mirror the text reports** (keys stable, derived from the same
  data the text renderers consume):
  - `status --json`: `{"name", "kind": "change"|"epic", "status"}` (the
    epic fallback sets `kind": "epic"`).
  - `show --json` on a change: `{"name", "kind": "change", "status",
    "tasks": {"done", "in_progress", "total"} | null, "metadata": {…}}`.
  - `show --json` epic fallback and `epic-show --json`: `{"name",
    "kind": "epic", "status", "metadata": {…}, "worktree": <name>|null,
    "shipped": {"done", "total"}, "lanes": {"unplanned": [...], "ready":
    [...], "building": [...], "shipped": [...]}}`, each member
    `{"slug", "state", "risk", "worktree": bool}`.
  - bare `show --json` (workspace report): `{"kind": "workspace",
    "totals": {"specs", "epics", "initiatives"}, "shipped": {"done",
    "total"}, "lanes": {…}}` with member rows carrying their epic slug or
    `standalone`.
  - `locate --json`: an array of `{"change", "root", "dir", "status"}`.
  - `workspace-show --json`: one object mirroring the text report's fields
    (workspace root, projects with their repo lists, initiatives).
  - `shipd list --json`: an array of `{"name", "location", "status"}`
    (`--all` adds the archived rows exactly as the text mode does).
  - `spec_lint.py --json`: `{"ok": bool, "errors": [str], "warnings":
    [str]}` with the same strings the text mode prints; exit code
    unchanged.
- **Renderer split, not logic split:** each verb computes its existing data
  first, then renders text or JSON from the same values — so the two modes
  cannot drift. Error paths are untouched: an error still prints
  `Error: …` to stderr and exits nonzero regardless of the flag.
- Risk: `show`'s three forms (change / epic fallback / workspace) tripling
  the surface; guard: one test per form pinning the `kind` discriminator.
- **Metadata keys are repeatable** (`Fixes:` per `shipd-spec-format`), so the
  renderer-split data layer carries metadata as the **ordered (key, value)
  pair list** the parsers already yield — never collapsed through `dict()`.
  The text renderer prints one line per pair (byte-identical to pre-flag
  output); the JSON `metadata` object groups pairs by key — a key appearing
  once maps to its string, a repeated key maps to an array of its values in
  file order.
