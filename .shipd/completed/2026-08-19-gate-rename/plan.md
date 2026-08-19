# gate-rename

Status: verified

## Idea

Rename the `/s:copilot` skill to `/s:gate`, moving its skill directory, body
template, registration listings, and capability spec to the provider-neutral
name while leaving the Copilot integration's own naming untouched.

### Motivation

The skill's job is setting up the semantic-review merge gate; naming it after
GitHub Copilot ties the user-facing handle to one review backend, and the
user wants the neutral name so other reviewing harnesses can sit behind the
same gate later.

### Details

- `plugins/s/skills/copilot/` → `plugins/s/skills/gate/` (frontmatter
  `name: gate`, `/s:gate` trigger phrases) and
  `plugins/s/harness/bodies/copilot.md` → `bodies/gate.md` — the
  bodies/skills id-set equality test forces the pair to move together.
- `README.md` skills-table row, `AGENTS.md` enumeration, and
  `docs/copilot-review.md` guided-path mentions → `/s:gate`.
- Capability move: `shipd-copilot`'s two requirements are REMOVED and
  continue as `gate-skill-flow` / `gate-skill-registration` in the new
  `shipd-gate` capability, text identical apart from the renamed paths and
  trigger.

Affected capabilities: `shipd-gate` (added), `shipd-copilot` (removed).
Impact: the six files above plus
`plugins/s/.claude-plugin/plugin.json` (version bump).

### Non-goals

- No rename of the Copilot integration itself: `shipd copilot add`, the
  `copilot-*.yml` workflow templates, `COPILOT_GITHUB_TOKEN`,
  `.github/skills/code-review/`, and `docs/copilot-review.md`'s filename all
  keep their names — they accurately describe the GitHub Copilot backend.
- No behavior change to the skill flow — the SKILL.md and body content change
  only where they name the skill itself.
- No touch of the `github-copilot` harness dialect in `harness_registry.py`
  (a target harness, unrelated to this skill).

## Implementation

- **Rename via `git mv`** so history follows the files.
- **Only self-naming text changes.** Inside `skills/gate/SKILL.md` and
  `bodies/gate.md`, replace the skill's own name, title, and trigger phrases
  (`/s:copilot` → `/s:gate`, `name: copilot` → `name: gate`, description
  trigger list updated to "set up the gate", "install the review gate",
  "block PRs on review", "/s:gate"); every mention of `shipd copilot add`,
  Copilot CLI, Copilot code review, and `COPILOT_GITHUB_TOKEN` stays, because
  those name the backend, not the skill.
- **Capability move over in-place edit.** REMOVED (with Reason/Migration and
  the current base hashes) + ADDED under the new ids, rather than keeping the
  requirements in a capability whose name no longer matches the skill.
  Rejected: renaming ids inside `shipd-copilot` — the capability directory
  name itself is the misnomer.
- **Post-merge shell cleanup (build orchestrator step, not a task).**
  `spec_merge.py` always writes an affected master back
  (`merge_change`, spec_merge.py:207-233), so after the Phase 6 merge the
  emptied `.shipd/verified/shipd-copilot/spec.md` survives as a
  preamble-only file. The build removes the
  `.shipd/verified/shipd-copilot/` directory immediately after running the
  merge engine and before committing, in the same commit — the engine
  performed the requirement-level removal; this deletes only the empty
  shell. This cannot be a `tasks.md` task because tasks run before the
  merge phase.
- **Version bump.** `plugins/s/.claude-plugin/plugin.json` bumps to the next
  patch above the version current at ship time (0.6.145 if main is still at
  0.6.144), same PR.

Risk: a stale `/s:copilot` reference surviving somewhere user-facing.
Guarded by a final repo-wide grep task asserting the only remaining
`/s:copilot` occurrences are in immutable archives
(`.shipd/completed/`) and this change's own REMOVED delta.
