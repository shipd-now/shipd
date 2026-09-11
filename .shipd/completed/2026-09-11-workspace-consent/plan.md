# workspace-consent
Status: verified

## Idea

Gate every workspace member materialization behind a single up-front consent
round — reuse existing checkouts, materialize fresh, review, or stop — and make
`/s:build` workspace-aware so a declared-but-absent member is pulled or mapped
only after the user agrees.

### Motivation

`/s:workspace sync` executes every planned clone with no question ("the
invocation is the consent"), so a user with existing checkouts gets duplicates
unless they knew to run `map` first. Build flows are workspace-blind: targeting
a declared member with no checkout dead-ends instead of offering to pull or map
it.

### Details

- One batched consent round in the `/s:workspace` sync flow before any
  materialization command runs, with reuse-where-found as the recommended
  default; `clone` hands into the same consenting flow.
- A checkout-folder question in that round when no clone source resolves,
  persisted machine-locally as a new `clone_sources` key in
  `.shipd-workspace.local.json` via new engine `workspace-sources` verbs, and
  unioned into the planner's candidate scan.
- A materialization gate in `/s:build` Phase 0: absent declared member → ask
  pull / map / stop, then continue inside the resolved checkout.

Affected capabilities: `shipd-workspace` (modified), `build-context-gate`
(modified). Impact: `plugins/s/skills/build/scripts/spec_common.py`,
`plugins/s/skills/build/scripts/spec_status.py`,
`plugins/s/skills/workspace/SKILL.md`, `plugins/s/skills/build/SKILL.md`,
`docs/workspaces/member-map.md`, `docs/workspaces/getting-started.md`, engine
tests, and the plugin version.

### Non-goals

- No consent gate in standalone `/s:plan` — build-only for now (Q4).
- No `workspace-sync --member` engine flag — the build gate selects the
  member's record from the existing `--json` output.
- No change to headless read guarantees — the engine planner stays read-only
  and network-free.
- No auto-adoption — a found candidate is never mapped without the user's
  explicit choice in the round.

## Implementation

- **Persistence lands in the workspace-local map file**, as an optional
  `clone_sources` array beside `repos`, read in union with the config key
  (config entries first, then local, duplicates removed after expansion).
  Rejected: `~/.shipd-config.json` via a config-write verb — the nearest-wins
  wholesale merge lets any committed workspace config shadow the user's
  machine value; rejected: no persistence — re-asks every session. The current
  loader already tolerates the extra key (verified: `workspace-map` and
  `workspace-sync --json` both exit 0 with `clone_sources` present in the
  local file), so mixed plugin versions stay safe.
- **Verb surface mirrors `workspace-map`**: `workspace-sources` (list),
  `workspace-sources add <dir>`, `workspace-sources remove <dir>` — the
  engine-owned writer; skills never hand-edit the file. `workspace-map set`
  already preserves foreign top-level keys (spec `workspace-map-verbs`), so
  the two verb families coexist without coordination.
- **Consent is one batched round**, the house pattern the oracle cited from
  `verified/shipd-gate` and `verified/shipd-doctor`: consent over a multi-item
  plan is a single batched selection, with member-by-member review as an
  opt-in escape hatch, never a per-item interrogation. Options and semantics
  are bound in the `workspace-clone-sync-flows` delta.
- **`clone` hands into the consenting sync flow.** This deliberately decouples
  the recorded "sync and clone SHALL remain question-free" contract
  (`workspace-setup-skill`) and overrides the unattended-bootstrap rationale in
  `completed/2026-08-01-workspace-clone-skill` — the user's typed decision (Q3).
  Headless consumers are unaffected: they drive the read-only engine verbs
  directly, never the skill.
- **The build gate consumes existing surfaces only**: resolve the workspace
  (`workspace-show`), match the target repo against the roster, read that
  member's record from `workspace-sync --json` (record grammar verified on a
  fixture: executable actions carry `command:`, candidates carry `source:`,
  mapped members plan `action: none` with `mapped:`), then on consent execute
  the advisory command exactly as printed or drive `workspace-map set`.
- **Sources answer triggers a replan**: after `workspace-sources add`, the
  skill recomputes `workspace-sync --json` before executing, so new candidates
  demote fresh clones to reuse under the already-given consent choice.
- **Version bump** to `0.6.205` in `plugins/s/.claude-plugin/plugin.json`,
  same PR; the snapshot refresh after merge follows the repo convention.

Risk: sessions on the stale cached skill snapshot keep the old no-questions
sync until `claude plugin update s@shipd` runs — mitigated by the version bump
making the update effective. Risk: a malformed local `clone_sources` value
would silently disable candidates — guarded by failing the reading verb with
an error naming the file, matching the map file's existing contract.

## Questions and answers

### Q1: Where does the checkout-folder interview answer persist?
- **Question:** Persist the "my checkouts live in <folder>" answer where?
  Options: (1) a `clone_sources` key in `.shipd-workspace.local.json`, unioned
  with config; (2) `~/.shipd-config.json` via a config-write verb; (3) do not
  persist. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1 — the workspace-local dot file. Machine-local and
  per-workspace, engine-owned writer, and immune to shadowing by a committed
  config layer. The queue block was discarded per the capture rubric: this
  delta makes the verified spec the durable record.
- **Queued:** q-clone-sources-interview-persistence

### Q2: What shape does the sync consent round take?
- **Question:** With AskUserQuestion capped at 4 questions per call and 30+
  member workspaces real, is consent one blanket summary question or
  per-member questions? Recommendation: blanket summary with review opt-in.
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** One blanket summary question over the whole plan with
  member-by-member review as the opt-in escape hatch — the standing convention
  for multi-item consent (`/s:gate` and `/s:doctor` both spec a single batched
  selection over a runnable plan).
- **Cited:** verified/shipd-gate, verified/shipd-doctor, verified/shipd-epic

### Q3: Does `clone` keep its unattended end-to-end bootstrap?
- **Question:** Should `/s:workspace clone` stay question-free end-to-end (the
  recorded position) or inherit sync's new consent round? Recommendation from
  the oracle: keep unattended.
- **Verdict:** ANSWER
- **Answered by:** USER
- **Answer:** Typed override of the oracle's position: the user wants a single
  consent up front in the `/s:workspace` flow where the user chooses to reuse
  existing repos or sync new ones — clone's hand-off included. The oracle's
  contrary standing sources are recorded here as the superseded position.
- **Cited:** epic/portable-workspaces, verified/shipd-workspace,
  completed/2026-08-01-workspace-clone-skill

### Q4: Which skills get the materialization gate?
- **Question:** `/s:build` only, or standalone `/s:plan` too? Recommendation:
  build only.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Build only for now; plan is normally reached through build after
  the member exists. The queue block was discarded as explicitly scoped to
  this change.
- **Queued:** q-plan-workspace-gate-scope
