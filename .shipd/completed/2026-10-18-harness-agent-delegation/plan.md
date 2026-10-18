# harness-agent-delegation
Status: verified
Epic: harness-agents
Theme: developer-experience
Planned-at: b2131406dcd52d652ac30b5c50730aa1f1ebcd50
Gated-hash: b5a1b5605de7

## Idea

Name the generated agents in the instruction that delegates to them: each body's
`if:subagents` branch names the `shipd-<role>` agent the harness actually
receives, so a session knows what to spawn.

### Motivation

A harness that declares `subagents` is told to "spawn one executor" or "delegate
to a non-interactive helper" without ever being told which agent, so a session on
OpenCode, Antigravity CLI, or oh-my-pi now has `shipd-sub-agent` and
`shipd-oracle` on disk but no instruction naming them. The delegation text and
the agents it needs are the last two pieces that must agree.

### Details

- `plugins/s/harness/bodies/build.md`: the `if:subagents` branch names
  `shipd-sub-agent` as the executor it directs the harness to spawn.
- `plugins/s/harness/bodies/ask.md`: the `if:subagents` branch names
  `shipd-oracle` as the helper agent.
- `plugins/s/harness/bodies/autopilot.md`: the `if:subagents` branch names
  `shipd-sub-agent` as the per-stage worker.
- `test_harness_bodies.py`: the named agent in each branch, and its absence for
  a harness declaring no `subagents`.
- `plugins/s/.claude-plugin/plugin.json`: the version bump this change owes.

Affected capabilities: `harness-command-bodies` (modified). Impact: no new
dependency; a harness without `subagents` renders the same single-agent branch
it always did, naming no agent.

### Non-goals

- No rename of the plugin's Claude agents or the skills that spawn them: the
  Claude surface keeps `s:sub-agent`/`s:oracle`/`s:validator`, which its own
  plugin agents register, and six capabilities pin those ids.
- No change to the neutral source, the registry, the render engine, or the verb.
- No documentation.

## Implementation

- **The generated bodies name the generated agents.** Each `if:subagents`
  branch names the `shipd-<role>` id the generator writes for that harness, so
  the instruction and the agents it needs share one name. `build` and
  `autopilot` name `shipd-sub-agent`; `ask` names `shipd-oracle`.
- **The Claude surface keeps its own ids, deliberately.** The Claude plugin's
  agents register as `s:sub-agent`/`s:oracle`/`s:validator`, and six verified
  capabilities (`build-spec-lifecycle`, `build-subagent-handoff`, `shipd-ask`,
  `shipd-plan`, `epic-autopilot`, `shipd-port`) pin those ids; the plugin skills
  already name them correctly, and each surface's instruction names the agents
  that surface has. Renaming them to `shipd-<role>` for one literal id
  everywhere would rewrite six capabilities' agent references for no functional
  gain. Rejected: the rename, as out of proportion to the goal.
- **A non-`subagents` harness names nothing.** The branches are already
  feature-gated, so the `else` text is untouched and no agent id leaks into a
  harness that has no agents. A test renders `build` with and without the
  feature and asserts the difference.
- **The version bump rides here.** `plugin.json` moves `0.6.323` → `0.6.324`.

Risk: none material — the edit is prose inside existing feature gates, and the
render tests pin both the named and unnamed renders.

## Readiness attestation

### Problem and motivation

A harness that declares `subagents` is told to delegate but never told which
agent, so a session now has `shipd-sub-agent` on disk with no instruction naming
it.

Evidence:

- Epic `harness-agents` Introduction: those harnesses "are told to spawn an
  executor that does not exist".
- `plugins/s/harness/bodies/build.md`: the `if:subagents` branch says "spawn one
  executor" with no id.

### Scope and non-goals

The three `if:subagents` branches and their tests, plus the version bump; the
plugin's Claude agents, the skills, and the engine stay out.

Evidence:

- In scope: `plugins/s/harness/bodies/{build,ask,autopilot}.md`,
  `test_harness_bodies.py`, `plugins/s/.claude-plugin/plugin.json`.
- Out of scope: the plugin agent ids are pinned by six verified capabilities;
  the registry, render, and verb members are done.

### Affected capabilities and files

One capability, `harness-command-bodies`, modified; three body files, one test
file, and the version bump.

Evidence:

- Capability `harness-command-bodies`: `delegation-agent-ids` added.
- Edited: `plugins/s/harness/bodies/build.md`, `ask.md`, `autopilot.md`,
  `test_harness_bodies.py`, `plugins/s/.claude-plugin/plugin.json`.
- Runnable premise: `python3 -m unittest discover -s
  plugins/s/skills/build/tests -p 'test_harness_bodies.py'` → exit 0, 27 tests
  OK.

### No open task-shaping decision

Every task-shaping decision is settled by the epic and the render engine.

Evidence:

- The three edit sites: settled by the `if:subagents` gates in the bodies.
- The agent ids: settled by the epic's `shipd-<role>` Decision.
- The Claude surface keeping its ids: settled by investigation — six verified
  capabilities pin `s:sub-agent`/`s:oracle`/`s:validator`.
