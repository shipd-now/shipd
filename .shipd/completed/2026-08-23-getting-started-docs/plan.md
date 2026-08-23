# getting-started-docs
Status: verified

## Idea

Ship the newcomer documentation pair: the first-session guide
`docs/getting-started.md` and a new `docs/cheatsheet.md` that lists every
`/s:` command and every `shipd` verb with its options and one short example.

### Motivation

The guide explains one path through the tool in prose, but a reader who
already knows the workflow has nowhere to look up what a command takes — the
19 `/s:` skills and 15 `shipd` verbs are documented only inside their own
`SKILL.md` files and `--help` banners. The user asked to broaden this change
so it also produces a succinct command reference.

### Details

- New `docs/cheatsheet.md`: a lookup reference, not a tutorial. A short
  conventions preamble covering the flags shared across verbs, then two
  tables — one row per `/s:` command, one row per `shipd` verb — each row
  giving the invocation with its argument and option forms, a one-line
  description, and exactly one short example.
- `docs/getting-started.md` already ships (238 lines, merged in #46 while
  this change stayed unarchived in `planned/`). It is not rewritten: it gains
  one link to the cheatsheet from its closing section, and is re-verified
  against the requirement it already satisfies.

Affected capabilities: `project-readme` (modified — two ADDED requirements).
Impact: `docs/cheatsheet.md` (new), `docs/getting-started.md` (one link added).
Docs only — nothing under `plugins/s/` changes, so no plugin version bump.

### Non-goals

- No `README.md` edit — neither doc is linked from the README by this change;
  the cheatsheet is reached from the guide.
- No restating of what each command *means* — the cheatsheet is a lookup
  table, and the README skills table stays the prose catalog.
- No per-skill internal protocol detail (grill loops, gate exit codes, oracle
  rungs); each row names the invocation surface a caller types, nothing more.
- No coverage of the engine scripts under `plugins/s/skills/build/scripts/`
  that skills call internally — only the two user-facing surfaces.

## Implementation

- **Two authorities, one per table, both mechanically enumerable.** The `/s:`
  rows come from the directories under `plugins/s/skills/` and each one's
  `SKILL.md`; the `shipd` rows come from the verb list in the `shipd --help`
  banner, with each row's options read from `shipd <verb> --help`. Verified by
  running both: `ls plugins/s/skills | wc -l` printed `19`, and the banner's
  verb block counted `15` verbs. This makes the completeness scenarios
  checkable by re-running the same two commands rather than by judgment.
- **Document `shipd copilot`, not `shipd gate`.** The skill was renamed
  `/s:gate` in v0.6.146 but the CLI verb was not: `python3 plugins/s/bin/shipd
  gate --help` printed the top-level usage banner rather than a verb help,
  while `shipd copilot --help` printed `usage: shipd copilot [-h] [--root
  ROOT] [--force] [{add,remove}]`. The cheatsheet names the verb that exists.
- **Shared flags are stated once, in a preamble, not repeated per row.**
  `shipd list|status|locate|related|epic|workspace|lint|harness` all accept
  `--json`, and most accept `--root DIR`; repeating them across 15 rows would
  bury the per-verb options that actually differ. Rejected: a dedicated
  Options column — it widens every row for information most rows share.
- **One example per row, and every example is runnable as written.** The
  examples are read-only or clearly marked as writing, so the verification
  task can execute the read-only ones directly. Rejected: multi-line examples
  or option matrices — the request asked for quick and simple.
- **The guide is linked from, not restructured.** `docs/getting-started.md`
  ends with a `## Where you are now` section (line 222) that already points at
  the other docs; the cheatsheet link joins that list. Rejected: embedding the
  cheatsheet as a section of the guide — a lookup table read repeatedly does
  not belong inside a linear walkthrough read once.
- Risk: the cheatsheet drifting as commands gain or lose options. Guard: the
  delta's completeness scenarios pin the row set to the two enumerable
  authorities, so drift shows up as a missing or extra row rather than as
  silently stale prose.
