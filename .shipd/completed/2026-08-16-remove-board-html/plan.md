# remove-board-html
Status: verified

## Idea

Remove the delivery board's HTML page mode — the `dashboard.py html` verb and
the `shipd board html` CLI mode word — from the engine, the CLI, the specs,
the tests, and the docs.

### Motivation

The HTML page mode is unused, and it has already drifted from the TUI: the
2026-08-16 semantic review of PR #25 noted the HTML table reads a member's
`stage` only from the autopilot roster, disagreeing with the TUI's new
build-heartbeat-aware lane semantics. Rather than maintain a second renderer
nobody uses, remove it.

### Details

- Delete the `board-html` requirement from `delivery-dashboard` and the html
  renderer/verb from `plugins/s/skills/build/scripts/dashboard.py`
  (`render_board_html`, `_write_html_atomic`, `_cmd_html`, the `html`
  subparser, the now-unused `import html`, and docstring/comment mentions).
- Modify `shipd-cli`'s `cli-dispatch`: the board-mode mapping consumes only
  `text`; `html` stops being special and falls through to the interactive
  delegate like any other trailing argument.
- Remove the `"html"` mapping and usage-banner line from `plugins/s/bin/shipd`,
  the html tests in both suites, and the two README lines documenting the mode.
- Bump the plugin version.

Affected capabilities: `delivery-dashboard` (modified — one requirement
removed), `shipd-cli` (modified). Impact:
`plugins/s/skills/build/scripts/dashboard.py`, `plugins/s/bin/shipd`,
`plugins/s/skills/build/tests_textual/test_dashboard.py`,
`plugins/s/skills/build/tests/test_shipd_cli.py`, `README.md`,
`plugins/s/.claude-plugin/plugin.json`; no dependency changes.

### Non-goals

- No `board-tui` restatement: its illustrative parenthetical "(so `board` and
  `html` also work)" stays until the next natural `board-tui` modification
  (Q1, oracle-settled) — the operative "any verb" clause remains true.
- No replacement export/snapshot mode; the text board (`shipd board text`) and
  the TUI are the board's two surfaces.
- No changes to text-board or TUI behavior.

## Implementation

- **Fall-through, not a retired-word error.** After `bin/shipd` stops
  consuming `html`, `shipd board html --out <p> --once` delegates to
  `dashboard.py tui html --out <p> --once`, which argparse rejects. Verified
  by running `dashboard.py tui html --out /tmp/x --once` today: exit `2`,
  `error: unrecognized arguments`. Rejected: a special-case usage error for
  the retired mode word (mirroring the retired top-level `tui` verb) — extra
  CLI logic for a mode that the default clause of the existing board-mode
  grammar already handles honestly.
- **`import html` goes too.** Every `html.escape` use in `dashboard.py` sits
  inside `render_board_html` (lines 1233-1289); nothing else imports it.
  `tui_bootstrap.py` has no html references; the self-provision comment at
  line ~866 and module docstring lines 6-7 name the verb and are updated.
- **Delta shape per Q1.** `delivery-dashboard` carries a REMOVED entry for
  `board-html` (base `235946794a1e`); `shipd-cli` carries a MODIFIED
  `cli-dispatch` (base `93319557d1d2`) restating the requirement without the
  html mode word, dropping the "Board html mode" scenario, and adding a
  fall-through scenario anchored on the observed exit-2 behavior. `board-tui`
  is deliberately untouched.
- **Tests.** `tests/test_shipd_cli.py` replaces the html snapshot test with
  the fall-through assertion (and fixes its provisioning comment);
  `tests_textual/test_dashboard.py` drops the "HTML renderer and the html
  verb" section. Both suites were green at today's `c2bb917`
  (1157 stdlib + 309 textual, observed this session).
- Archived changes under `.shipd/completed/` mentioning the html verb are
  immutable history and are not edited.

Risk: an external script invoking `dashboard.py html` would start exiting 2;
accepted — the mode was documented only in this repo's README, and the
removal is the point of the change.

## Questions and answers

### Q1: Also modify board-tui to drop its stale html mention?
- **Question:** `board-tui` (13,556 chars, over the ~2,000-token budget)
  mentions the html verb once, in an illustrative parenthetical. Should this
  change (a) leave `board-tui` untouched, accepting the stale six-word example
  until the next natural modification, or (b) include a full MODIFIED
  restatement now? Recommendation: (a).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Leave `board-tui` untouched — option (a). The parenthetical is
  illustrative, not normative: the operative "any `dashboard.py` verb
  invocation" clause stays true after removal. The context-economy budget
  exists to keep deltas lean, and a 13.5k full-content MODIFIED carrying a
  `base:` hash for a requirement this change does not alter maximizes
  exposure to take-newer stale-base overwrites for zero semantic gain.
- **Cited:** verified/shipd-spec-lint, verified/shipd-spec-merge,
  verified/shipd-spec-format
