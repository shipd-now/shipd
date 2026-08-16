# pipeline-docs-sweep
Status: verified
Epic: pipeline-hardening

## Idea

Bring every pipeline teaching surface — the format-authority
`.shipd/README.md`, root `README.md`, the copyable config example JSON, and
`docs/quickstart.md` — to the shipped `autonomous-pipeline` grammar, and
correct the three known documentation falsehoods the pipeline-hardening
audit named.

### Motivation

The named-pipelines epic shipped typed per-stage options, the `autopilot`
options namespace, and strict pydantic validation, but the format-authority
docs still describe the pre-epic grammar — `.shipd/README.md` documents
neither the per-stage options nor the real skip-exclusivity rule, so a user
cannot hand-author what `pipeline-show --expand eco` prints. Three known
falsehoods mislead readers besides: the `pipeline_schema.py` docstring's
dashboard-pydantic claim, the stale "Three-strike" requirement title, and
the named-pipelines epic table's `default` column.

### Details

- `.shipd/README.md` pipeline section: document the per-stage options, the
  `autopilot` namespace, the real exclusivity rule, strict typing with
  defaults-never-injected, and the declared-list-requires-pydantic rule.
- Root `README.md` pipeline paragraph and
  `plugins/s/skills/build/references/shipd.config.example.json` follow with
  a brief options mention / key pointer.
- `docs/quickstart.md`: doctor check list gains `pydantic`; one-line eco
  opt-in mention added.
- Falsehood corrections: `pipeline_schema.py` module docstring,
  `epic-autopilot`'s `three-strike-parking` requirement title (via delta),
  and `.shipd/epics/named-pipelines/epic.md`'s `default` preset column.

Affected capabilities: `shipd-config` (added docs requirement),
`project-readme` (added), `epic-autopilot` (modified retitle). Impact:
`.shipd/README.md`, `README.md`, `docs/quickstart.md`,
`plugins/s/skills/build/references/shipd.config.example.json`,
`plugins/s/skills/build/scripts/pipeline_schema.py` (docstring only),
`.shipd/epics/named-pipelines/epic.md`,
`plugins/s/.claude-plugin/plugin.json` (version bump). No dependencies.

### Non-goals

- No pipeline semantics, grammar, or preset changes — documentation only
  (epic non-goal: existing semantics made documented, not extended).
- No rename of the stable requirement id `three-strike-parking` and no
  rename of `autopilot.py`'s internal `_strike_loop` naming — ids and
  internal identifiers are stable; only the human-readable title is stale.
- No documentation of the future doctor `pipeline` check — that ships with
  the `doctor-pipeline-check` member; quickstart lists the checks as
  shipped today.
- No `pipeline-show --json` documentation and no renderer changes — other
  epic members own those.

## Implementation

- **The verified `shipd-config` spec is the truth source.** The
  `.shipd/README.md` grammar additions mirror the `pipeline-entry-validation`,
  `pipeline-stage-options`, and `pipeline-presets` requirements verbatim in
  substance. Rejected: restating from `pipeline_schema.py` source — the spec
  is the contract the schema implements.
- **Exclusivity correction.** Replace `.shipd/README.md`'s sentence
  "`skip`, `tools`, and `replace` are mutually exclusive on one entry" with
  the shipped rules: `skip` may only be `true` when present and excludes
  every other field on the entry (options on a skipped stage are an error);
  `tools` and `replace` are mutually exclusive; unknown keys and wrongly
  typed values are rejected (strict validation); defaults are
  schema-declared and never injected — a resolved entry carries exactly the
  keys its author wrote.
- **Options documentation.** Every stage entry may carry `model` (symbolic
  tier `session`/`tier-below`/`tier-two-below` or a concrete model id);
  `build` adds `subagent_model`, `validator` (default true), `telemetry`
  (default true), `parallelism` (>= 1); `review` adds `disposition`
  (`all`/`high-only`/`none`, default `all`); any stage or custom entry may
  carry `autopilot` with `attempts` (>= 1, default 3), `timeout` (> 0),
  `max_resumes` (>= 0). A declared list — and every preset but `default` —
  requires pydantic and fails closed with the `pip install -r
  requirements.txt` hint (observed: `pipeline-show --expand eco` without
  pydantic printed exactly that error).
- **Retitle keeps the id.** The `epic-autopilot` delta retitles
  `three-strike-parking` to "Attempt-budget failure handling" via MODIFIED
  (base `78864b825c78`), body and scenarios unchanged. Rejected: RENAMED —
  `stable-requirement-identifiers` exists precisely so titles can change
  while citations (e.g. `tests/test_autopilot.py:553`) stay valid.
- **Example JSON stays copy-safe.** The example gains a `"//"`-style
  comment naming the optional `autonomous-pipeline` key (preset name such
  as `"eco"`, or an entry list; grammar in `.shipd/README.md`) — not an
  active key, so copying the file never silently declares a wholesale
  pipeline.
- **`default` column correction.** The archived epic's design table
  `default` column becomes the shipped truth: bare stage entries, schema
  defaults apply but are never injected (matching `PRESETS["default"]`).
  The epic file is not an immutable artifact; `completed/` archives are
  untouched.
- **Docstring correction.** `pipeline_schema.py`'s claim that
  `dashboard.py`'s `tui` is the other pydantic-dependent module becomes the
  constitution's actual scoping: this module is the engine's only
  pydantic-dependent path; `tui`'s third-party exception is `textual`.
- **No engine behavior changes**, so the constitution's engine-tests rule
  is discharged by the stdlib suite passing unchanged (barrier task).
  Version bump per the standing plugins/s convention (current 0.6.117).

Risk: quickstart's doctor list goes stale again when `doctor-pipeline-check`
lands; accepted — that member owns its own doc updates, and the new
`project-readme` requirement makes the list a checkable contract.
