# autopilot-ask-mikk
Status: verified
Epic: mikk-knowledge

## Idea

Give the epic autopilot the ask-mikk rung: one oracle-backed enrichment
session before a gate-rejection park, plus oracle-aware guidance in the
canned resume reply and in the build prompt's `QUESTION:` routing.

### Motivation

The autopilot parks a member as `rejected` on the first context-gate rejection
and resumes every stalled session with a bare self-recommendation reply, even
when the workspace wiki already holds mikk's standing answer. The oracle read
path shipped in `ask-mikk-oracle`, but no autopilot surface consults it, so
unattended runs escalate to a human more often than the epic intends.

### Details

- On gate exit 2, `drive_member` drives **one** headless enrichment session —
  `/s:plan <member>` enrichment mode, instructed to consult the `s:oracle`
  agent for gaps the repository cannot answer — then re-runs the gate; a pass
  continues the pipeline, anything else parks the member as `rejected`.
- `rejected` results and report entries now carry the enrichment session id,
  and the run summary prints a `claude --resume` pointer for them.
- `GOAHEAD_REPLY` gains the oracle rung: shape undecided points into compact
  questions for `s:oracle`, adopt `ANSWER`, self-recommend on `INSUFFICIENT`.
- The build stage prompt routes sub-agent `QUESTION:` escalations the
  artifacts and code cannot answer through the oracle before the coordinator
  answers on its own authority.
- `/s:deliver`'s report relay reflects the attempted enrichment and prints
  the rejected members' resume pointers.
- Plugin version bumps 0.6.9 → 0.6.10.

Affected capabilities: `epic-autopilot` (modified). Impact:
`plugins/s/skills/build/scripts/autopilot.py`,
`plugins/s/skills/build/tests/test_autopilot.py`,
`plugins/s/skills/deliver/SKILL.md`,
`plugins/s/.claude-plugin/plugin.json`. The oracle contract (`shipd-ask`) is
consumed, not modified; `session_driver.py` and `dashboard.py` are untouched.

### Non-goals

- No changes to the oracle agent, `/s:ask`, the wiki store, or any engine
  verb — the oracle contract is consumed as shipped.
- No plan-skill changes: the readiness-gap rung is the `plan-ask-mikk`
  member; this change relies only on `/s:plan`'s existing enrichment mode.
- No retry loop: exactly one enrichment attempt per member per run, and a
  `rejected` member is still never re-driven by a later run.
- No new report outcome class — enrichment failure still parks as `rejected`,
  keeping `/s:deliver`'s recovery pointers valid.

## Implementation

- **Enrichment is a driven `/s:plan` session plus a deterministic re-gate,
  not autopilot-side artifact patching.** `autopilot.py` is deterministic
  stdlib Python and must never edit spec artifacts; `/s:plan`'s enrichment
  mode already owns locate → in-place edit → re-gate. After the session the
  autopilot re-runs `gate_fn` itself so the gate engine, not the session's
  claim, decides. Rejected alternative: spawning `s:oracle` from the driver
  and patching artifacts — there is no model in the driver to do either.
- **Gate-branch flow in `drive_member`.** Verdict `rejected` → heartbeat
  `stage_started(slug, "enrich", 1)` → one `session_fn("enrich", slug, cwd,
  <enrich prompt>, timeout, max_resumes)` call (no `_three_strike`) → on
  session ok, `_run_gate` again: `pass` continues the pipeline; `rejected`
  parks `MemberResult(outcome="rejected", stage="gate", reason="context
  insufficient after oracle enrichment", session_id=<enrich sid>)`; `failed`
  keeps today's `_park("gate", reason)` needs-human semantics. On session
  failure or unmet grade: if the worktree vanished, resolve via
  `_resolve_vanished`; else park `rejected` with reason
  `"context insufficient (gate exit 2); oracle enrichment failed: <failure>"`
  and the session id. Exactly one enrichment attempt per member per run.
- **Grade.** `_make_session_fn` maps stage `"enrich"` to `_plan_grade`
  (member at `ready`, lint-clean) — the same terminal state the re-gate
  requires, so the resume loop stops once the session has re-gated clean.
- **Enrichment prompt** (new `"enrich"` branch in `_stage_prompt`): run
  `/s:plan <member>` (locates the rejected change, enters enrichment mode);
  resolve repository-answerable findings by editing the artifacts; for gaps
  the repository genuinely cannot answer, consult the ask-mikk oracle — spawn
  agent `s:oracle` with one compact question (the decision, the options,
  your recommendation) per gap — never a human, the session is unattended;
  fold `ANSWER` verdicts in, adopt your own recommendation on
  `INSUFFICIENT`; exit through the re-gate so the change returns to `ready`.
- **`GOAHEAD_REPLY` (binding text).** "Proceed. For any undecided point or
  decision, now or in later rounds: shape it into a compact question (the
  decision, the options, your recommendation) and consult the ask-mikk
  oracle by spawning agent `s:oracle` with that question and this repo's
  root; adopt its ANSWER, and on INSUFFICIENT — or if the oracle is
  unavailable — take the option you yourself recommend. Never wait for a
  human. Complete the work through to its terminal state."
- **Build prompt addendum (binding).** Appended to the build stage base
  prompt: "If a sub-agent escalates a QUESTION: that the spec artifacts and
  code cannot answer, consult the ask-mikk oracle (spawn agent `s:oracle`
  with a compact question) before answering on your own authority; on
  INSUFFICIENT, answer with your own recommendation — never leave the
  sub-agent blocked."
- **Report shape.** `report["rejected"]` entries gain a `"session_id"` key
  (`None` when no id was captured); `_summarize` appends
  `-> claude --resume <id>` to a rejected line when the id is present. The
  key is additive, so existing report consumers keep working.
- **Deliver skill wording.** Phase 3's park sentence notes the single
  oracle-backed enrichment attempt between rejection and park; Phase 4's
  rejected bullet notes that the automatic enrichment already failed, keeps
  `/s:plan <member>` as the manual recovery entry point, and prints the
  resume command when the report carries an enrichment session id.
- **Risks.** A session could force `ready` without the gate — guarded: the
  autopilot re-runs the gate itself and only its exit decides (a `ready`
  plan stays `ready` on pass; exit 2 re-parks). Enrichment loops are
  impossible: one attempt per run, and `rejected` members are never
  re-driven. Heartbeat needs no change — `stage_started` accepts any label,
  so `enrich` appears on the live board as-is.
