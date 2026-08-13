# onboard-kanban-walkthrough
Status: verified

## Idea

Onboarding today is a six-chapter lecture: `/s:onboard` opens with a chapter
menu, walks the user through docs with checkpoints, and only offers the
hands-on sandbox as an opt-in finale — on a spec-only `greeter` toy with no
runnable code. The user has to make choices before touching anything real, and
the learning-by-doing part arrives last, if at all.

This change inverts the flow:

- `/s:onboard` goes straight into sandbox mode — no chapter menu, no
  start-choice. It scaffolds the throwaway sandbox immediately and tells the
  user what they can do.
- The walkthrough incrementally builds a **CLI kanban app** through guided
  plan → build → merge cycles: first the board (a `kanban.py` with `list` and
  a visual `board` view), then adding cards, then editing cards — then invites
  further user-invented cycles.
- Each cycle prompts the user with the planning task, authors the lean
  artifacts inside the sandbox's `.shipd/planned/`, lints, promotes, implements
  the code, ticks tasks with the coordinator, merges with the real engine, and
  explains what happened to the artifacts (planned → completed, master specs
  grown).
- The six-chapter library under `docs/onboarding/` is deleted; the chapter
  concept is retired.

### Non-goals

- No changes to the engine scripts or to `/s:plan`/`/s:build` — the
  walkthrough only consumes them.
- No eval case for `/s:onboard` (the eval harness covers `/s:plan` only).
- No worktree/branch/PR ceremony inside the sandbox — mentioned in narration,
  exercised only in real repos.
- No fixture files shipped in this repo — the skill's instructions carry the
  kanban fixture inline, as the old greeter fixture did.

Affected capabilities: `shipd-onboard` (modified: one requirement removed, four
modified). Impact: `plugins/s/skills/onboard/SKILL.md` (rewrite),
`docs/onboarding/` (deleted), `plugins/s/.claude-plugin/plugin.json`
(0.3.1 → 0.3.2).

## Implementation

- **Sandbox starts bare** — `git init` plus an empty `.shipd/verified/` and
  `.shipd/planned/`, no seed capability. Cycle 1 then creates the `kanban`
  capability as an ADDED-requirements change, and `spec_merge.py` seeds the
  brand-new master file (it supports this: "Brand-new capability: seed a
  master file"). Rejected: pre-seeding a working kanban app — it would make
  cycle 1 ("add the board") redundant and hide the new-capability flow.
- **Fixture: a single-file python3 CLI.** `kanban.py` over a JSON store
  `cards.json` (card fields: `id`, `title`, `lane`; fixed lanes
  `todo`/`doing`/`done`). Cycle 1 implements `list` (flat listing) and `board`
  (three-column ASCII board) and seeds `cards.json` with three sample cards so
  both views render before an `add` command exists. Cycle 2 adds
  `add <title> [--lane]`. Cycle 3 adds `edit <id> [--title] [--lane]` — the
  `--lane` edit doubles as moving a card across the board. Rejected: a
  multi-file package — ceremony with no teaching value.
- **The skill carries the fixture inline** (spec text and code guidance in
  `SKILL.md`), exactly as the greeter fixture did. Rejected: shipping fixture
  files under the plugin — a second source of truth to keep in sync.
- **Cycle pacing.** Cycle 1 is fully narrated — the guide does everything and
  explains each artifact as it lands. Cycles 2–3 hand the decisions to the
  user (flag names, card wording) while the guide keeps driving. After cycle 3
  the guide offers open-ended further cycles (move, delete, WIP limits) or
  finishing. Checkpoints between cycles are plain-text numbered prompts
  (continue as recommended default / re-explain / stop) — the existing
  no-dialog-with-prose rule and rejection-recovery guardrails carry over.
- **Isolation mechanism unchanged.** Every engine call runs by absolute plugin
  path with the sandbox as `--root`/cwd; all writes land under `$SANDBOX`.
  Planning happens by authoring artifacts directly in the sandbox's
  `planned/` — the walkthrough never invokes `/s:plan` against the user's
  checkout, so it can never touch their codebase.
- **Chapters deleted, not archived.** `docs/onboarding/` has no live consumers
  besides the onboard skill (verified by grep); references inside
  `.shipd/completed/` archives are historical records and stay untouched.

Risk: the skill is model-interpreted prose, so behavior drift is possible;
guarded by a manual smoke run (verification task) that executes the scaffold
and the full cycle-1 engine sequence exactly as the rewritten skill instructs.
