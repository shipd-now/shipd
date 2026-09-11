## ADDED Requirements

### Requirement: Supersession gate documentation
id: supersession-gate-doc

The repository SHALL provide `docs/supersession-gate.md`, a concept guide to
the supersession gate that explains: why a planned change can go stale
between `/s:plan` and `/s:build`; build's Phase-0 sequence — the base-branch
sync, the `check-base` run, and the three outcomes (clean proceeds silently,
content drift proceeds with the findings carried into plan review, a
superseded plan stops the build for an abandon-or-re-scope decision); the
three finding kinds (`stale-base`, `missing-master`, `id-collision`) with
their meanings; the verb's exit codes; and the self-run invocation of the
status CLI's `check-base` verb. The guide SHALL conform to the shipd
documentation standard: `<!-- doc-type: concept -->` as its first line and a
total line count within the concept cap.

#### Scenario: Guide explains the gate's outcomes and findings
- **WHEN** `docs/supersession-gate.md` is inspected
- **THEN** it states the three Phase-0 outcomes, names the three finding
  kinds with their meanings, and shows the self-run `check-base` invocation

#### Scenario: Guide carries its marker and fits its cap
- **WHEN** `docs_lint.py` runs over `docs/supersession-gate.md`
- **THEN** it exits 0 with the file marked `concept`
