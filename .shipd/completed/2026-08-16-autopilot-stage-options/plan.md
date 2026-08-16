# autopilot-stage-options
Status: verified
Epic: named-pipelines

## Idea

Teach the epic autopilot to honor the typed per-stage pipeline options:
per-stage `autopilot.*` knobs replace the fixed three-strike, symbolic model
tiers resolve to concrete `--model` values for its headless sessions, and
build/review options are conveyed in its stage prompts.

### Motivation

The pipeline schema and presets (members 2-3 of `named-pipelines`) already
type and ship per-stage options — `autopilot.attempts`, `model`,
`subagent_model`, `validator`, `telemetry`, `disposition` — but the driver
ignores every one: `_three_strike` and `_run_gate` hardcode three attempts,
no `--model` is ever passed to a driven session, and `_stage_prompt` conveys
only `tools`. Until the driver honors them, `{"autonomous-pipeline": "eco"}`
cannot cut autopilot token spend at all.

### Details

- Stdlib model-tier authority in `spec_common.py`: `MODEL_LADDER`
  (`fable`, `opus`, `sonnet`, `haiku`) and pure
  `resolve_model_tier(tier, session_model=None)`.
- `autopilot.py`: per-stage attempts/timeout/max_resumes from each entry's
  `autopilot` block; resolved `--model` on driven sessions; option-conveying
  build/review prompts; option-rendering dry-run labels; a `--session-model`
  anchor flag surfaced in the dry run and the run report.
- `plugins/s/skills/autopilot/SKILL.md`: stage-instruction sync, in-session
  `model` via the Agent tool parameter, `autopilot.*` ignored in-session.

Affected capability: `epic-autopilot` (modified). Impact:
`plugins/s/skills/build/scripts/spec_common.py` and `autopilot.py`,
`plugins/s/skills/autopilot/SKILL.md`, tests under
`plugins/s/skills/build/tests/`, plugin version bump.

### Non-goals

- No interactive `/s:build`/`/s:plan` pipeline resolution — that is member 6
  (`interactive-pipeline`).
- No schema or preset changes (members 2-3) and no `review_gate.py` changes —
  member 4 already shipped `--disposition`, `--model`, and `autoreply`.
- No pydantic anywhere in the driver: it consumes resolved plain-dict entries
  only, and `tests/` keep passing without pydantic installed.
- No new registry stages, no concurrency or scheduling changes.

## Implementation

- **Tier authority in `spec_common.py`** (per Q1, oracle-settled):
  `MODEL_LADDER = ("fable", "opus", "sonnet", "haiku")` and
  `resolve_model_tier(tier, session_model=None)`: `session` returns the
  anchor (`None` means omit `--model`, inheriting the CLI default);
  `tier-below`/`tier-two-below` step 1/2 below the anchor's ladder index,
  clamped at the bottom; the anchor is `session_model` when it is a ladder
  alias, else the ladder top — fail-expensive, never fail-weak; any other
  non-empty string returns verbatim as a concrete id. Rejected: probing the
  CLI default model (untestable without a live session) and a fixed
  tier-to-alias map (breaks anchor-relative semantics).
- **Knob extraction**: `_stage_opts(entry, timeout, max_resumes)` returns
  `(attempts, timeout, max_resumes)` from `entry.get("autopilot")` with
  defaults `(3, run-global, run-global)`; applies to stage, custom, and
  replace entries alike.
- **Retry loops**: rename `_three_strike` to
  `_strike_loop(action, out, label, attempts=3, on_attempt=None)` (labels
  print `attempt N/attempts`); `_run_gate` gains `attempts=3`. The gate
  entry's attempts governs both the gate-engine retry loop and the
  enrichment-session loop — eco's `attempts: 1` yields one gate run and at
  most one enrichment session, restoring the single-enrichment doctrine.
  Enrichment sessions use the gate entry's timeout/max_resumes/model.
- **Session model plumbing**: `session_fn` gains keyword `model=None` (a
  resolved concrete value or None); the production seam builds per-call extra
  args (base plus `["--model", model]` when set). An entry's `model` resolves
  through `resolve_model_tier` with the run anchor; `subagent_model` resolves
  against the build session's own resolved model as anchor (falling back to
  the run anchor) and is conveyed in the prompt as the concrete alias with
  its symbolic provenance.
- **Prompt conveyance** (declared keys only — bare entries produce today's
  prompts unchanged): build adds one line per declared option — `validator`
  false (skip the adversarial validator phase), `telemetry` false,
  `parallelism` cap, `subagent_model` tier; review adds
  `--disposition <scope>` and `--model <tier>` to the poster command and
  matches the disposition-loop paragraph to the scope: `all` keeps today's
  text; `high-only` implements high-severity findings then runs
  `review_gate.py autoreply <pr> --disposition high-only` before `resolve`;
  `none` posts, then `autoreply --disposition none`, then `resolve`. The
  review grade is unchanged — autoreply keeps `resolve --check` reaching
  `unresolved=0`.
- **Anchor visibility** (oracle's caution): `--session-model` CLI flag
  (default None, meaning ladder-top anchoring); the dry run prints a
  `Model tier anchor:` line; the run report JSON gains `"tier_anchor"`.
- **Dry-run labels** render declared options (`gate [attempts 1]`,
  `build [validator off, subagent_model tier-two-below, telemetry off]`) so
  the in-session drive, which parses dry-run output, sees them.
- **SKILL.md sync**: the in-session stage instructions mirror
  `_stage_prompt` including the conditional option lines; a declared entry
  `model` maps to the Agent tool's `model` parameter resolved relative to the
  current session; `autopilot.*` blocks are ignored in-session — the human is
  the retry loop.
- **Runnable premises verified**: `claude --help` shows `--model <model>`
  accepting aliases (`fable`, `opus`, `sonnet`) or full names (observed);
  a declared pipeline without pydantic fails closed
  (`ConfigError: ... requires pydantic; pip install -r requirements.txt`,
  observed via a `resolve_pipeline` probe) — hence the driver never imports
  `pipeline_schema` and tests construct entry dicts directly.

Risks: prompt drift between `_stage_prompt` and the SKILL.md verbatim blocks
— guarded by updating both in one task group and by the prompt-content tests;
a wrong ladder-top assumption for non-fable defaults — guarded by
`--session-model` and the printed anchor line.

## Questions and answers

### Q1: How does the detached driver anchor symbolic tier resolution?
- **Question:** Symbolic tiers (`session`, `tier-below`, `tier-two-below`)
  resolve relative to the driving session, but the headless driver cannot see
  the user's CLI default model. Options: (a) stdlib `MODEL_LADDER` constant
  plus pure `resolve_model_tier(tier, session_model=None)` in
  `spec_common.py`, anchor defaulting to the ladder top with a
  `--session-model` override, steps clamped, concrete ids verbatim;
  (b) probe the actual default model at run start; (c) fixed mapping
  `tier-below` = `sonnet`, `tier-two-below` = `haiku`. Recommendation: (a).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option (a). The epic binds spawn-time resolution to one code
  authority with symbolic values that stay correct as generations ship; a
  fixed map hard-codes family names and breaks anchor-relative semantics;
  probing (b) makes tier resolution untestable without a live session. The
  top-default reproduces today's strongest-first doctrine and fails expensive
  rather than weak; surface the anchor in the dry run and report so it is
  visible, not implicit.
- **Cited:** epic/named-pipelines, verified/build-subagent-handoff,
  verified/epic-autopilot
