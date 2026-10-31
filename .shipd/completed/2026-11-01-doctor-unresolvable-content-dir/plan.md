# doctor-unresolvable-content-dir
Status: verified
Planned-at: 4a6a5cd9c93128aae1542bfa3f926ced0e8c6080
Gated-hash: 3a5d1de51e58

## Idea

Document that the doctor's `schema` and `local-state` checks skip, rather
than fail or raise, when the content directory cannot resolve.

### Motivation

A reader checking `shipd doctor` output against the `shipd-cli` spec finds no
documented outcome for these two checks under an invalid or malformed config.
The shipped behavior from PR #401 therefore has no contract a validator or
reviewer can hold it to.

### Details

- Modify `doctor-schema-check`: a configuration that resolves no content
  directory reports `ok`, carrying the error, and says the check was skipped.
  A marker that resolves but cannot be read still fails.
- Modify `doctor-local-state-check`: the same skip outcome for a configuration
  that resolves no content directory.
- Each requirement gains one scenario for an invalid `dir`.

Affected capabilities: `shipd-cli` (modified). Impact: spec only; the code in
`plugins/s/bin/shipd` already implements this, so no plugin version bump.

### Non-goals

- No code change to `check_schema`, `check_local_state`, or any other check.
- The `pipeline` check's failure on a malformed config stays as documented by
  `doctor-verb`; it is out of scope here.
- No change to the `config`, `wiki`, `store`, or `store-sync` requirements.

## Implementation

- Mirror the wording `doctor-store-check` and `doctor-store-sync-check`
  already use: "the check never double-fails what the `config` check owns".
  One phrase for one meaning across the doctor requirements. Rejected: a new
  shared requirement for config tolerance — it would restate rules four
  requirements already carry.
- Keep the schema check's existing `fail` outcome for a resolved but garbled
  marker, stated explicitly, so the skip cannot be read as covering it.
- Restate every existing scenario in both MODIFIED entries unchanged, because
  a MODIFIED entry replaces the requirement wholesale. No scenario is dropped.
- The new scenarios use an invalid `dir` (`../specs`), the case the shipped
  regression tests exercise. The prose covers any configuration that fails
  to resolve, which the observed malformed-JSON run also confirms.
- Tasks verify the shipped behavior only: they run the existing tests and the
  doctor command. A spec-only change adds no code, so no test-first pair.

Risk: the delta could drift from shipped code. The verification tasks run the
real command and tests, so a mismatch fails the build.

## Readiness attestation

### Problem and motivation

The doctor specs leave the unresolvable-content-directory outcome for `schema`
and `local-state` undocumented, so the PR #401 behavior has no contract.

Evidence:

- `doctor-schema-check` and `doctor-local-state-check` in capability
  `shipd-cli` name no config-failure outcome.
- `doctor-store-check` carries the scenario "Malformed config is reported, not
  double-failed"; the two edited requirements carry none.

### Scope and non-goals

Two requirements in one capability change; code and every other doctor check
stay as they are.

Evidence:

- In scope: `shipd-cli` requirements `doctor-schema-check` and
  `doctor-local-state-check`.
- Out of scope: `pipeline` behavior under `doctor-verb`; code at
  `plugins/s/bin/shipd:608` and `plugins/s/bin/shipd:647` is not edited.

### Affected capabilities and files

One capability is affected; the tasks touch no file and only verify.

Evidence:

- Capability `shipd-cli`: `doctor-schema-check` (base f840eaa6ec94) and
  `doctor-local-state-check` (base d562a844eaca), hashes from
  `spec_status.py base-hash`.
- Code already shipped: `plugins/s/bin/shipd:626` and
  `plugins/s/bin/shipd:671` emit `content directory unresolvable — skipped`.
- Tests already shipped:
  `plugins/s/skills/build/tests/test_shipd_cli.py:1768` and
  `plugins/s/skills/build/tests/test_shipd_cli.py:1893`.
- Runnable premise: `shipd doctor` in a git repo with `{"dir": "../specs"}`
  printed `fail config`, `ok schema — content directory unresolvable —
  skipped (...)`, `ok local-state — content directory unresolvable — skipped
  (...)`, and `doctor: 1 problem(s)`, exit 1.
- Runnable premise: with `{not json` as the config, `schema` and
  `local-state` printed the same skip line; `config` and `pipeline` failed,
  `doctor: 2 problem(s)`, exit 1.

### No open task-shaping decision

Every task-shaping decision is settled by investigation; none remain.

Evidence:

- Scenario case (invalid `dir`): settled by investigation — the shipped tests
  exercise it.
- Pipeline exclusion: settled by investigation — `doctor-verb` documents its
  `fail` outcome.
- Version bump: settled by investigation — AGENTS.md requires one only for
  changes under `plugins/s/`, and this change edits none.
