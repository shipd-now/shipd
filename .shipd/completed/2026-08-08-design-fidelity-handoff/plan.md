# design-fidelity-handoff
Status: verified
Theme: developer-experience

## Idea

Preserve design intent through spec-driven execution by parking the design in a
global scratch area that sub-agents and the validator read verbatim, and by
encoding design conformance as validator-refutable scenarios.

### Motivation

`/s:build` compiles context into the artifacts, so a design captured only as
prose in `plan.md` drifts — sub-agents rebuild from the summary, not the design.
The design belongs to the consuming project, so it must not be committed to that
repo's PR.

### Details

- Add a stdlib `design.py` engine verb: `path <change>` resolves and creates the
  global scratch dir `~/.shipd/designs/<change>/`; `clean <change>` removes it,
  fail-soft. The design lives here, never in the consuming repo or its PR.
- Sub-agents and the validator read the plan-named design dir verbatim when
  `plan.md`'s `## Implementation` names one (consume-if-present — absent leaves
  every existing behavior unchanged).
- `/s:plan` authors design conformance as `#### Scenario:` blocks the validator
  refutes against the design (option 3).
- Build deletes the scratch dir at finish (Phase 7), fail-soft.

Affected capabilities: `design-handoff` (added), `build-subagent-handoff`
(modified), `build-spec-lifecycle` (modified). Impact:
`plugins/s/skills/build/scripts/design.py` (new) + its test,
`plugins/s/agents/sub-agent.md`, `plugins/s/agents/validator.md`,
`plugins/s/skills/plan/references/emission.md`,
`plugins/s/skills/build/SKILL.md`, plugin version bump. Stdlib only; no new
dependency.

### Non-goals

- No active "capture the design" prompt in `/s:plan`/`/s:build` — it consumes a
  design only if one was parked in the scratch dir (presence-based).
- No repo-scoped scratch path — the flat `~/.shipd/designs/<change>/` matches the
  flat `~/.shipd/builds/` layout; cross-project same-named collisions are out of
  scope (cleaned at finish).
- No committing the design into the consuming project or its PR.
- No image-diff tooling — fidelity is asserted by validator-exercised scenarios,
  not automated pixel comparison.

## Implementation

- **Scratch root resolution.** `design.py` resolves the designs root exactly like
  `build_report.py::build_log_dir` resolves the build log dir: read the layered
  config's `build.design_dir`, default `~/.shipd/designs`, home-expanded; the
  per-change dir is `<designs-root>/<change>`. Rejected: writing under the
  repo-local content dir (`.shipd/`) — that would risk committing the design; the
  global home keeps it out of the consuming repo, matching `~/.shipd/builds`.
- **`design.py` verbs.** `path <change>` prints the absolute per-change dir and
  `os.makedirs(..., exist_ok=True)` it (so a design session can drop files in);
  `clean <change>` `shutil.rmtree`s it and is **fail-soft** — a missing dir or a
  removal error warns on stderr and still exits `0`, mirroring `heartbeat.py`, so
  cleanup never blocks a build. Stdlib only (`argparse`, `os`, `shutil`,
  `spec_common` for config), like the sibling scripts.
- **Handoff stays clean-context.** The design path travels *inside* `plan.md`'s
  `## Implementation`, not as extra spawn-message content — so the
  "artifacts are the compiled context" contract holds. The sub-agent reads the
  named dir as a **read-only** reference and matches it; it never edits it and it
  sits outside the worktree, the one documented exception to the
  paths-inside-the-worktree rule.
- **Validator input.** The validator additionally reads the plan-named design dir
  so it can exercise and refute design-fidelity `#### Scenario:` blocks against
  the real design. Its clean-context isolation from builders/conversation is
  unchanged.
- **Contract tests.** The agent-definition edits are guarded by contract tests in
  the stdlib suite (extending `tests/test_subagent_contract.py`), matching how
  the workspace-gate clause is already asserted, so a contract regression fails
  CI without `textual`.
- **Version bump.** Editing `plugins/s/` requires bumping
  `plugins/s/.claude-plugin/plugin.json`, or the versioned plugin cache keeps
  running stale skills.

Risk: a stale design left in `~/.shipd/designs/` if a build is abandoned before
Phase 7. Guard: `clean` is idempotent and fail-soft, so a later build (or a
manual `design.py clean`) clears it; the flat, change-named layout makes a stray
dir easy to spot.
