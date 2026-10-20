# gate-update-room-set
Status: ready
Planned-at: 73156d3ce5cd7c38ac953d31cd0771c4a89ffd93
Gated-hash: fd5c615ec6eb

## Idea

`/s:gate update` also refreshes the PR-room wake set when the repository already has it installed, in the same commit as the gate files.

### Motivation

A repository that installed the room wake set keeps running an old wake workflow and an old bundled room runtime after `/s:gate update`, so its maintainer has to know to run a second `shipd copilot add --room` (seen twice on unkannybanny). The update flow claims to bring the repository to the running plugin version, and today it does that for only half of what shipd installed.

### Details

- **New engine action.** `shipd copilot update` refreshes the four gate files exactly as `add` does, and also refreshes the room wake set when its "room-wake.yml" carries the shipd-copilot ownership marker. A wake set that is absent, or whose workflow is not shipd-owned, is left untouched and named on a report line.
- **Skill.** The `update` flow of `plugins/s/skills/gate/SKILL.md` reads both sets from the bare report, runs `shipd copilot update` instead of `add`, and commits exactly the paths the verb printed on its "wrote" lines.
- **Docs and version.** `docs/room-wake-reference.md` and `docs/copilot-review.md` describe the new action and the update flow's reach; the plugin version moves up one patch.

Affected capabilities: `shipd-cli` (one added requirement, `copilot-update`) and `shipd-gate` (`gate-update-flow` modified). Impact: `plugins/s/bin/shipd`, `plugins/s/skills/build/tests/test_copilot_verb.py`, `plugins/s/skills/gate/SKILL.md`, the two docs, `plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- `shipd copilot add` and `add --room` keep their exact behaviour; fresh install of either set is unchanged.
- `update` never installs the room wake set fresh, and never overwrites a wake workflow shipd does not own.
- No change to `shipd doctor`, the templates, or the setup flow of `/s:gate`.

## Implementation

- **The logic lives in the engine, the skill calls it.** A new `update` choice on the `copilot` verb's `action` argument in `plugins/s/bin/shipd`. Rationale: the "is the room set installed" decision is then made from the same `room_wake_states` the bare report prints, and it is tested offline. Rejected: teaching the skill to read the room lines and run `add --room` itself, which leaves the decision untested and re-derives state from text in prose. Rejected: making plain `add` also refresh an installed room set, which changes `add`'s documented contract (requirement `copilot-room-wake` says plain `add` leaves the wake set untouched) and its tested behaviour.
- **Detection rule.** The room set counts as installed exactly when `room_wake_states(root, version)` reports the workflow ("room-wake.yml") as `installed` or `stale`, which happens only when it carries the marker. With a marked workflow no runtime file can be `foreign` (ownership follows the workflow), so the refresh never needs `--force`. Workflow `absent`: print "room wake set: not installed — left as is". Workflow `foreign`: print "room wake set: room-wake.yml is not shipd-owned — left as is". Neither case is an error, and neither changes the exit code.
- **Foreign gate files.** `update` applies `add`'s rule to the four gate files: a foreign one refuses with exit `1` naming it and writes nothing (room set included), unless `--force` is given. `--force` never extends to the room set.
- **`--room` with `update`** is a usage error: `parser.error("update refreshes every installed set; --room does not apply")`, exit `2`, nothing written.
- **All payloads first.** Refactor `_copilot_add` and `_room_add` into builders `_copilot_payloads(version)` and `_room_payloads(version)` that return `[(relative, data, mode)]` and raise `OSError`/`ValueError`, plus `_write_payloads(root, payloads)` that writes atomically and prints `wrote <relative>` per file. `_copilot_add` and `_room_add` keep their output and exit codes exactly by calling these. `_copilot_update(root, version, room_states)` builds the gate payloads plus, when the room set is installed, the room payloads, before writing anything; a read failure writes nothing and exits `1`.
- **Output.** `update` prints the `wrote` lines for every file written (gate files first, then the wake set), then the room line when the set was skipped, then the same closing note `add` prints. The bare report's hint line gains "`shipd copilot update` refreshes the gate files and an installed room wake set."; the usage banner line becomes `copilot [add|update|remove]`.
- **Skill flow.** In `## Update — refresh an installed gate`: "already current" means all four gate files `installed` and the room wake set either all `installed` or not shipd-installed (its "room-wake.yml" `absent` or `foreign`). A `foreign` gate file still refuses. A foreign or absent wake set is reported, never refused. The refresh command becomes `<shipd> copilot update`, and the commit stages exactly the paths the verb printed on `wrote` lines (`git add` of those paths), so the room files ride the same commit, push, and fallback pull request. The `## Arguments` bullet and the front-matter description name the wake set.
- **Tests** in a new `CopilotUpdateVerbTest(CopilotVerbCase)` class in `plugins/s/skills/build/tests/test_copilot_verb.py`, reusing the room constants already there.

Risk: a user who hand-edited the bundled runtime loses the edit on update. That is the existing `add --room` contract for owned files, and the docs already say to edit the plugin, not the installed copies.

## Readiness attestation

### Problem and motivation

`/s:gate update` refreshes only the four gate files, so an installed room wake set stays on its old version.

Evidence:

- `plugins/s/skills/gate/SKILL.md` update flow runs `<shipd> copilot add` and stages only the gate paths.
- `plugins/s/bin/shipd` `cmd_copilot`: without `--room`, `add` dispatches to `_copilot_add` alone.
- Requirement `copilot-room-wake` (shipd-cli): plain `add` leaves the wake set untouched.

### Scope and non-goals

The engine verb gains one action; the skill's update flow, two docs, and the version change. `add`, `add --room`, `remove`, and setup stay as they are.

Evidence:

- In scope: `cmd_copilot`, `_copilot_add`, `_room_add`, `_copilot_report` in `plugins/s/bin/shipd`.
- Out of scope: `plugins/s/integrations/copilot/` templates, `shipd doctor` checks.

### Affected capabilities and files

Two capabilities and six files are affected.

Evidence:

- Capability `shipd-gate`: requirement `gate-update-flow` (base c814818dc501, from `spec_status.py base-hash`).
- Capability `shipd-cli`: new requirement `copilot-update`.
- Runnable premise: `python3 plugins/s/bin/shipd copilot --root /tmp/nonexist-xyz` exited 0 and printed the four gate lines, then "room wake set:" and six `absent` lines, so the bare report already carries both sets for the skill to read.

### No open task-shaping decision

Every decision is settled in Implementation under the user's pre-approved recommended defaults; none remain.

Evidence:

- Engine verb over skill-only logic, and a new action over changing `add`: settled above.
- Detection by the workflow marker, skip-not-refuse for an absent or foreign wake set: settled above.
