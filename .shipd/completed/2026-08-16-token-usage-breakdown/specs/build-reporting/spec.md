## ADDED Requirements

### Requirement: Per-tool token breakdown
id: tool-usage-breakdown

The build-report CLI SHALL provide a `--tool-table` mode that prints a
markdown `## Token usage breakdown` section: a table with columns
`Tool | Calls | Output tokens` holding one row per tool name invoked across
the session's main and subagent transcripts (merged into the same rows), a
`(no tool)` row for responses carrying no tool call, rows sorted by output
tokens descending, and a bold `**Total**` row. Each assistant response SHALL
be counted once at its final usage snapshot, keyed by message id with
synthetic records skipped, its output tokens split evenly across the
`tool_use` blocks its records carry (the union across the response's
records) and its `Calls` contribution being those blocks' count — so the
table's total equals the deduplicated response total exactly. The mode SHALL
honor `--since` scoping like the existing per-model table. If no transcript
resolves or no responses are in scope, then the mode SHALL print nothing and
exit zero.

#### Scenario: A multi-tool response splits evenly
- **WHEN** a response with 100 output tokens carries two `tool_use` blocks,
  `Bash` and `Read`
- **THEN** the table adds 50 output tokens and one call to each of the
  `Bash` and `Read` rows

#### Scenario: A tool-less response lands in the no-tool row
- **WHEN** a response carries only text and thinking blocks
- **THEN** its output tokens land in the `(no tool)` row with no call counted

#### Scenario: Subagent tool calls merge natively
- **WHEN** a subagent transcript's response invokes `Bash` and the main
  transcript also invokes `Bash`
- **THEN** both responses' tokens accumulate in the single `Bash` row

#### Scenario: Cumulative snapshots count the final value once
- **WHEN** one message id spans three records whose `output_tokens` snapshots
  are 1, 1, then 331, the last carrying a `tool_use` block
- **THEN** the table attributes 331 tokens for that response, not 333

#### Scenario: The total preserves the deduplicated sum
- **WHEN** the table renders over responses summing to N deduplicated output
  tokens
- **THEN** the `**Total**` row shows exactly N and the tool rows sum to N

#### Scenario: An empty scope prints nothing
- **WHEN** `--tool-table` runs with a `--since` newer than every record
- **THEN** nothing is printed and the exit code is zero
