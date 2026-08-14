# lean-spec-format
Status: verified

## Idea

### Why

The change artifact set we emit today (`proposal.md` + `design.md` + `tasks.md`
+ delta specs) is a near-verbatim clone of OpenSpec's layout — which was never
the intention of the homegrown engine. The SDD research synthesis ("Strategic
Architecture of Lean Specification-Driven Development") points at a leaner
shape: aggressive context economy (LeanSpec's ~2,000-token budget), a single
decision-driving document instead of ceremony spread across files, EARS-shaped
normative statements for deterministic parsing, and a constitution-style global
steering layer (Spec Kit). This change cuts the format over to that lean shape
while keeping the two parts the research explicitly endorses: the delta-spec
architecture (exact-keyed, LLM-free merge) and the executor-mutated `tasks.md`
checklist.

### What Changes

- Collapse `proposal.md` + `design.md` into a single **`plan.md`** per change:
  the `# <change>` title and `Status:` header, a `## Idea` section (the former
  proposal: why, what, capabilities, impact) and an `## Implementation` section
  (the former design: binding decisions, risks).
- `tasks.md` stays a separate file — executors flip its checkboxes during
  build, and `spec_status.py`/the statusline parse it; that churn stays out of
  `plan.md`.
- Delta specs under `specs/<capability>/spec.md` are unchanged; the merge
  engine (`spec_merge.py`) is untouched.
- Point every consumer of `proposal.md`/`design.md` at `plan.md`:
  `spec_lint.py` (header check becomes a plan-header + required-sections
  check), `spec_status.py` (status read/write), `statusline.sh`, the plan
  skill's emission guide, the build skill and teammate prompt, tests and
  fixtures, and the README trees.
- Add a **context-economy lint warning**: `spec_lint.py` warns (never errors)
  when `plan.md` or a delta spec exceeds a ~2,000-token budget, nudging
  decomposition instead of monolith documents.
- Document the five **EARS patterns** (Ubiquitous / When / While / If-Then /
  Where) in `am/spec/README.md` and the emission guide as the recommended
  shape for SHALL/MUST statements — guidance only, the linter still enforces
  just SHALL/MUST.
- Add **`am/spec/constitution.md`** — a Spec Kit-style global steering document
  with this repo's non-negotiable engineering rules (stdlib-only Python
  engine, POSIX-ish statusline shell, tests beside the engine, plugin-snapshot
  refresh discipline). The plan and build flows load it as binding constraints
  when present.

### Capabilities

#### Modified Capabilities

- `shipd-spec-format` — per-change artifact set becomes `plan.md` + `tasks.md` +
  deltas; new requirements for the plan document sections, EARS guidance, and
  the constitution document.
- `shipd-spec-lint` — the proposal-header check becomes a plan-header +
  required-sections check; new context-economy warning requirement.
- `spec-status` — the status header lives in `plan.md`; CLI wording follows.
- `shipd-plan` — emission produces the lean artifact set; status header
  requirement points at `plan.md`.

### Impact

- Engine scripts: `plugins/s/skills/build/scripts/spec_lint.py`,
  `spec_status.py` (path + header logic); `spec_merge.py` untouched.
- Integration: `plugins/s/integrations/statusline.sh` reads `plan.md`.
- Skills: `plugins/s/skills/plan/references/emission.md` (rewrite),
  `plugins/s/skills/plan/SKILL.md`, `plugins/s/skills/build/SKILL.md`,
  `plugins/s/skills/build/references/teammate-prompt.md`.
- Tests + fixtures: `test_spec_lint.py`, `test_spec_status.py`,
  `test_statusline.py`, and the `fixtures/sample` change directory.
- Docs: `am/spec/README.md` (format authority), root `README.md` tree; new
  `am/spec/constitution.md`.
- Transitional: this change's own directory is authored in the old format and
  must be converted to `plan.md` as a late task, before its status can pass
  the post-cutover lint. Archived changes are immutable and are not converted.

## Implementation

### Context

The engine's change layout was inherited from OpenSpec during bootstrap:
`proposal.md` (why/what, carries `Status:`), `design.md` (decisions),
`tasks.md`, and per-capability delta specs. The SDD research synthesis
recommends leaner artifacts: LeanSpec's context economy (~2,000 tokens per
document, signal-to-noise maximization), EARS notation for normative
statements, Spec Kit's constitution as a global steering layer — while
validating exactly the two mechanisms our engine is built on: OpenSpec's
delta architecture and checklist-driven executor state.

Only `spec_lint.py`, `spec_status.py`, and `statusline.sh` know the artifact
filenames; `spec_merge.py` reads only `specs/` deltas and archives the change
directory wholesale, so the merge engine is unaffected by the cutover.

### Goals / Non-Goals

**Goals**

- One `plan.md` per change holding the former proposal ("Idea") and design
  ("Implementation") content, with the status header.
- Keep `tasks.md` and the delta-spec grammar exactly as they are.
- Surface the research's low-cost wins: EARS guidance, a size warning, and a
  constitution document.

**Non-Goals**

- No change to the delta grammar, merge semantics, base-hash concurrency
  check, or archive layout.
- No conversion of archived changes (they are immutable by design).
- No lint *enforcement* of EARS phrasing or hard size caps.
- No new statuses or transition-guard changes.

### Decisions

**D1 — plan.md shape and lint contract.** `plan.md` line 1 is `# <change>`
(matching the directory slug), the first non-blank line after it is
`Status: <status>`, and the body contains at least the two level-2 sections
`## Idea` and `## Implementation`, in that order. Extra sections are allowed.
Lint errors on: missing file, wrong title, missing/invalid status, or a
missing required section. Rationale: the sections are the whole point of the
merge; enforcing them keeps future emissions honest. Alternative rejected:
leaving sections unenforced — drift back to freeform documents is exactly the
failure mode this change fixes.

**D2 — tasks.md stays separate.** Executors physically flip checkboxes during
build; `spec_status.py sync`, the transition guards, and `statusline.sh` all
parse those checkboxes. Folding tasks into `plan.md` would have every executor
rewriting the plan document mid-build and would touch three parsers for zero
research-supported benefit (the research's own five-document suite keeps tasks
separate for exactly this state-management reason).

**D3 — requirement ids stay stable.** The modified requirements keep their
existing `id:` slugs (e.g. `proposal-header-validation`) with updated titles
and content, rather than pairing RENAMED + MODIFIED operations on the same
requirement in one delta. Titles are free to change; ids are the merge key,
and mixing a re-key with a content replace in one delta depends on merge-order
subtleties we don't need to take on.

**D4 — EARS is guidance, not grammar.** `am/spec/README.md` gains an EARS
section (the five patterns with one-line templates) and the emission guide
recommends them for SHALL/MUST statements. The linter continues to require
only a SHALL/MUST token. Rationale: EARS's value is in authoring discipline;
lint-enforcing sentence templates with regexes would produce false rejections
and fossilize phrasing.

**D5 — context-economy warning, chars/4 heuristic.** `spec_lint.py` warns to
stderr (`WARNING: ...`, exit code unaffected) when `plan.md` or any single
delta spec exceeds the budget of 2,000 tokens, approximated stdlib-only as
`len(text) / 4 > 2000` (≈8,000 characters). Warning not error: an oversized
plan is a smell, not structural invalidity, and a hard cap would block
legitimately large cutovers (this change's own plan is near the line).

**D6 — constitution.md is optional and loaded, not linted.** The file lives at
`am/spec/constitution.md`. When present, the plan flow reads it during
investigation and the build flow includes it in the Phase 0 context gate and
the teammate prompt; its rules are binding constraints on designs and
implementations. Lint ignores it entirely (absence is fine — other repos
adopting the plugin may not have one). Seed content for this repo: stdlib-only
Python for engine scripts, POSIX-compatible `statusline.sh`, tests in
`plugins/s/skills/build/tests/` covering every engine change, and the
plugin-cache snapshot refresh rule from AGENTS.md.

**D7 — self-migration ordering.** This change is authored in the old format
(today's lint requires `proposal.md`). The task list flips the engine first,
then converts this change's own directory (`proposal.md` + `design.md` →
`plan.md`) *before* any status transition, because post-cutover lint — which
gates `set-status complete/verified` — will demand `plan.md`.

### Risks / Trade-offs

- **Stale snapshot risk:** skills run from the plugin cache; after the build,
  `claude plugin update s@shipd` is required or `/s:plan` keeps emitting
  the old ceremony. Mitigated by an explicit final task.
- **Requirement ids no longer match filenames** (`proposal-header-validation`
  validates `plan.md`). Accepted per D3; the title says what it does.
- **chars/4 is a rough token estimate.** Fine for a warning threshold; it will
  never fail a build.
