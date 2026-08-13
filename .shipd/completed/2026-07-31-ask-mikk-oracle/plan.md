# ask-mikk-oracle
Status: verified
Epic: mikk-knowledge

## Idea

Add the mikk-knowledge epic's read path: an `s:oracle` agent and an `/s:ask`
skill that answer one compact question from the workspace wiki and the asking
repo's spec surfaces — or queue it for the user instead of blocking.

### Motivation

The epic's wiki store shipped with no way to consult it: a planner or
autopilot at an un-inferrable decision still has only a user question round or
parking. The oracle is the middle rung of the epic's read → ask-mikk → human
ladder, and the later plan/autopilot integration members depend on its
contract existing first.

### Details

- New agent definition `plugins/s/agents/oracle.md` (agent type `s:oracle`):
  a non-interactive, clean-context answerer spawned via the Agent tool, taking
  one compact question plus the asking repo's root.
- New skill `plugins/s/skills/ask/SKILL.md` (`/s:ask`): the human entry —
  shapes the request into a compact question, spawns `s:oracle`, relays the
  verdict.
- First-line verdict contract (`ANSWER` / `INSUFFICIENT`) so later callers can
  branch mechanically; `INSUFFICIENT` queues the question through
  `wiki-queue-add`.
- `AGENTS.md` skill roster gains `/s:ask`; plugin version bumps
  0.6.6 → 0.6.7.

Affected capabilities: `shipd-ask` (new). Impact: two new markdown files under
`plugins/s/`, `AGENTS.md`, `plugins/s/.claude-plugin/plugin.json`. No engine
scripts change — the store verbs the oracle uses (`wiki-init`, `wiki-show`,
`wiki-queue-add`, `cat wiki`) shipped in `mikk-wiki-store`.

### Non-goals

- No caller integrations — `/s:plan` and the autopilot consult the oracle in
  the later `plan-ask-mikk` / `autopilot-ask-mikk` members.
- No teach-mikk write path: no distillation, no interviews, no queue draining
  — the oracle's only store write is appending a pending question.
- No engine changes, embeddings, or search beyond index reads and grep — the
  epic binds retrieval to index- and grep-based over markdown.
- No model pinning in the agent definition — the spawning surface picks the
  tier, as with `s:sub-agent` / `s:validator`.

## Implementation

- **Naming.** Skill directory `ask` (single-word verb like `plan`/`research`),
  agent file `oracle.md` → agent type `s:oracle`, capability `shipd-ask`
  following the `am-<skill>` convention. Rejected: an `ask-mikk` directory —
  no existing skill directory is multi-word, and the `/s:` namespace already
  carries the brand.
- **Search ladder (binding order).** The oracle resolves the workspace and
  reads wiki-first, then widens to the asking repo, all engine-mediated where
  a verb exists: (1) `spec_status.py wiki-show`, then `cat wiki index` and
  `cat wiki <slug>` for candidate pages, with read-only grep over
  `<ws-root>/<content-dir>/wiki/` to widen (sanctioned by the epic's
  index-and-grep decision); (2) the asking repo's spec surfaces via
  `spec_status.py --root <asking-root>`: `cat verified <capability>`,
  `cat epic <slug>` (Decisions/Design), `cat research <slug>`, and
  `project-show` for project context. Writes go only through
  `wiki-queue-add`/`wiki-init` — never direct file edits in the store.
- **Verdict contract.** The oracle's reply begins with a first non-blank line
  of exactly `ANSWER` or `INSUFFICIENT`. `ANSWER` is followed by an
  opinionated position (a recommendation, not an alternatives list) plus
  `Cited:` line(s) naming the wiki page(s) (`[[slug]]`) or repo artifacts
  behind it. `INSUFFICIENT` is followed by the compact question block
  (`Question:` / `Options:` / `Recommendation:`) and a `Queued:` line carrying
  the `q-<slug>` (or `none` — see below). Rejected: JSON output — every
  caller is an LLM surface reading markdown, and the plugin's agents return
  prose reports.
- **Queue behavior.** Before queueing, the oracle reads `cat wiki queue`; an
  equivalent pending question is cited (`Queued: q-<existing>`) instead of
  duplicated. Otherwise it derives a kebab `q-<slug>` from the decision
  subject and appends via `wiki-queue-add --origin <asking-repo>[/<surface>]`.
  When the store is missing it runs `wiki-init` first (the verb refuses an
  existing store, so this is safe), keeping the epic's "questions queue up
  instead of blocking" promise even on a fresh workspace. When no workspace is
  discoverable at all, the oracle still returns its verdict from repo surfaces
  alone and reports `Queued: none (no workspace)` rather than failing.
  Rejected: erroring on a missing store — the oracle must never block its
  caller.
- **Skill flow.** `/s:ask` announces the plugin version, shapes the user's
  request into a compact question itself (inferring options and a
  recommendation from the request and repo context — no interview round),
  spawns `s:oracle` with the question and the repo root, and relays the
  verdict: the cited answer verbatim, or the queued `q-<slug>` plus how the
  answer reaches the wiki (answering the queue entry, drained by the future
  teach-mikk).
- **Risks.** Two sessions queueing concurrently can interleave — accepted
  epic-wide (no multi-writer coordination). Live validation of queue side
  effects must not touch the real workspace store: exercise the oracle against
  a scratch workspace fixture (a tmp dir whose `.shipd-config.json` declares
  `workspace`), which isolates discovery by construction.
