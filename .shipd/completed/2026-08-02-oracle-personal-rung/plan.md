# oracle-personal-rung
Status: verified
Epic: personal-memory
Theme: developer-experience

## Idea

Wire the personal memory store into the ask-mikk read ladder as its top rung:
the oracle searches personal memory first (via the `--personal` wiki reads),
before the job wiki, base wiki, and repo surfaces, and marks a personal-store
citation `(personal)`.

### Motivation

The `personal-memory` epic's binding decision is that personal memory sits
*above* the wiki in the read ladder — a personal preference is the highest-signal
answer for how to treat this user. The `personal-memory-store` member shipped the
store and its `--personal` read verbs; this member makes the oracle actually
consult it, which is what lets a captured preference answer a decision without a
user round.

### Details

- Modify the `shipd-ask` oracle contract so the search ladder begins with the
  personal memory store, then job wiki, then base wiki (when present), then repo
  surfaces (focus-first).
- The oracle reads the personal store through the existing `--personal` verbs:
  `cat wiki index --personal`, `cat wiki <slug> --personal`, and read-only grep
  under the store directory reported by `wiki-show --personal`. An absent
  personal store (no memories captured yet) is skipped, exactly as an `(absent)`
  base is.
- A personal-store-backed answer carries a `Cited: [[slug]] (personal)` marker,
  mirroring the existing `(base)` marker, so the caller can tell which store
  answered.
- Update `plugins/s/agents/oracle.md`: add the personal-memory rung as the new
  first rung of the "search ladder (binding order)" section and add the
  `(personal)` citation example; bump the plugin version.

Affected capabilities: `shipd-ask` (modified — `oracle-agent-contract` and
`oracle-cited-answers`). Impact: `plugins/s/agents/oracle.md`; plugin version
bump to 0.6.22. No engine or script changes (the `--personal` read verbs already
exist on `spec_status.py`). No new dependencies.

### Non-goals

- No engine change — the `--personal` verbs (`cat wiki`, `wiki-show`) landed with
  `personal-memory-store`; this member only teaches the oracle to use them.
- No `/s:ask` skill change — the ask skill shapes the question and relays the
  verdict; the laddering lives entirely in the oracle agent definition.
- No write path — capturing, listing, and removing personal memories are the
  `memory-capture`, `memory-browse`, and `memory-git-backing` members.
- No change to the job/base/repo rungs' existing order or behavior; the personal
  rung is prepended, not a reshuffle.

## Implementation

- **Personal is prepended as the top rung; the rest of the ladder is
  untouched.** The `oracle-agent-contract` requirement and `oracle.md`'s
  numbered "search ladder (binding order)" gain a new first rung — the personal
  memory store — pushing job wiki, base wiki, and repo surfaces down one. The
  "take the first durable position" rule is unchanged, so a personal-store answer
  short-circuits the rest. Rejected: personal *below* the job wiki (contradicts
  the epic's "read first" decision — a personal preference must outrank a
  workspace convention for how to treat this user).

- **The oracle reads the personal store by fixed path, workspace-independent.**
  The reads use `--personal` (`cat wiki index --personal`, `cat wiki <slug>
  --personal`) and read-only grep under the directory `wiki-show --personal`
  prints, all with `--root <asking-root>` so `memory_dir` resolves from the
  asking repo's config (default `~/.shipd-memory`). Because the personal store is
  resolved by fixed path and not through workspace discovery, this rung works
  even when the asking repo has no workspace — unlike the job/base rungs.

- **An absent personal store is skipped, never an error.** When `wiki-show
  --personal` reports no store (no memories captured yet), the oracle skips the
  personal rung and proceeds to the job wiki, mirroring how it skips a `base:
  … (absent)` / `base: none` rung. The rung never blocks or errors the oracle.

- **Citation marker mirrors `(base)`.** A position resting on a personal-store
  page is cited `Cited: [[slug]] (personal)`, exactly parallel to the existing
  `Cited: [[slug]] (base)` convention, so a caller can tell personal memory
  answered. The `oracle-cited-answers` requirement and `oracle.md`'s citation
  example both state it.

- **Documentation-only member; verified by inspection + a real oracle drive.**
  The contract requirements are inspection scenarios (the ladder and marker
  appear in `oracle.md` and the spec). Because the change is LLM-facing (the
  oracle agent), it also warrants a real spawn: seed a `memory-<subject>` page in
  a personal store, ask the oracle a matching decision, and confirm it answers
  from the personal rung with the `(personal)` citation before widening.

Risk: the oracle spawning `wiki-show --personal` against a machine with a real
`~/.shipd-memory` could read the user's actual memories during a drive; guard the
verification by pointing `memory_dir` at a throwaway store via a config layer,
exactly as the store member's tests do.
