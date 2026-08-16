## ADDED Requirements

### Requirement: Pipeline grammar documentation
id: pipeline-grammar-docs

The content directory's `README.md` (the format authority) SHALL document
the full shipped `autonomous-pipeline` grammar: the five entry forms; the
typed per-stage options (`model` as a symbolic tier — `session`,
`tier-below`, `tier-two-below` — or a concrete model id; `build`'s
`subagent_model`, `validator`, `telemetry`, and `parallelism`; `review`'s
`disposition` with its closed `all`/`high-only`/`none` set); the
`autopilot` options namespace (`attempts`, `timeout`, `max_resumes`) on any
stage or custom entry; the exclusivity rule that `skip` may only be `true`
when present and excludes every other field on the entry, with `tools` and
`replace` mutually exclusive; strict validation (unknown keys and wrongly
typed values rejected, defaults schema-declared and never injected into
resolved entries); and the rule that a declared entry list — and every
preset but `default` — requires pydantic and fails closed with an install
hint when it is not importable. The copyable config example JSON shipped in
the plugin's build references SHALL name the optional `autonomous-pipeline`
key with a pointer to that grammar, without actively declaring a pipeline.

#### Scenario: Eco expansion is hand-authorable from the README alone
- **WHEN** a reader compares `pipeline-show --expand eco`'s entries against
  the format authority's pipeline section
- **THEN** every key those entries carry (`skip`, `model`, `autopilot`,
  `validator`, `subagent_model`, `telemetry`, `disposition`) is documented
  there with its type and allowed values

#### Scenario: Skip exclusivity is stated correctly
- **WHEN** a reader consults the format authority on combining `skip` with
  other entry fields
- **THEN** it states that `skip` may only be `true` and that a skipped
  entry carries no other field, not merely that `skip`, `tools`, and
  `replace` are mutually exclusive

#### Scenario: Config example points at the key
- **WHEN** a reader opens the copyable config example JSON
- **THEN** it mentions the optional `autonomous-pipeline` key and where its
  grammar lives, while copying the file unchanged declares no pipeline
