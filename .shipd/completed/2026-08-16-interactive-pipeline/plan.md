# interactive-pipeline
Status: verified
Epic: named-pipelines

## Idea

Make the interactive `/s:build` and `/s:plan` skills resolve the shared
`autonomous-pipeline` and honor its per-stage options in their phases,
completing the `named-pipelines` epic.

### Motivation

The schema, presets, review options, and autopilot honoring (members 1-5)
are all shipped, but a hand-driven `/s:build` or `/s:plan` never reads the
declared pipeline — so `{"autonomous-pipeline": "eco"}` cuts nothing on
interactive deliveries, and a typo'd pipeline is only discovered when the
autopilot runs.

### Details

- `/s:build` resolves the pipeline once at flow start via
  `spec_status.py pipeline-show` and honors, per the resolved entries:
  `subagent_model` (Agent-tool model on `s:sub-agent` and `s:validator`
  spawns), `parallelism` (fan-out cap), `validator` false (skip the
  adversarial validation gate), `telemetry` false (skip the per-tool
  persist and the report's token blocks), and the review entry's
  `disposition`/`model` (passed to the `/s:review` post flow). A skipped
  or absent review entry in a declared pipeline means no gate post.
- `/s:plan` resolves the pipeline at start, announces its provenance when
  a layer declares one, and stops on a resolution error; its internal
  context gate runs regardless of the pipeline's gate entry.
- Both flows stop fail-closed on a resolution error and ignore
  `autopilot` blocks, `replace` bindings, and a `skip` on the very stage
  the user explicitly invoked.

Affected capabilities: `build-spec-lifecycle` (modified),
`build-reporting` (modified), `shipd-plan` (modified). Impact:
`plugins/s/skills/build/SKILL.md`, `plugins/s/skills/plan/SKILL.md`,
`plugins/s/.claude-plugin/plugin.json` (version bump). Markdown-only —
no engine script changes, no new tests required by the constitution.

### Non-goals

- No schema, preset, resolver, or `pipeline-show` changes — members 2-3
  shipped them; the skills consume the rendered labels as-is.
- No `/s:review` skill or `review_gate.py` changes — member 4 shipped the
  invoker contract (`disposition=`/`model=` passed through, scope-aware
  loops); this change only makes `/s:build` the passing invoker.
- No autopilot changes — member 5 shipped conveyance and in-session
  honoring; the in-session drive's text is mirrored, not moved.
- No interactive enforcement of `autopilot.*` budgets, `replace`
  commands, or custom steps — those stay driver semantics.
- No status forcing in `/s:plan`: the context gate remains the only path
  to `ready`, whatever the pipeline's gate entry says.

## Implementation

- **Resolution mechanism: one `pipeline-show` run, labels are the API.**
  Each skill runs `python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/
  spec_status.py" pipeline-show` once at flow start and reads the
  declared options from the rendered entry labels (`build
  subagent_model=tier-two-below, validator=false, ...`), never
  re-deriving them from config files — the same doctrine the autopilot
  skill already states. Verified by running it: an eco-configured repo
  prints all six entries with options and `preset:eco (<config-path>)`
  provenance (exit 0); a `"validater"` typo exits 1 printing `entry 0
  ({"stage": "build", "validater": false}): build.validater: Extra
  inputs are not permitted`; with pydantic
  absent it exits 1 with the `pip install -r requirements.txt` hint.
  Rejected: a new machine-readable verb — the labels already carry every
  declared key deterministically.
- **Fail-closed stop.** A non-zero `pipeline-show` (validation error or
  missing pydantic) stops either flow with the engine's own error text —
  a declared pipeline never half-runs. A default pipeline (`[default]`
  provenance) changes nothing and is not announced by `/s:plan`.
- **Model resolution is session-relative**, mirroring the autopilot
  skill's in-session table verbatim: `session` → omit the Agent `model`
  parameter; `tier-below`/`tier-two-below` → one/two steps below the
  session's own model on `fable` → `opus` → `sonnet` → `haiku`, clamped
  at `haiku`; anything else is a concrete id passed verbatim. A declared
  `subagent_model` governs both `s:sub-agent` and `s:validator` spawns
  (the validator stays on the executors' tier). The build entry's own
  `model` is ignored interactively — the session's model is the user's
  choice. Rejected: resolving via a Python call — the skill already
  knows its own model and the ladder is three lines of prose.
- **Fan-out cap precedence**: pipeline `parallelism` > the
  `~/.shipd-config.json` `parallelism` key > default 3 — the per-repo
  pipeline entry is the more specific declaration.
- **Telemetry opt-out scope** mirrors the shipped conveyance line ("do
  not persist the per-tool token breakdown and do not render the token
  report"): skip the Phase 6 tasks.md persist and the report's token
  summary, per-model table, and total-runtime line; the report opens
  `Build complete.` and keeps the change header, warnings, description,
  and Observations. The persistent build log stays best-effort and
  unchanged. Rejected: skipping the log too — it is not rendered output
  and other tooling reads it.
- **Review options ride the existing invoker contract**: the ship flow's
  gate posting passes `--disposition <scope>`/`--model <tier>` from the
  resolved review entry and follows the review skill's matching scoped
  disposition loop. `model` on review is recorded provenance, per the
  review skill. Where a declared pipeline skips or omits review, build
  posts no gate; the PR watch already surfaces a PR blocked on a
  still-required check.
- **Conveyed options win.** When a driving invoker (the autopilot's
  stage prompt) conveys option lines, those instructions supersede
  self-resolution — both read the same config so they coincide, except a
  detached driver's `--session-model` anchor may resolve different
  concrete aliases, and the conveyed concrete value is authoritative.
- **Risk:** honoring is prompt-driven (markdown skills), so drift is the
  failure mode; guarded by mirroring the in-session drive's shipped
  wording and by delta scenarios pinning each honored field.
