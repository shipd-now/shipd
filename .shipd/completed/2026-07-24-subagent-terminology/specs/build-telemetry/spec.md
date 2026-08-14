# build-telemetry — delta

## MODIFIED Requirements

### Requirement: Per-model token accounting from transcripts
id: per-model-token-accounting-from-transcripts
base: aa56a8ff0251
The telemetry tool SHALL compute a build's token usage by reading the current
session transcript and every subagent transcript for that session, aggregating
usage per model. It SHALL source counts from the transcript usage fields:
`input_tokens` (non-cached input), `output_tokens`, `cache_creation_input_tokens`
(cache write), and `cache_read_input_tokens` (cache read).

#### Scenario: Orchestrator and sub-agents are both counted
- **WHEN** the tool runs after a build that spawned execution sub-agents
- **THEN** the totals include usage from the orchestrator's session transcript AND
  from each subagent transcript, attributed to the correct model per record

#### Scenario: Usage is broken down per model
- **WHEN** a build uses more than one model (e.g. an orchestrator model and a
  cheaper execution model)
- **THEN** the tool can report a separate token breakdown for each model
