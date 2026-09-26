# parallel-member-drive
Status: verified

## Idea

Let the in-session epic autopilot drive independent members in parallel waves computed by the engine, instead of one member at a time.

### Motivation

An epic with several ready, independent members still ships one member at a time under `/s:autopilot`, so its delivery time scales with its member count and the user ends up building independent members side by side by hand, as happened with two changes this session. The drive already gives each member its own worktree, branch, PR, and heartbeat, so nothing but the serial loop keeps them apart.

### Details

- A `--waves` mode on the autopilot driver computes, from disk alone, the waves the in-session drive may run together: plan waves over unplanned members, then build waves over ready members whose planned delta capabilities are pairwise disjoint, each wave capped at `--parallel N` (default 3).
- The in-session drive runs one wave at a time: it spawns the current entry's sub-agent for every member of the wave together, grades each from disk, advances each passing member, re-runs `--waves` when the wave is done, and stops before the next wave when a grade fails.
- The run-controls confirmation gains `--parallel N` and shows the computed waves; `--parallel 1` is today's serial walk.
- The detached driver keeps its serial loop.

Affected capabilities: `epic-autopilot` (modified). Impact: `plugins/s/skills/build/scripts/autopilot.py`, `plugins/s/skills/build/tests/test_autopilot.py`, `plugins/s/skills/autopilot/SKILL.md`, `plugins/s/harness/bodies/autopilot.md`, `plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No concurrency in the detached `claude -p` driver; `run` and `--member` stay serial and `member-selection-and-order` is unchanged.
- No dependency column or other change to the epic's `## Changes` table grammar.
- No new pipeline configuration key; the cap is a per-run control, and `autopilot` blocks stay ignored in-session.
- No change to the build skill, to the `[P<n>]` task fan-out inside one build, or to the delivery board.
- No detection of repo-specific shared files outside the spec library, such as a plugin version line; a conflict there surfaces through the build's reconcile step as a stop-and-ask.

## Implementation

- **Wave computation lives in `autopilot.py`, beside member selection.** Add `member_capabilities(root, slug)`: call `ss._member_state_with_root(root, slug)`; when the state is not `ready` return `[]`; else list the sorted names of directories under `<sc.specs_dir(hosting_root)>/planned/<slug>/specs/` that contain a `spec.md`. Add `compute_waves(root, epic, parallel)` returning `{"epic", "parallel", "waves", "skipped"}`: `parse_members` then `select_and_order`; plan waves chunk `to_drive` into slices of `parallel`, each `{"index", "stage": "plan", "members": [{"slug", "risk", "capabilities": []}]}`; build waves walk the `ready` members from `skipped` sorted by `(RISK_RANK, order)` and place each in the first build wave whose union of capabilities is disjoint from the member's and whose member count is below `parallel`, else append a new wave; `skipped` lists every member whose state is neither `unplanned` nor `ready`. Indexes run from 1 across plan then build waves. Rejected: a separate `spec_status.py epic-waves` verb, because member parsing, risk ranking, and the dry run already live in the driver.
- **CLI surface.** In `main`, add `--waves` (store_true), `--parallel` (int, default 3, `parser.error` below 1), and `--json` (store_true, meaningful only with `--waves`). When `--waves` is set, call `compute_waves` and render: with `--json`, `json.dumps` the dict on one line; without, print `Waves for epic '<epic>' (cap <N>):` then one line per wave `  wave <i> [<stage>]: <slug> (<caps or risk>)…`, then `  skipped: <member> (<state>)` per skipped member. Drive nothing, write no heartbeat, exit 0. `--waves` with `--dry-run` or `--member` is a `parser.error`.
- **Skill: waves replace the serial member loop.** In `plugins/s/skills/autopilot/SKILL.md`: Phase 2 adds a `--parallel N` control (default 3; 1 = serial) and runs `autopilot.py <epic> --waves --parallel N` so the confirmation shows the waves. The in-session "Member order and pipeline" section obtains grouping and order from `autopilot.py <epic> --waves --parallel N --json` instead of parsing the dry run's two sections; the dry run stays the detached mode's preview only. A new "Running a wave" subsection states the loop: for the first wave returned, run per-member setup for every member, spawn the current entry's sub-agent for each member together in the background (or run its command entry via Bash), wait for all, grade each from disk, advance passing members to their next entry, repeat until the wave's members have all finished their walk, then re-run `--waves` and continue with its first wave until none is returned. The failure contract says a failed grade lets the wave's in-flight sub-agents end, starts no further entry or wave, and reports every stopped member in one message. The sentence stating members run one at a time is removed. The run summary reports members per wave.
- **Harness body.** `plugins/s/harness/bodies/autopilot.md` adds a `--parallel N` row to its run-controls table with default 3, and one sentence that the in-session drive runs members in engine-computed waves.
- **Tests, black-box against temp roots.** In `test_autopilot.py` add `WaveTest(AutopilotTestBase)` with a helper that plants a ready member under a chosen root (the repo root or `.worktrees/<slug>`) with `planned/<slug>/plan.md` at `Status: ready` and the given `specs/<cap>/spec.md` files, then cover the six scenarios of `member-wave-scheduling` by calling `compute_waves` directly and `main([...,"--waves","--json"])` for the CLI rendering and the drive-nothing guarantee (a spy `member_driver` never called, no heartbeat file written).
- **Version.** Bump `plugins/s/.claude-plugin/plugin.json` by one patch level over the value `origin/main` carries when the task runs.

Risk: two members that both add requirements to one capability would often merge cleanly, yet the rule serializes them. Guard: the rule is conservative by design and the cap of 1 restores the serial walk; loosening it is a later change once real epics show the cost.

## Questions and answers

### Q1: How are independent members chosen for a wave?
- **Question:** When the in-session autopilot drives several members in parallel, how should it decide which members may build concurrently? Options: (1) capability-disjoint waves computed by the engine from planned delta capabilities; (2) an explicit dependency column in the epic table; (3) always parallel, relying on the reconcile step. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. The shared verified library is the one write that makes parallel members unsafe, and its footprint is on disk once a plan lands, so the engine computes disjoint waves and the epic grammar stays unchanged.
- **Queued:** q-autopilot-parallel-member-scheduling

### Q2: Where does the concurrency cap come from?
- **Question:** Where should the cap on concurrently driven members come from? Options: (1) a Phase 2 run control, default 3, no config key; (2) a new `concurrency` key on the pipeline's `autopilot` block; (3) the build entry's `parallelism`. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. The cap sits beside the existing per-run controls; the in-session drive ignores `autopilot` blocks, and `parallelism` caps sub-agent fan-out inside one build.
- **Queued:** q-autopilot-member-concurrency-cap-source

## Readiness attestation

### Problem and motivation

The in-session autopilot drives members one at a time even when several are ready and independent, so delivery time scales with member count and the user parallelizes by hand.

Evidence:

- Capability `epic-autopilot`, requirement `in-session-drive`: the drive "loops over the epic's members" in the dry run's order, one sub-agent per stage; `plugins/s/skills/build/scripts/autopilot.py:1104-1106` loops `for member in reached` serially.
- This session built `plan-summary-heading` and `ignore-local-state` concurrently by hand in two worktrees at the user's request.
- The oracle's `Cited:` sources for Q1 and Q2 record "no parallel member builds" only as closed epics' non-goals, never as a verified rule.

### Scope and non-goals

The change touches the driver's wave computation, the in-session skill flow, the harness body, and four requirements; the detached loop, the epic grammar, the pipeline schema, and the build skill stay out.

Evidence:

- In scope: `autopilot.py:113-153` (`parse_members`, `select_and_order`), `:1228-1268` (`main`), `plugins/s/skills/autopilot/SKILL.md:81-107` (run controls) and `:109-454` (in-session drive), `plugins/s/harness/bodies/autopilot.md:33-46` (controls table).
- Out of scope: `autopilot.py:1029-1146` (`run`) and `:587` (`drive_member`) are not edited; `pipeline_schema.py:142-156` is not edited; `.shipd/README.md:741-756` (stub table grammar) is not edited.

### Affected capabilities and files

One capability and five files are affected, because the waves are computed in the driver, consumed by the skill, mirrored in the harness body, and tested beside the driver.

Evidence:

- Capability `epic-autopilot`: `in-session-drive` (base e711c2de2cac), `in-session-asks-human` (base e1d4fbd50cb6), `deliver-skill` (base 509d838de2d2), all from `spec_status.py base-hash`; added `member-wave-scheduling`.
- Files: `plugins/s/skills/build/scripts/autopilot.py`, `plugins/s/skills/build/tests/test_autopilot.py`, `plugins/s/skills/autopilot/SKILL.md`, `plugins/s/harness/bodies/autopilot.md`, `plugins/s/.claude-plugin/plugin.json`.
- Runnable premise: `spec_status.py pipeline-show --json` exited 0 and printed `{"source": "default", "entries": [...]}` with `plan`, `gate`, `build`, and `review` entries.
- Runnable premise: `spec_status.py epic-show autonomous-delivery --json` exited 0 and listed members with `slug`, `state`, `risk`, and `worktree` fields, confirming member state derives from disk including worktrees.
- Runnable premise: `spec_status.py show ignore-local-state --json` from its worktree exited 0 and printed the change's status, confirming a planned change is readable through the hosting root.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- Independence rule (capability-disjoint waves): settled by the user, Q1.
- Cap source (Phase 2 run control, default 3): settled by the user, Q2.
- Home (the in-session drive, not the detached driver): settled by the request, which names sub-agents, and by `in-session-drive` being the sub-agent surface.
- Recompute waves after every wave: settled by investigation, since member state and capabilities live on disk and change as plans land.
- Failure handling (finish the wave, start nothing new, report once): settled by `in-session-asks-human`, which forbids continuing while a stop is unanswered.
