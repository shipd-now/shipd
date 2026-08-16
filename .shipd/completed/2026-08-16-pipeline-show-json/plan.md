# pipeline-show-json
Status: verified
Epic: pipeline-hardening

## Idea

Give `pipeline-show` a `--json` machine contract, move the three skill
surfaces that parse its human-rendered labels onto it, and give preset
discovery a `/s:status pipeline` route.

### Motivation

The interactive `/s:build` and `/s:plan` flows and the in-session autopilot
read pipeline entries and per-stage options by parsing human-rendered label
lines, because no machine-readable view exists — a fragile contract the
pipeline-hardening epic explicitly closes. The label renderers stay for
humans; machine consumers move to JSON.

### Details

- `spec_status.py pipeline-show` gains `--json`: one JSON object with the
  resolved provenance and the validated entry dicts; `--expand <preset>
  --json` is accepted and emits the entry-list array expand already prints.
- `/s:build` step 1, `/s:plan`'s pipeline resolution, and the in-session
  autopilot's stage-option reading consume `--json`; rendered labels drop
  their contract status and stay human-only.
- `/s:status` gains a `pipeline` command routing to `pipeline-show`
  (bare relay) and `pipeline <preset>` routing to `--expand <preset>`.

Affected capabilities: `spec-status`, `build-spec-lifecycle`, `shipd-plan`,
`epic-autopilot` (all modified). Impact:
`plugins/s/skills/build/scripts/spec_status.py`,
`plugins/s/skills/build/scripts/autopilot.py` (one docstring),
`plugins/s/skills/build/SKILL.md`, `plugins/s/skills/plan/SKILL.md`,
`plugins/s/skills/autopilot/SKILL.md`, `plugins/s/skills/status/SKILL.md`,
tests in `plugins/s/skills/build/tests/test_spec_status.py` and
`plugins/s/skills/build/tests_pydantic/test_pipeline_show.py`, plugin
version bump. No new dependencies.

### Non-goals

- No renderer unification: the human `pipeline-show` lines and the dry-run
  labels keep their differing styles and keep rendering options (epic
  non-goal).
- No new pipeline semantics — no stages, options, presets, or grammar forms.
- No change to which entry forms the in-session drive honors — that is the
  sibling `insession-pipeline-fidelity` member; here only the *reading*
  mechanism moves to JSON.
- No `--json` on other verbs; the existing five-read-verb JSON mode is
  untouched.

## Implementation

- **Resolve-mode JSON shape.** `pipeline-show --json` prints exactly one
  indented JSON object: `{"source": <provenance>, "entries": [<dict>, ...]}`.
  `source` is the raw provenance value `resolve_pipeline` returns —
  `"default"`, a config file path, or `"preset:<name> (<config-path>)"` —
  not the text header's `[default]` decoration. `entries` is the resolved
  list verbatim: plain dicts carrying exactly the keys each entry declared.
  Rejected: a structured provenance object — the skills announce the string
  verbatim, and the existing `json-output` verbs keep metadata as plain
  values.
- **Expand-mode JSON.** `--expand <preset> --json` emits the same indented
  entry-list array as flagless expand: that output already is one JSON
  document (the fork-ready paste value) and expand resolves no config, so
  there is no provenance to add. The flag is accepted so a machine consumer
  can uniformly pass `--json`. Rejected: wrapping expand output in an
  object — it would break the documented paste-value contract.
- **Wiring.** Reuse `_add_json_flag` on the `pipeline-show` subparser and
  pass `as_json` into `cmd_pipeline_show`; update `_add_json_flag`'s
  docstring (no longer "only the five read verbs") and the module
  docstring's verb list and JSON paragraph. Text mode stays byte-identical
  without the flag; error handling (stderr `Error:` lines, exit codes) is
  unchanged in both modes — matching the `json-output` convention.
  Verified premises: `pipeline-show` exits 0 printing six stages with
  `[default]` here; `pipeline-show --expand basic` without pydantic exits 1
  with the install-hint error (both observed by running the verb).
- **Skill rewires.** `build/SKILL.md` step 1 runs `pipeline-show --json`;
  the "rendered labels are the API" bullet becomes "the JSON is the
  contract": options are read from the entry dicts, provenance from
  `source` (`"default"` means no announcement). `plan/SKILL.md`'s resolve
  step likewise (non-zero exit still stops the flow in both). In
  `autopilot/SKILL.md`, the in-session "Stage options declared by the
  resolved entry" section runs `pipeline-show --json` once per run and
  reads each entry's options from the dicts; the dry run keeps supplying
  member order only, and Phase 1's flagless `pipeline-show` display for
  the user stays. `autopilot.py`'s `_entry_label` docstring drops "which
  the in-session drive parses" — labels are human-facing only.
- **`/s:status` route.** `status/SKILL.md` adds a fourth command:
  `/s:status pipeline` runs `pipeline-show` and relays it verbatim;
  `/s:status pipeline <preset>` runs `pipeline-show --expand <preset>` and
  relays it — an unknown preset relays the CLI's known-preset listing,
  which is the discovery surface. The skill's frontmatter description
  mentions the pipeline report.
- **Tests split by dependency.** Stdlib-only cases (default resolution
  `--json`, `--expand default --json`, flagless text unchanged) go in
  `tests/test_spec_status.py`'s `PipelineShowTest`; declared-list and
  preset cases (options in entries, `preset:` source, invalid pipeline
  still erroring under `--json`) go in
  `tests_pydantic/test_pipeline_show.py`, per the existing suite split.
- **Plugin version bump** to 0.6.120 in
  `plugins/s/.claude-plugin/plugin.json` (standing convention; the change
  touches `plugins/s/`).

Risk: consumers of the epic's later `insession-pipeline-fidelity` member
build on this contract, so the JSON keys (`source`, `entries`) are named in
the delta spec and must not drift.
