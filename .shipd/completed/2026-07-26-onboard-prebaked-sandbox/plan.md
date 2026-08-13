# onboard-prebaked-sandbox
Status: verified

## Idea

The first live test of the sandbox-first walkthrough surfaced two failures.
Startup is slow: the guide authors the cycle-1 artifacts from scratch and
explores the real repo for example shapes on every run, so minutes pass before
anything interactive appears. And the teaching UX is poor: cycle 1 ran as one
long silent burst that ended in a wall-of-text recap, with internal
troubleshooting (coordinator CLI syntax discovery) leaking into the transcript.

This change fixes both:

- Ship a **pre-built sandbox template on disk** inside the plugin
  (`plugins/s/skills/onboard/assets/`): the `.shipd/` layout with the cycle-1
  `add-board` change already authored and lint-clean, plus a reference
  implementation (`kanban.py`, `cards.json`) kept outside the sandbox layout.
  Scaffolding becomes copy + `git init` — near-instant, no live authoring, no
  repo exploration.
- Add **pacing discipline** to the skill: explain-before-do (a sentence or
  two of intent ahead of every action), mid-cycle pauses so no cycle runs
  end-to-end without a user reply, short teaching beats, excerpt-only
  quoting, the rendered board shown early as the visual payoff, few-sentence
  lifecycle explanations, and never narrating internal troubleshooting. The
  live test showed cycle 1 executing plan → merge in one silent burst and
  explaining it retrospectively — the opposite of onboarding.
- Bump the plugin version.

### Non-goals

- Cycles 2–3 stay live-authored — they hand design decisions to the user,
  which cannot be pre-baked.
- No engine-script changes and no changes to other skills.
- No `/s:onboard` eval case (still `/s:plan`-only harness).

Affected capabilities: `shipd-onboard` (two added requirements, one modified).
Impact: `plugins/s/skills/onboard/assets/` (new),
`plugins/s/skills/onboard/SKILL.md`, `plugins/s/.claude-plugin/plugin.json`
(0.3.4 → 0.3.5).

## Implementation

- **Template location:** `plugins/s/skills/onboard/assets/sandbox/` — assets
  ride the plugin cache snapshot, so at runtime the skill resolves it as
  `${CLAUDE_PLUGIN_ROOT}/skills/onboard/assets/sandbox`. The empty
  `verified/` needs a `.gitkeep` (git cannot track empty directories).
  Rejected: generating the template at first run — that is exactly the slow
  path being removed.
- **Reference implementation lives outside the sandbox layout**, at
  `assets/solutions/add-board/` (`kanban.py`, `cards.json`), and is copied in
  only at cycle 1's build step — if it were inside the template, the app would
  pre-exist before "build" and the teaching beat would be a lie.
- **Template `add-board` artifacts** (under
  `assets/sandbox/.shipd/planned/add-board/`): `plan.md` (`# add-board`,
  `Status: draft`, `## Idea` with `### Non-goals`, `## Implementation`);
  `specs/kanban/spec.md` with `## ADDED Requirements` declaring `list-cards`
  (the CLI SHALL list every card with id, lane, title) and `board-view` (the
  CLI SHALL render cards as a three-column todo/doing/done board), each with
  an `id:` and one `#### Scenario:`; `tasks.md` with three `[req:]`-tagged
  tasks (implement `list`, implement `board`, seed `cards.json`). Must lint
  clean against the engine — the smoke task proves it.
- **Reference `kanban.py`:** single file, stdlib only; `list` prints
  `#<id> [<lane>] <title>` per card; `board` prints three columns headed
  TODO / DOING / DONE with card titles under their lane; cards load from
  `cards.json` (list of `{"id", "title", "lane"}`). `cards.json` seeds three
  cards spread across the lanes.
- **Scaffold becomes a copy:** `cp -R` the template into `$SANDBOX`, then
  `git init`. The skill explicitly forbids reading the user's real repository
  for examples — the template is the example.
- **Pacing rules go in the skill as binding instructions:** explain before
  doing — every action is preceded by a sentence or two of intent, and a
  cycle is never executed as a silent batch explained afterwards. Cycle 1 is
  three checkpointed beats (A: orient + walk the pre-authored artifacts;
  B: lint + promote + build + board payoff; C: tick + statuses + merge +
  short lifecycle note), each beat boundary a plain-text typed pause — so a
  learner replies at least twice inside cycle 1. Teach in short beats (a
  few short paragraphs, not a recap essay); quote at most a few lines of any
  file, never full dumps; reach the rendered board early — it is the payoff
  that makes the artifacts worth explaining; cap post-merge lifecycle
  explanations at a few sentences; never narrate internal troubleshooting or
  command-syntax discovery — the skill documents the exact engine
  invocations, so use them as written.
- **Version 0.3.4 → 0.3.5** per the plugin-snapshot rule.

Risk: template artifacts drifting from the engine's lint rules as the grammar
evolves; mitigated by the smoke task linting the copied template through the
real engine, which any future change to the template must re-run.
