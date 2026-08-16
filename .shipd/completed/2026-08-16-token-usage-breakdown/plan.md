# token-usage-breakdown
Status: verified

## Idea

Persist a per-tool token breakdown table into every built change and every
epic: the build writes a trailing `## Token usage breakdown` section into the
change's `tasks.md` before archive, and `epic-sync` aggregates its archived
members' tables into the same section at the bottom of `epic.md`.

### Motivation

A build's token spend is printed to chat as a per-model table and then lost —
neither the archived change nor the epic records which tools drove the spend,
so delegation-heavy builds (the dominant cost, per the subagent-token-tracking
investigation) leave no durable cost trace. The user asked for a per-tool
breakdown table at the bottom of each spec's `tasks.md` and each epic.

### Details

- New `--tool-table` mode in `build_report.py`: a markdown
  `## Token usage breakdown` section — table `Tool | Calls | Output tokens`,
  rows per tool across main and subagent transcripts, a `(no tool)` row,
  a bold Total — scoped by `--since`.
- The build flow writes that section as the trailing section of the change's
  `tasks.md` before `spec_merge` archives it (build `SKILL.md` edit).
- `epic-sync` additionally rewrites the epic's trailing
  `## Token usage breakdown` section by summing archived members' tables.

Affected capabilities: `build-reporting` (added), `spec-status` (added).
Impact: `plugins/s/skills/build/scripts/build_report.py`,
`plugins/s/skills/build/scripts/spec_status.py`,
`plugins/s/skills/build/SKILL.md`,
`plugins/s/skills/build/tests/test_build_report.py`,
`plugins/s/skills/build/tests/test_spec_status.py`,
`plugins/s/.claude-plugin/plugin.json` (version bump); no new dependencies.

### Non-goals

- No dashboard/board-graph changes — this change persists artifacts; the live
  charts are untouched.
- No dependency on the user-global build log (`~/.shipd/builds/`), which is
  `logging_enabled`-gated — epic aggregation reads only in-repo archived
  member tables.
- No input/cache columns — output tokens and call counts only, matching the
  board graph's metric.
- No retroactive backfill of already-archived changes or epics.

## Implementation

- **Per-response even-split attribution.** Each assistant response is counted
  once at its final usage snapshot (message-id keyed, per `build-reporting`'s
  `usage-dedup`), and its output tokens split evenly across the `tool_use`
  blocks its records carry (union across the response's records); a response
  with no tool call lands in `(no tool)`. Rejected: per-record delta
  attribution — accurate only for subagent transcripts (one content block per
  snapshot record, observed), skewed for main transcripts, which stamp the
  final usage on every record. Settled as Q1 (oracle).
- **Subagent tokens count natively under their own tool rows** — a subagent's
  Bash spend merges into the same Bash row as the main session's, mirroring
  the per-model table's flat attribution; no `Agent` roll-up row. Settled as
  Q2 (oracle).
- **Table grammar.** `## Token usage breakdown` heading, then a
  `Tool | Calls | Output tokens` markdown table, rows sorted by output tokens
  descending, `Calls` = number of tool_use invocations (0 for `(no tool)`),
  a bold `**Total**` row. Number formatting reuses the existing report
  helpers. The same grammar serves `tasks.md` and `epic.md`, so the epic
  aggregator parses exactly what the build wrote.
- **Write points.** The build flow generates the section with
  `build_report.py --since "$BUILD_START" --tool-table` and writes it as the
  trailing section of `planned/<change>/tasks.md` (replacing an existing one)
  immediately before the Phase-6 `spec_merge`, so it archives with the
  change. Lint-safe: the tasks linter inspects only checkbox lines. Rejected:
  writing after archive — `completed/` is immutable.
- **Epic aggregation rides `epic-sync`.** `cmd_epic_sync` (already the
  PR-shipped epic derivation verb) resolves each member's archived change the
  way its state derivation already does, parses the member's trailing
  breakdown table, sums per-tool rows, and idempotently replaces the epic's
  trailing section; members without tables contribute nothing, and with no
  tables at all the section is absent. The draft-epic guard is unchanged.
  Epic lint requires only its four sections to be present, so the extra
  trailing section is legal (`spec_lint.py` epic checks).
- **Verified premises.** `build_report.py --since 2026-08-16T00:00:00Z
  --table` renders the per-model table and exits 0 (run); the stdlib test
  suite passes (`unittest discover`, 41 OK in `test_build_report.py`);
  `test_spec_status.py` already carries an epic-sync test class to extend.
- **Ordering dependency.** Builds on `subagent-token-tracking`'s
  final-snapshot counting (same file, `build_report.py`): build this change
  only after that change merges, rebasing `change/token-usage-breakdown`
  onto updated `main` first.
- Risk: a member's `tasks.md` table edited by hand could fail to parse —
  the aggregator skips an unparseable table (contributing nothing) rather
  than failing the sync.

## Questions and answers

### Q1: How are a response's output tokens attributed to tool rows?
- **Question:** How should a single assistant response's output tokens map to
  tool rows when one message calls several tools, or none? Options:
  (a) per-response even split across its tool_use blocks, tool-less
  responses in a `(no tool)` row; (b) per-record delta attribution to each
  record's own content block. Recommendation: (a).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Per-response even split (a). The response is the repo's atomic
  unit of token accounting (`usage-dedup` counts each response once and
  treats per-record repeats as duplication), and the sampling requirement
  sets the precedent of distributing a response's tokens across finer units
  while preserving the total exactly; (b) is accurate for only one of the
  two transcript shapes.
- **Cited:** verified/build-reporting, verified/build-telemetry,
  verified/delivery-metrics

### Q2: Where do subagent-generated tokens appear in the table?
- **Question:** Do a subagent transcript's tokens appear under the subagent's
  own tool rows, or fold entirely under one `Agent` row? Options: (1) fold
  under `Agent`, matching the harness's own `Agent(...)` display; (2) count
  natively under the subagent's own tool rows. Recommendation: (1).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Count natively under the subagent's own tool rows (2),
  overriding the recommendation. The verified per-model accounting already
  merges orchestrator and subagent records into the same breakdown rows with
  no delegation row, and this workflow delegates most implementation — one
  `Agent` row would collapse the table into a single dominant figure, the
  opaque presentation the subagent-token-tracking change exists to fix.
- **Cited:** verified/build-telemetry, verified/build-reporting
