# doctor-pipeline-config-skip
Status: verified
Planned-at: 330105c2c4808869180a3eb10a4b3098198f3241
Gated-hash: 3853519c3c80

## Idea

Make the doctor's `pipeline` check skip, rather than fail, when the layered
configuration cannot load at all.

### Motivation

A user whose `.shipd-config.json` is malformed sees `shipd doctor` report two
problems for one mistake, because `pipeline` repeats the `config` failure.
They cannot tell from the count that one fix clears both.

### Details

- `check_pipeline` resolves the configuration first. A `ConfigError` there
  reports `ok pipeline — configuration unresolvable — skipped (<error>)`.
- A configuration that loads still runs the pipeline resolver. A declared
  pipeline with malformed entries or an unknown preset still fails.
- One new `shipd-cli` requirement states the skip, with two scenarios.
- One regression test file gains two tests; the plugin version moves to
  0.6.359.

Affected capabilities: `shipd-cli` (one requirement added). Impact:
`plugins/s/bin/shipd`, `plugins/s/skills/build/tests/test_shipd_cli.py`,
`plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- An invalid `autonomous-pipeline` value still fails both `config` and
  `pipeline`; `pipeline` stays the delivery surfaces' hard stop.
- No change to `doctor-verb`'s text or scenarios, or to any other check.
- No change to `resolve_config`, `resolve_pipeline`, or
  `pipeline_from_config` in `spec_common.py`.

## Implementation

- Split the resolve inside `check_pipeline` (`plugins/s/bin/shipd:591`).
  When the caller passes no `resolve`, call `sc.resolve_config(root)` inside
  its own `try`. On `sc.ConfigError` return `("ok", "pipeline",
  "configuration unresolvable — skipped (%s)" % exc)`. Otherwise set
  `resolve` to a closure returning `sc.pipeline_from_config(config, prov)`,
  then run the existing `try` that maps `ConfigError` to `fail`.
- Keep the `resolve=` parameter and its behavior unchanged when a caller
  passes it. Two existing tests inject it, and an injected resolver still
  fails on `ConfigError`. Rejected: replacing the parameter with two hooks,
  which would rewrite those tests for no behavioral gain.
- Extend the docstring: an unloadable configuration is reported as the detail
  rather than failing, because the `config` check owns it.
- Add a new requirement instead of modifying `doctor-verb`. `doctor-verb`
  names only malformed entries and unknown presets as `pipeline` failures, so
  an unloadable file is an unstated case, not a contradiction. Rejected:
  restating `doctor-verb` in full, which carries 25 scenarios and would
  overrun the delta budget.
- Bump `plugins/s/.claude-plugin/plugin.json` from 0.6.358 to 0.6.359, as
  AGENTS.md requires for any change under `plugins/s/`.

Risk: the autopilot preflight reads `doctor:pipeline`. An unloadable config
still fails that preflight through `doctor:config`, so a run never launches
on a broken config.

## Questions and answers

### Q1: How far should the pipeline check defer to the config check?
- **Question:** Should `pipeline` skip only when the configuration cannot
  load, or also when a loaded configuration declares an invalid
  `autonomous-pipeline` that `config` already fails? Options: (1) unloadable
  configuration only; (2) any error `config` reports. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Unloadable configuration only. A bad pipeline value still fails
  both checks, because the spec names `pipeline` as the delivery hard stop.
- **Queued:** q-doctor-pipeline-defer-scope

## Readiness attestation

### Problem and motivation

A malformed configuration fails both `config` and `pipeline`, so doctor
counts one mistake as two problems.

Evidence:

- `plugins/s/bin/shipd:591` maps every `ConfigError` from
  `sc.resolve_pipeline` to `fail pipeline`, including a load error from
  `resolve_config`.
- Capability `shipd-cli`, requirement `doctor-store-check`, states the
  "reported, not double-failed" rule the `pipeline` check lacks.

### Scope and non-goals

The `pipeline` check changes only for an unloadable configuration; every
other outcome and check is unchanged.

Evidence:

- In scope: `check_pipeline` at `plugins/s/bin/shipd:591`.
- Out of scope: `doctor-verb` (base 0a043ef30352) stays as written; its
  scenario "Unresolvable declared pipeline fails the preflight" still holds.
- Out of scope: `pipeline_from_config` at
  `plugins/s/skills/build/scripts/spec_common.py:1101` is not edited.

### Affected capabilities and files

One capability gains a requirement; three files change.

Evidence:

- Capability `shipd-cli`: ADDED requirement `doctor-pipeline-unloadable-config`.
- Files: `plugins/s/bin/shipd:591`,
  `plugins/s/skills/build/tests/test_shipd_cli.py:1691`,
  `plugins/s/.claude-plugin/plugin.json:4`.
- Runnable premise: `shipd doctor` with `{not json` as the config printed
  `fail config` and `fail pipeline`, then `doctor: 2 problem(s)`.
- Runnable premise: `shipd doctor` with `{"autonomous-pipeline": "nope"}`
  printed `fail config` and `fail pipeline`, both naming the unknown preset
  `nope`.
- Runnable premise: `sc.resolve_pipeline` is `resolve_config` followed by
  `pipeline_from_config(config, prov)`, at
  `plugins/s/skills/build/scripts/spec_common.py:1070-1098`.

### No open task-shaping decision

Every task-shaping decision is settled.

Evidence:

- Defer scope: settled by the user, Q1.
- New requirement over a `doctor-verb` rewrite: settled by investigation of
  the requirement's scenario count and wording.
- Keeping the `resolve=` hook: settled by investigation of the two tests
  that inject it.
