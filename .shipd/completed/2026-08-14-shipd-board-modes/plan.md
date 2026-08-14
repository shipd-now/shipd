# shipd-board-modes
Status: verified

## Idea

Make `shipd board` open the interactive board by default, with positional
mode words selecting the other renderers (`text`, `html`), and retire the
now-redundant `tui` verb.

### Motivation

The user expected `shipd board` to be the interactive delivery board, but the
shipped verb table routes it to the one-shot text renderer and hides the
interactive one behind a separate `tui` verb; the board verb should lead with
the interactive experience and expose the text and HTML renderings as modes.

### Details

- Remap `board` in `plugins/s/bin/shipd`'s verb table: bare `shipd board` →
  `dashboard.py tui`; first trailing bare word `text` → `dashboard.py board`;
  first trailing bare word `html` → `dashboard.py html`. All remaining
  arguments still pass through verbatim.
- Remove the `tui` verb (its behavior is now `shipd board`); update the usage
  banner and the README's CLI section.
- Bump the plugin version 0.6.97 → 0.6.98.

Affected capabilities: `shipd-cli` (modified). Impact: `plugins/s/bin/shipd`,
`plugins/s/skills/build/tests/test_shipd_cli.py`, `README.md`,
`plugins/s/.claude-plugin/plugin.json`; no new dependencies.

### Non-goals

- No changes to `dashboard.py` itself — its `board`/`tui`/`html` verbs and
  flags are untouched; only the dispatcher's mapping moves.
- No `tui` alias kept: the curated surface has one way per action.
- No mode-selection flags (`--text`): the engine's idiom is positional
  subverbs (`metrics summary`, `dashboard.py tui`), and the dispatcher
  follows it.
- No other verb changes.

## Implementation

- **Mode words, not flags.** `shipd board [mode] [args...]` recognizes a mode
  only when the **first** trailing argument is exactly the bare word `text`
  or `html`; the mode word is consumed and the rest passes through verbatim.
  Anything else (including a leading flag) means the default mode:
  `shipd board --root X` → `dashboard.py tui --root X`. Verified premises:
  `dashboard.py tui --help` runs non-interactively and accepts
  `--root/--epic/--interval` (observed, exit 0); `dashboard.py html --out <f>
  --once` writes one snapshot and exits 0 (observed this session). Rejected:
  a `--text` flag — the dispatcher would have to strip a flag the delegate
  does not know, and no engine surface selects modes by flag.
- **Represent modes as a nested table** in `plugins/s/bin/shipd` — e.g.
  `BOARD_MODES = {None: ("dashboard.py", ["tui"]), "text": ("dashboard.py",
  ["board"]), "html": ("dashboard.py", ["html"])}` — resolved before the
  ordinary `VERB_TABLE` delegation path so `os.execv` process replacement,
  verbatim trailing args, and the exit-code contract stay exactly as the
  `cli-dispatch` requirement states them.
- **`tui` is removed, not aliased.** `shipd tui` becomes an unknown verb
  (usage banner on stderr, exit 2). Rationale: the curated surface keeps one
  way per action (the guarded-verb convention in `verified/shipd-port` /
  `verified/spec-status`), and the verb shipped less than a day ago. Rejected:
  a deprecation alias — it would freeze a synonym into the public contract.
- **Testing follows the existing pattern.** Delegation tests compare the
  binary's output byte-for-byte against the delegate script; any test that
  invokes `dashboard.py` as a subprocess carries the existing `HAS_TEXTUAL`
  skip guard (`test_shipd_cli.py:52`), because `dashboard.py`'s script entry
  self-provisions `textual` over the network — the stdlib-only `tests/` suite
  must never trigger that. `shipd board --help` vs `dashboard.py tui --help`
  proves the default-mode mapping without launching the full-screen app.

Risk: a user's day-old habit of `shipd tui` breaks; mitigated by the usage
banner (exit 2) listing `board` first and the README's updated table.
Risk: a future `board`-mode name colliding with a change slug a user meant to
pass positionally — not applicable today (`dashboard.py board` takes no
positional argument), noted for future mode additions.
