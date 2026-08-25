# guardrail-state-prune
Status: verified

## Idea

Prune stale remind cooldown state files automatically whenever the guardrail
hook writes state, so `~/.shipd/guardrails/` stops growing unboundedly.

### Motivation

Every session where a remind rule fires leaves a `<session_id>.json` state
file behind forever — the semantic review of the rulebook change flagged the
unbounded growth, and the user chose the prune-on-write fix. A stale file's
only meaning is reminder dedup for a session that is over, so deleting it is
always safe.

### Details

- Sweep the state directory from `save_state` after each successful write:
  delete `*.json` files whose mtime is older than seven days.
- Note the auto-pruning in the cooldown documentation (`docs/guardrails.md`
  and the README's Guardrails section).

Affected capabilities: `guardrail-hook` (modified). Impact:
`plugins/s/skills/build/scripts/guardrails.py`, `tests/test_guardrails.py`,
`docs/guardrails.md`, `.shipd/README.md`,
`plugins/s/.claude-plugin/plugin.json` (version 0.6.154); no new
dependencies.

### Non-goals

- No configuration for the threshold — a fixed seven-day constant, no new
  `.shipd-config.json` key.
- No throttle marker: the sweep runs only when a remind rule actually fires
  (already rare under once-per-session dedup) and costs one `listdir` plus a
  `stat` per file, so throttling state would add complexity for no measurable
  saving.
- No `shipd doctor` probe and no SessionEnd hook — rejected in design as
  weaker alternatives (doctor does not self-heal; SessionEnd misses crashed
  sessions and would drop a resumed session's dedup state).

## Implementation

- **Piggyback on the single write path.** `save_state`
  (`guardrails.py:349`) is the only place state is written, already wrapped
  fail-open; after a successful write, call a new `prune_state_dir(directory,
  now)` on the file's parent directory. Rejected: pruning from `load_state` —
  reads happen even when nothing fires, and the sweep should cost nothing on
  the no-reminder path.
- **Sweep semantics**: delete only entries matching `*.json` whose mtime is
  older than `PRUNE_AGE_SECONDS = 7 * 24 * 3600`. The file just written has a
  fresh mtime and can never self-prune; any active session keeps its own file
  fresh by writing on each fire. Non-JSON entries and subdirectories are left
  untouched.
- **Correctness argument, recorded**: a state file's only role is dedup
  within its own session; the worst outcome of deleting a stale one is a
  single repeated reminder in a weeks-old resumed session. Over-deletion is
  therefore harmless, which is why a coarse mtime threshold suffices.
- **Fail-open throughout**: the sweep runs inside its own try/except —
  an unreadable directory, an unlinkable file, or any race (a file deleted
  between listing and unlink) is ignored; the reminder has already been
  emitted and the session's own state written. The hook still never exits
  non-zero.
- **Docs**: one sentence each in `docs/guardrails.md`'s cooldown section and
  the README's cooldown paragraph — state files from past sessions are
  removed automatically about a week after their last use.
- **Snapshot caveat**: live after the version bump (0.6.154) merges and
  `claude plugin update s@shipd` runs.

Risk: essentially none — the sweep is destructive only toward files whose
loss is harmless by construction, and every failure mode degrades to today's
behavior (the file lingers).
