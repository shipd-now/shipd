# doctor-pipeline-check
Status: verified
Epic: pipeline-hardening

## Idea

`shipd doctor` gains a read-only `pipeline` check that resolves the
effective autonomous pipeline at the working directory, and the `pydantic`
check escalates from `warn` to `fail` when the declared pipeline actually
needs pydantic.

### Motivation

A repo whose declared `autonomous-pipeline` cannot resolve — malformed
entries, an unknown preset, or missing pydantic — passes `shipd doctor`
today: pydantic is a blanket `warn` and no check looks at the pipeline at
all, so the preflight green-lights environments where the configured
delivery pipeline is a hard stop.

### Details

- New `check_pipeline(root)` in `plugins/s/bin/shipd`: `ok` naming entry
  count and provenance when the pipeline resolves (the built-in default
  included), `fail` carrying the resolver's own error line when a declared
  pipeline cannot resolve. Reported directly after `config`.
- `check_pydantic` becomes context-aware: stays `warn` when nothing
  declared needs pydantic, `fail` when the resolved configuration declares
  a pipeline whose validation requires it.
- Follower surfaces kept in step: the `/s:doctor` skill's check list and
  remedy table (`plugins/s/skills/doctor/SKILL.md`), `docs/quickstart.md`'s
  check enumeration, tests in
  `plugins/s/skills/build/tests/test_shipd_cli.py`, and the plugin version
  bump.

Affected capabilities: `shipd-cli` (modified `doctor-verb`), `shipd-doctor`
(modified `doctor-remedy-boundaries`). Impact: `plugins/s/bin/shipd`,
`plugins/s/skills/doctor/SKILL.md`, `docs/quickstart.md`,
`plugins/s/skills/build/tests/test_shipd_cli.py`,
`plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No change to pipeline resolution itself — `spec_common.resolve_pipeline`
  is consumed as-is, never altered.
- No `--root` flag on `shipd doctor` — checks stay anchored at the working
  directory, matching `check_config`.
- No mutation from the CLI verb — remedies stay in the consent-gated
  `/s:doctor` skill; the verb remains read-only.

## Implementation

- **`check_pipeline(root, resolve=None)`** calls `_load_engine()` and
  `sc.resolve_pipeline(root)` (the `resolve` parameter is the test
  injection point, defaulting to the real resolver). On success it returns
  `("ok", "pipeline", "resolves: <n> entries (source: <provenance>)")`,
  rendering the no-declaration provenance as `default`. On
  `sc.ConfigError` it returns `("fail", "pipeline", str(exc))` — the
  resolver's own error line, verbatim. Rejected: shelling out to
  `spec_status.py pipeline-show` — a subprocess where an in-process call
  suffices, and the doctor path already lazy-loads the engine for
  `check_config`.
- **Runnable premise (observed):** in this worktree `plugins/s/bin/shipd
  doctor` printed `warn pydantic — not importable …` and `doctor: 1
  problem(s)` with exit `0` (this interpreter lacks pydantic); and
  `resolve_pipeline` on a repo declaring an entry list, and on the preset
  `"basic"`, raised exactly ``declared `autonomous-pipeline` (from
  <config-path>) requires pydantic; pip install -r requirements.txt``.
  That ConfigError string is what the new check surfaces.
- **Escalation predicate mirrors the resolver's pydantic-import path
  exactly.** A helper `_pipeline_needs_pydantic(root)` resolves the config
  via `sc.resolve_config(root)` and returns the supplying config path when
  the `autonomous-pipeline` value is a list, or a string in
  `sc.PIPELINE_PRESETS` other than `"default"`; it returns `None` (never
  escalating) for an absent key, the `"default"` preset, an unknown preset
  string, a non-list/non-string value, or a `ConfigError` — those last
  three already fail the `config`/`pipeline` checks. Rationale: the epic's
  success criterion is failing a repo whose declared pipeline *cannot
  run*; a `"default"`-preset repo runs without pydantic. Rejected:
  escalating on any declared key — it would fail a working environment.
- **`check_pydantic(root, find_spec=...)`** keeps the `find_spec`
  injection and gains the root. Importable → `ok`, unchanged. Missing with
  nothing requiring it → the existing `warn` text. Missing while
  `_pipeline_needs_pydantic(root)` names a config path → `fail` naming
  that path plus the `pip install -r requirements.txt` hint.
- **Ordering:** `default_checks(root)` returns python, git, config,
  pipeline, gh, textual, pydantic, snapshot, statusline (the
  `statusline` check shipped by `statusline-verb` stays last).
  `doctor_report` is untouched
  — any `fail` already exits `1`, so the escalated `pydantic` and the new
  `pipeline` check fail the preflight through the existing machinery.
- **Skill surfaces:** `plugins/s/skills/doctor/SKILL.md` step 2 lists
  `pipeline` among the checks; the remedy table's pydantic row covers the
  `warn` and the escalated `fail` alike (same command); a new `fail
  pipeline` row is report-only — never edit a `.shipd-config.json` —
  noting that when its detail names missing pydantic, the pydantic row's
  remedy is the fix.
- **Tests stay pydantic-free** (constitution): real tmp-config tests with
  `HOME` redirected cover the absent-key, `"default"`-preset, and
  declared-without-pydantic branches on this interpreter; the
  pydantic-present branches use the injected `resolve`/`find_spec`
  callables, matching `DoctorCheckTest`'s existing style. The ordering
  test extends to the nine-check sequence.
- **Version bump:** `plugins/s/.claude-plugin/plugin.json` 0.6.118 →
  0.6.119 (standing convention for `plugins/s/` changes).

Risks: running `shipd doctor` outside any repo reports the default
pipeline `ok` — acceptable and consistent with `check_config`'s cwd
anchoring. An unusable config file yields two `fail` lines (`config` and
`pipeline`) carrying the same underlying error — acceptable; both are true
findings and the exit code is unchanged by the duplication.
