# subagent-handoff
Status: verified

## Idea

Sub-agent handoffs work today but two pieces of the contract live only in the
orchestrator's head: build-specific context is improvised into spawn prompts ad
hoc, and verification has no independent adversary — the orchestrator both
coordinates the builders and grades their work. Reviewing an external "SDD
orchestrator directives" proposal surfaced two kernels worth adopting (and
several ideas our artifact set already covers better):

- **Codify the handoff contract.** The change artifacts are the compiled
  context — sub-agents read a fixed, named file set and never inherit
  conversation history or restated globals. The spawn prompt template gains an
  explicit, optional **Orchestrator addenda** slot for build-specific
  constraints (sequencing hazards, environment caveats) so that practice stops
  being improvised.
- **Adversarial validation.** Build Phase 5 gains an independent **validator
  sub-agent** (same tier as builders) that reads only the delta specs and the
  code and tries to *refute* each scenario; refutations must be resolved before
  the change can be stamped `verified`.
- **Lint-enforced task traceability.** Every task in `tasks.md` names the
  requirement(s) it satisfies via a `[req: ...]` tag, so the validator can map
  criteria to work items; `spec_lint.py` errors on missing or unresolvable
  tags.

Affected capabilities: `build-subagent-handoff` (new), `build-spec-lifecycle`
(modified: validator gate), `shipd-spec-format` (new: tag grammar), `shipd-spec-lint`
(new: tag enforcement), `shipd-plan` (modified: emission mandates tags). Impact:
`spec_lint.py` + its tests, build `SKILL.md`, `subagent-prompt.md`, new
`validator-prompt.md`, plan `emission.md`; plugin snapshot refresh afterwards.

### Non-goals

- Adopting the six-element sub-spec block verbatim — a second handoff format
  that would drift from the artifacts it duplicates.
- Per-task orchestrator-compiled context blocks — duplicates the spec into
  prompts; the artifacts stay the compiled context.
- Retrofitting `[req: ...]` tags onto archived changes — they are immutable.

## Implementation

- **Tag grammar (binding):** a task carries one bracket tag
  `[req: <id>[, <id>...]]` or the wildcard `[req: *]` (whole-change tasks such
  as verify barriers). Ids must resolve against the requirement ids present in
  the change's own delta specs (any operation, any capability); `*` must appear
  alone. The tag sits in the task text after the optional `[P<n>]` group tag;
  the claim script's `\[P[0-9]+\]` regex cannot match it, so coordination is
  untouched. Rejected: lint against master ids too — a change's tasks implement
  its own deltas, nothing else.
- **Lint rule (error, not warning):** every checkbox task in `tasks.md` must
  carry exactly one well-formed `[req: ...]` tag whose ids all resolve;
  enforcement is per-task with one error per violation. Stdlib-only, tests ride
  along (constitution), and the failing tests land before the implementation
  (test-first mandate).
- **Validator contract:** spawned in Phase 5 after the task list is done and
  the suite is green, before `set-status verified`. Same tier as builders.
  Inputs: the change name and instructions to read the delta specs, relevant
  masters, and the code — explicitly not the builders' summaries or the
  orchestrator's history (clean context). Posture: for each `#### Scenario:`,
  attempt to refute it by exercising the real behavior; output one
  verdict per scenario (`confirmed` or `refuted` + evidence). Any refutation
  returns the build to the fix loop; `verified` is only stamped on a fully
  confirmed report. Prompt template lives at
  `references/validator-prompt.md`.
- **Handoff rules codified in Phase 3:** sub-agents start with clean contexts
  (no conversational history, no planning transcript); context arrives via the
  artifact set the template already names; globals (`CLAUDE.md`/`AGENTS.md`,
  `am/constitution.md`) are inherited/read, never restated; build-specific
  hazards go in the template's new **Orchestrator addenda** slot. Rejected: the
  strong isolation form that hides decision rationale — `## Implementation`
  rationale prevents executors re-litigating decisions.
- **Self-hosting:** this change's own `tasks.md` carries `[req: ...]` tags so
  the Phase 5 re-lint (running the new rule) passes on the change that
  introduced it. Risk: existing in-flight changes authored without tags would
  fail the new lint — acceptable; `am/planned/` is empty apart from this
  change.
