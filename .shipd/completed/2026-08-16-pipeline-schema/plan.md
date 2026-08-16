# pipeline-schema
Status: verified
Epic: named-pipelines

## Idea

Replace the hand-rolled autonomous-pipeline entry validator with a pydantic
discriminated-union schema carrying typed per-stage options and an
`autopilot`-namespaced driver-knob block, validated fail-closed on declared
pipelines while the default pipeline stays stdlib-only.

### Motivation

The hand-rolled validator at `spec_common.py:477` can only check the five
bare entry forms, so the epic's per-stage options (model tiers, validator
toggle, disposition depth, retry attempts) have nowhere typed to live and
user-authored pipelines get no strict unknown-key rejection.

### Details

- New module `plugins/s/skills/build/scripts/pipeline_schema.py`: pydantic
  models for every stage entry plus the custom form, `extra="forbid"`.
- `resolve_pipeline` (`spec_common.py`) lazily imports it only for a
  *declared* pipeline; pydantic missing → `ConfigError` with an install
  hint; the no-key default path is untouched and stdlib-only.
- Migrate the declared-pipeline tests from the stdlib suite to a new
  `plugins/s/skills/build/tests_pydantic/` suite; add option-field and
  fail-closed tests; add the CI step running the new suite after the
  requirements install.

Affected capability: `shipd-config` (modified + added requirements).
Impact: `plugins/s/skills/build/scripts/spec_common.py`, new
`plugins/s/skills/build/scripts/pipeline_schema.py`,
`plugins/s/skills/build/tests/test_spec_common.py`, new
`plugins/s/skills/build/tests_pydantic/`, `.github/workflows/ci.yml`,
`plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No preset names (`"eco"` etc.) — the key's string form is the
  `pipeline-presets` member; here the key remains a JSON list only.
- No consumer changes: autopilot, `/s:build`, `/s:plan`, `/s:review`, and
  `pipeline-show` rendering are untouched (epic members 4–6); the new
  option fields are validated and carried, not yet acted on.
- No engine-wide pydantic import: nothing outside the declared-pipeline
  validation path imports it, per the constitution's scoped exception.
- No stdlib-suite dependency: `plugins/s/skills/build/tests/` keeps passing
  with pydantic absent.

## Implementation

- **Module boundary.** `pipeline_schema.py` imports pydantic at module top —
  legal because only `resolve_pipeline`'s declared-pipeline branch imports
  the module, and lazily (function-local import). `spec_common.py` itself
  gains no top-level third-party import. The fail-closed catch is specific:
  `ModuleNotFoundError` on that lazy import → `ConfigError` reading
  "declared `autonomous-pipeline` requires pydantic; pip install -r
  requirements.txt" (naming the provenance file); any other exception
  propagates — it is a real bug, not a missing dependency.
- **Model set (discriminated on `stage` / presence of `custom`).**
  `AutopilotOpts`: `attempts: int >= 1 = 3`, `timeout: int > 0 | None`,
  `max_resumes: int >= 0 | None`; `extra="forbid"`. Tier type: `str`,
  non-empty; the symbolic values `session`, `tier-below`, `tier-two-below`
  are documented constants (`SYMBOLIC_TIERS` tuple exported by the module);
  any other non-empty string is a concrete model id — no closed enum, so
  new model ids never need a schema release. Common stage fields: `stage`
  (Literal per model), `skip: bool = False` (only `True` accepted when
  present, mirroring today), `tools`, `replace`, `model: Tier | None`,
  `autopilot: AutopilotOpts | None`. Stage-specific: **build** adds
  `subagent_model: Tier | None`, `validator: bool = True`,
  `telemetry: bool = True`, `parallelism: int >= 1 | None`; **review** adds
  `disposition: Literal["all", "high-only", "none"] = "all"`. `tools` items:
  `{name: non-empty str, fallback: Literal["builtin", "skip"]}`; `replace`:
  `command` or `tool` (at least one) + the same `fallback` — both
  `extra="forbid"`. Custom form: `custom` (kebab slug, reuse
  `KEBAB_RE.pattern`), `command` (non-empty), optional `autopilot`.
- **Exclusivity rules** (model validators): `skip: true` excludes every
  other field except `stage` — a skipped stage carries no options (today
  skip excludes only `tools`/`replace`; the tightening is deliberate:
  options on a skipped stage are dead config and likely a mistake).
  `tools` and `replace` stay mutually exclusive with each other and with
  `skip`. Options (`model`, `autopilot`, build/review extras) combine
  freely with bare, `tools`, and `replace` forms.
- **Return-type compatibility.** `resolve_pipeline` keeps returning
  `(list-of-dicts, provenance)`: each validated model is dumped with
  `model_dump(exclude_unset=True)` so entries carry exactly the keys the
  user declared — today's consumers (`entry.get("stage")` in autopilot,
  `_entry_label`, `_format_pipeline_entry`) behave identically, and the
  wholesale/provenance semantics are unchanged. `pipeline_schema.py`
  exposes `validate_entries(raw) -> list[dict]` (raises `ValueError` with
  per-entry lines) plus the model classes for future consumers that want
  typed defaults re-parsed.
- **Error rendering preserved.** `validate_entries` wraps pydantic's
  `ValidationError` into lines prefixed `entry <i>
  (<compact-sorted-json>): <field-path>: <message>` — the same
  index-and-content naming the current messages carry, collected across
  *all* bad entries before raising (matching
  `test_every_offending_entry_is_reported`). `resolve_pipeline` re-raises
  the joined lines as `ConfigError`.
- **Cross-entry canonical order stays where it is** — the existing
  order-check loop in `resolve_pipeline` operates on the returned dicts and
  is untouched; pydantic owns per-entry shape only.
- **Test placement.** The `DeclaredPipeline` tests (declared-list cases,
  `test_declared_list_is_wholesale` through
  `test_pipeline_not_a_list_errors`, `test_spec_common.py:777-1040`
  region) move to `tests_pydantic/test_pipeline_schema.py` (new suite dir
  with the same `home_set_to` isolation pattern — copy the small helpers
  the moved tests need rather than importing the stdlib suite's module),
  extended with: option-field acceptance (each new field), unknown-key
  rejection, `attempts` bounds, tier non-empty check, skip-excludes-options,
  and `exclude_unset` round-trip (a declared `{"stage": "build"}` dump has
  exactly `{"stage": "build"}`). The stdlib suite keeps
  `test_registry_is_canonical_ordered_names`,
  `test_absent_key_yields_full_default`, and gains the fail-closed test:
  patch the import machinery so importing `pipeline_schema`/`pydantic`
  raises `ModuleNotFoundError`, assert a declared pipeline raises
  `ConfigError` naming pydantic and `requirements.txt` — deterministic on
  machines with or without pydantic installed.
- **CI.** After the existing "Install third-party deps" step, add: `Run
  pydantic-dependent test suite` → `python3 -m unittest discover -s
  plugins/s/skills/build/tests_pydantic -v`, mirroring the
  `tests_textual` step. The stdlib engine suite keeps running before the
  install, which is what proves the default path needs no pydantic.
- **Runnable premises (observed pre-plan):** `spec_status.py
  pipeline-show` prints the six-stage default with source `[default]`,
  exit 0 — must be byte-identical after this change on a no-key repo;
  `python3 -c "import pydantic"` fails on this machine
  (ModuleNotFoundError), so the new stdlib fail-closed test and the
  unchanged-default premise are both genuinely exercised here.
- **Version bump** in `plugins/s/.claude-plugin/plugin.json` (change
  touches `plugins/s/`).

Risk: pydantic v2 minor releases changing `ValidationError` message text —
guarded by asserting on our own rendered `entry <i> (...)` lines and field
paths, never on pydantic's prose.
