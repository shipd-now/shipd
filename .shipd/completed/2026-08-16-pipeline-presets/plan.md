# pipeline-presets
Status: verified
Epic: named-pipelines

## Idea

Give the `autonomous-pipeline` config key a string form naming a built-in
preset (`default`, `eco`, `basic`), shipped as a data table beside the
pydantic schema, with `preset:<name>` provenance and on-demand expansion
through `pipeline-show`.

### Motivation

Cheapening a delivery today means hand-authoring a full entry list; the epic's
success criterion is that `{"autonomous-pipeline": "eco"}` is a one-line
opt-in, and `resolve_pipeline` currently rejects any non-list value outright
(`spec_common.py:504`).

### Details

- `resolve_pipeline` accepts a string value: `"default"` resolves to the
  built-in six-stage pipeline stdlib-only; `"eco"`/`"basic"` expand through
  the preset table and the existing pydantic validation (fail-closed without
  pydantic); unknown names error listing the known presets.
- Preset table as data in `pipeline_schema.py`; stdlib names tuple
  `PIPELINE_PRESETS` in `spec_common.py`. Provenance becomes
  `preset:<name> (<config-path>)`.
- `pipeline-show` renders declared per-stage options on entry lines and gains
  `--expand <preset>` printing a preset's entry list as JSON — the supported
  path to fork a preset into a custom list.

Affected capabilities: `shipd-config` (modified + added requirements),
`spec-status` (modified requirement). Impact:
`plugins/s/skills/build/scripts/spec_common.py`, `pipeline_schema.py`,
`spec_status.py`, `tests/test_spec_common.py`, `tests/test_spec_status.py`,
`tests_pydantic/`, `.shipd/README.md`, `README.md`,
`plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No preset+override merging: the key holds a preset name or a full entry
  list, never both; "eco but tweaked" means `pipeline-show --expand eco` and
  committing the edited list (epic non-goal).
- No consumer changes: autopilot, `/s:build`, `/s:plan`, and `/s:review` do
  not yet act on the option fields presets carry (epic members 4-6).
- No new stages, no schema changes: the entry grammar from `pipeline-schema`
  is consumed as-is; presets only populate it.
- No review skip in shipped presets: eco/basic cheapen review via
  `model`/`disposition`, never omit the stage.

## Implementation

- **Names mirror, table single-sourced.** `spec_common.py` exports
  `PIPELINE_PRESETS = ("default", "eco", "basic")` (stdlib, beside
  `PIPELINE_STAGES`); `pipeline_schema.py` exports the table
  `PRESETS: dict[str, list[dict]]` with exactly those keys plus
  `expand_preset(name)` returning `validate_entries(PRESETS[name])` — so
  preset-expanded entries are validated and `exclude_unset`-dumped exactly
  like user-authored ones (epic Design: the typed-options layer validates
  every entry). A `tests_pydantic` test asserts the keys match the tuple,
  following the existing `PIPELINE_FALLBACKS`/`Fallback` mirror precedent
  (`pipeline_schema.py:44`). Rejected: table in a stdlib module — expansion
  needs validation anyway, and "data beside the schema" is the epic's
  decision; rejected: names only in the table — unknown-name errors must
  list known presets without pydantic installed.
- **String branch in `resolve_pipeline`.** After the `raw is None` default:
  a `str` value is checked against `PIPELINE_PRESETS` first — unknown names
  raise `ConfigError` "unknown pipeline preset '<name>' (from <path>); known
  presets: basic, default, eco" with no import. `"default"` returns the same
  entries as the no-key default with provenance `preset:default (<path>)` —
  stdlib-only, per the epic non-goal. Any other known name goes through the
  existing lazy-import guard (same fail-closed `ConfigError`) and
  `expand_preset`; provenance `preset:<name> (<path>)`. The non-list error
  message becomes "must be a JSON list or a preset name string". Provenance
  stays a plain string, so `pipeline-show`, autopilot, and the heartbeat
  (`heartbeat.py:109`) consume it unchanged; `cmd_pipeline_show`'s
  `[default]` special case applies only to the literal `"default"`
  provenance, so preset provenance prints verbatim.
- **Preset table contents** (the epic's v1 table, encoded): `default` =
  `[{"stage": s} for s in PIPELINE_STAGES]` (bare — schema defaults apply,
  never injected). `eco` = research/epic `{"skip": true}`; plan
  `{"model": "session"}`; gate `{"autopilot": {"attempts": 1}}`; build
  `{"validator": false, "subagent_model": "tier-two-below",
  "telemetry": false}`; review `{"model": "tier-below",
  "disposition": "high-only"}`. `basic` = research/epic `{"skip": true}`;
  plan `{"model": "session"}`; gate `{"skip": true}`; build
  `{"validator": false, "subagent_model": "tier-below"}`; review
  `{"model": "tier-below", "disposition": "high-only"}`. Explicit skip
  entries (not omission) keep skipped stages visible in `pipeline-show`;
  explicit `"model": "session"` on plan encodes the never-cheapen-plan
  decision in the data.
- **`pipeline-show` options suffix.** `_format_pipeline_entry`
  (`spec_status.py:1599`) appends declared option fields after the existing
  form label: for each of `model`, `subagent_model`, `validator`,
  `telemetry`, `parallelism`, `disposition` present on the entry render
  `key=value` (booleans as `true`/`false`), and each `autopilot` sub-key as
  `autopilot.<key>=<value>`, joined with `", "` and separated from the label
  by two spaces. Entries without options render byte-identically to today
  (the observed default `pipeline-show` output is unchanged).
- **`--expand <preset>` on `pipeline-show`.** Optional flag on the existing
  subparser (`spec_status.py:2505`). With it, the verb resolves no config:
  it prints `json.dumps(entries, indent=2)` of the named preset — the exact
  JSON value to paste as the key — and exits 0. `default` expands via
  `PIPELINE_STAGES` with no import; other known names lazily import
  `pipeline_schema` (pydantic absent → the same install-hint error text,
  raised as `StatusError`); unknown names exit non-zero listing the known
  presets. Rejected: a separate verb — expansion is a view of the same
  surface, and the flag matches existing verb-flag precedent
  (`--json`, `spec_status.py:2420`).
- **Docs.** `.shipd/README.md` "The autonomous pipeline" section (lines
  183-224) documents the string form and the three presets; `README.md`
  (lines 176-183) gains one sentence naming the preset opt-in and
  `--expand`.
- **Test placement** follows the member-2 split: stdlib behavior (default
  preset, unknown-name error, fail-closed eco, `--expand default`) in
  `tests/`, run without pydantic; expansion/validation/rendering of eco and
  basic in `tests_pydantic/` (venv locally, CI after the requirements
  install). Runnable premises observed pre-plan: `spec_status.py
  pipeline-show` on this repo prints the six-stage `[default]` listing,
  exit 0 — must be byte-identical after this change; `python3 -c "import
  pydantic"` fails here (ModuleNotFoundError), so the stdlib guarantees are
  genuinely exercised on this machine.
- **Version bump** in `plugins/s/.claude-plugin/plugin.json` (change
  touches `plugins/s/`).

Risk: preset table drifting from the schema as members 4-6 evolve options —
guarded by the `tests_pydantic` table-validity test, which fails the moment
any preset entry stops validating.
