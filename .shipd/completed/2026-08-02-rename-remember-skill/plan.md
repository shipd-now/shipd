# rename-remember-skill
Status: verified
Theme: developer-experience

## Idea

Rename the personal-memory capture skill from `/s:preferences` to
`/s:remember`: move the skill directory, retarget the `shipd-memory` capability's
skill contract, update every cross-reference, and re-point the trigger phrases at
"remember"-shaped invocations. Behavior is unchanged.

### Motivation

`/s:preferences` is a noun that narrows the concept — the store holds general
`memory-*` pages about how the user works, not just "preferences" — and it does
not pair with its opposite, `/s:forget`. `/s:remember` is the natural verb,
makes remember ↔ forget a symmetric pair, and matches the "memory" framing the
rest of the triad (`/s:memory`, `/s:forget`) already uses.

### Details

- Rename the skill directory `plugins/s/skills/preferences/` →
  `plugins/s/skills/remember/` (so the invocation becomes `/s:remember`), and
  update its `SKILL.md` frontmatter (`name`, `description`), trigger phrases
  (toward "remember I…", "note that…", "/s:remember"), the version-announce
  example, and every in-body `/s:preferences` / `skills/preferences` reference.
- Retarget the `shipd-memory` capability: remove `preferences-skill` and add
  `remember-skill` (identical capture contract, now naming `/s:remember` at
  `plugins/s/skills/remember/SKILL.md`); modify `git-backing-flow` to name
  `/s:remember` and the new SKILL.md path.
- Update the `/s:memory` and `/s:forget` SKILL.md cross-references and the
  `AGENTS.md` skill-roster sentence from `/s:preferences` to `/s:remember`.

Affected capabilities: `shipd-memory` (modified — `preferences-skill` removed,
`remember-skill` added, `git-backing-flow` modified). Impact: renamed
`plugins/s/skills/preferences/` → `remember/`, edits to `memory/SKILL.md`,
`forget/SKILL.md`, `AGENTS.md`; plugin version bump to 0.6.26. No engine or
script changes; no behavior change. No new dependencies.

### Non-goals

- No behavior change — the capture flow (extract → reconcile → confirm →
  staged `--personal` emit) and the git-backing flow are byte-for-byte the same;
  only the skill's name, path, and references change.
- No change to `/s:memory` or `/s:forget` names — only the capture verb is
  renamed; the triad becomes remember / memory / forget.
- No overloaded `/s:memory <arg>` capture path — adding a memory stays a
  distinct verb (`/s:remember`), keeping the remember ↔ forget symmetry.
- No new capability and no roster change — `/s:remember` stays a typed-round
  skill (no AskUserQuestion), so `shipd-interaction` is untouched.

## Implementation

- **The rename is REMOVE + ADD, not RENAMED.** The `RENAMED Requirements`
  operation only re-keys a requirement's `id` and preserves its content, but this
  rename changes both the id (`preferences-skill` → `remember-skill`) and the
  content (the skill name and path throughout). So the delta removes
  `preferences-skill` (with a migration note) and adds `remember-skill` carrying
  the identical capture contract reworded for `/s:remember`. Rejected: RENAMED
  plus a follow-up MODIFIED on the re-keyed id — fragile ordering for no gain
  over a clean remove/add.

- **`git-backing-flow` is a straight MODIFIED.** Its id is unchanged; only the
  `/s:preferences` / `skills/preferences` references inside it become
  `/s:remember` / `skills/remember`. Its `base:` hash is the current master's.

- **Directory rename uses `git mv`.** `git mv plugins/s/skills/preferences
  plugins/s/skills/remember` preserves history; the skill's invocation name is
  derived from the directory, so the move is what makes it `/s:remember`. Then a
  sweep of the moved `SKILL.md` swaps `am:preferences` → `am:remember` and
  `skills/preferences` → `skills/remember`, updates the frontmatter `name`/
  `description`, the trigger phrases, and the illustrative version-announce line
  (now `am:remember v<version>`).

- **Catch every straggler with a repo-wide grep.** After the edits, a
  `grep -rn "am:preferences\|skills/preferences" plugins/ .shipd/verified AGENTS.md`
  must return nothing (the `.shipd/completed/` archive is immutable history and is
  left untouched). Known references beyond the moved skill: `memory/SKILL.md`,
  `forget/SKILL.md`, and the `AGENTS.md` roster sentence.

- **Version bump; no engine work.** The change touches `plugins/s/`, so the
  plugin version bumps to 0.6.26. No script changes means the engine unit suite
  must stay green, run as the final gate.

Risk: a missed reference would leave a dangling `/s:preferences` mention after
the skill no longer exists; guarded by the mandatory repo-wide grep sweep
returning clean before the change is considered done.
