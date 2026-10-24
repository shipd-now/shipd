# risk-rubric-home
Status: verified
Planned-at: e2b3ec50a7c07b06618f7c4940ab5f6aaf9ceab2
Gated-hash: 05c437752465

## Idea

Rename the shared risk rubric to `risk-rubric.md`, move it into `/s:epic`'s references, and have `/s:epic` rate its stub table with it.

### Motivation

`/s:epic` writes each member's Code/Integration/Unknowns/Risk ratings from a one-line "honest estimate", while `/s:epic-grill` later re-scores those same axes from a rubric `/s:epic` never reads, so the two can disagree for the same member. The rubric also sits under `plan-deep/` with the generic name `rubric.md`, beside two other rubrics, so its name and home hide what it rates and who owns the ratings.

### Details

- Move `plugins/s/skills/plan-deep/references/rubric.md` to `plugins/s/skills/epic/references/risk-rubric.md`, and update its own self-description to name all three readers.
- Point every citer at the new path: the plan-deep and epic-grill skills and harness bodies, their two contract tests, and the verified requirements `plan-deep-rubric` and `epic-grill-risk-report`.
- `/s:epic` and its harness body load the rubric when writing the stub table's four rating cells.

Affected capabilities: `shipd-plan-deep` (modified), `shipd-epic-grill` (modified), `shipd-epic` (one added requirement). Impact: the files above plus `plugins/s/skills/epic/SKILL.md`, `plugins/s/harness/bodies/epic.md`, and the plugin version.

### Non-goals

- No change to the epic table: still six columns plus `After`, values `low`/`medium`/`high`, no Novelty or Overall column.
- No change to `/s:plan`'s depth gate or to autopilot's ordering.
- No change to the rubric's content beyond its self-description.

## Implementation

- **Home.** `skills/epic/references/` already holds `capture-rubric.md`, and the repo's pattern is that the skill owning a concept holds its shared reference (`document/references/question-brief.md`). `/s:epic` authors the ratings, so it owns the rubric. Rejected: a new plugin-wide references folder, which would be a new convention for one file; `harness/references/`, which holds harness fallback copies.
- **Name.** `risk-rubric.md` states what it rates and cannot be confused with the two `capture-rubric.md` files.
- **Move with `git mv`** so history follows the file. The old path must not remain.
- **How `/s:epic` uses it.** When writing the four rating cells, `/s:epic` rates each axis by the rubric's Axes table descriptors. It ignores Novelty, rabbit holes, coverage, and Overall, which belong to scoring a written plan. The SKILL.md stub-table bullet (`plugins/s/skills/epic/SKILL.md:426-427`) and the body line (`plugins/s/harness/bodies/epic.md:91-92`) replace "your honest per-change complexity estimate" wording with a rubric reference.
- **Verified specs.** The two existing requirements are MODIFIED to the new path; the epic rating rule is a new requirement `epic-risk-rubric-ratings` rather than a modification of the long `epic-interview-skill` requirement.

Risk: a missed citer leaves a dangling path. The contract tests assert the new path in every citer and that the old file is gone.

## Readiness attestation

### Problem and motivation

`/s:epic` rates the four axes without the rubric the grill scores them with, and the rubric's name and home hide its purpose.

Evidence:

- `plugins/s/skills/epic/SKILL.md:426-427` rates cells as "your honest per-change complexity estimate".
- `plugins/s/skills/epic-grill/SKILL.md:247` scores the same axes from the rubric.

### Scope and non-goals

A move, a rename, citer updates, and one new `/s:epic` rule; no table or engine change.

Evidence:

- In scope: the citers listed by `git grep -n "plan-deep/references/rubric"` (11 hits across plugins and verified specs).
- Out of scope: `plugins/s/skills/plan/SKILL.md` depth gate and `plugins/s/skills/build/scripts/autopilot.py`.

### Affected capabilities and files

Three capabilities and twelve files, because every citer moves to the new path and `/s:epic` gains the rubric.

Evidence:

- `shipd-plan-deep` requirement `plan-deep-rubric` (base 3b705d1e979b); `shipd-epic-grill` requirement `epic-grill-risk-report` (base aba011e42084), from `spec_status.py base-hash`; `shipd-epic` gains one requirement.
- Files: `plugins/s/skills/plan-deep/SKILL.md:30`, `plugins/s/harness/bodies/plan-deep.md:22`, `plugins/s/skills/epic-grill/SKILL.md:247`, `plugins/s/harness/bodies/epic-grill.md:82`, `plugins/s/skills/build/tests/test_plan_deep_skill_contract.py:15,28`, `plugins/s/skills/build/tests/test_epic_grill_contract.py:101`, `plugins/s/skills/epic/SKILL.md:426`, `plugins/s/harness/bodies/epic.md:91`, `plugins/s/.claude-plugin/plugin.json`.

### No open task-shaping decision

Every decision is settled.

Evidence:

- Home and name (`epic/references/risk-rubric.md`): the user approved the recommendation in conversation.
- Epic table unchanged and depth gate out of scope: the user's build request.
