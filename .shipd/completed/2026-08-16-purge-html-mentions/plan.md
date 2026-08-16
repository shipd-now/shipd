# purge-html-mentions
Status: verified

## Idea

Erase the last references to the removed board HTML mode from the live spec
masters and the CLI test suite, so nothing outside the immutable change
archives mentions the feature at all.

### Motivation

The `remove-board-html` change (merged as PR #33) deliberately left three
references to the retired verb standing — two illustrative asides in spec
masters and the CLI's retired-mode scenario/test. The user has since overruled
that disposition: no HTML-mode functionality, documentation, or mention may
remain anywhere outside archived history.

### Details

- `delivery-dashboard` master: `board-tui`'s provisioning aside becomes
  "(so `board` also works)"; `board-shipd-theme` loses its "(the `html` verb's
  separate inline page CSS is exempt)" parenthetical entirely.
- `shipd-cli` master: the "Retired html mode falls through" scenario becomes a
  generic "Unknown board mode word falls through" scenario (`frobnicate`), so
  the fall-through clause keeps coverage without naming the retired word.
- `plugins/s/skills/build/tests/test_shipd_cli.py`: the retired-html test is
  rewritten to the generic unknown-word shape, dropping every html mention.
- Plugin version bump (test file lives under `plugins/s/`).
- Live epic records under `.shipd/epics/` lose their two references to the
  removed verb: `update-ui-look-feel/epic.md`'s Non-goals drops the sentence
  "The `html` verb's static page is out of scope.", and `shipd-dx/epic.md`'s
  Non-goals drops the clause "; the board's existing `html` verb is
  unchanged" — epics are live documents, not archives, so the sweep covers
  them.

Affected capabilities: `delivery-dashboard` (modified), `shipd-cli`
(modified). Impact: `plugins/s/skills/build/tests/test_shipd_cli.py`,
`plugins/s/.claude-plugin/plugin.json`; no engine code changes.

### Non-goals

- `.shipd/completed/` archives stay untouched — they are the immutable record
  of past changes, and rewriting history is out of scope.
- Unrelated occurrences of the string "html" stay: GitHub's `html_url` API
  field in `review_gate.py` and its tests, `semdiff.py`'s generic `.html`
  file-extension→language mapping, external URLs cited in
  `.shipd/research/` reports, and the `.dc.html` design-mock filename named
  in `update-ui-look-feel/epic.md` (a design artifact, not the board
  feature) — none belong to the board feature.
- No behavior changes anywhere: `shipd board <unknown-word>` already falls
  through to the interactive delegate; only the example word naming that
  behavior changes.

## Implementation

- **User override supersedes the prior Q1 disposition.** The
  `remove-board-html` plan's oracle-settled Q1 kept the two spec asides to
  avoid a 13.5k `MODIFIED` restatement; the user's typed instruction now
  requires the sweep, and the user is the final authority. The restatement
  cost is mitigated by generating both `MODIFIED` blocks programmatically
  from the current masters (byte-identical apart from the single edit each),
  with `base:` hashes computed by the engine's own `spec_common.content_hash`
  at authoring time: `board-tui` `e42cc3f13b2f`, `board-shipd-theme`
  `2c6ed2a95c1d`, `cli-dispatch` `3da395f81af1`. The oversized `board-tui`
  delta triggers only the linter's context-economy *warning*, which never
  affects the exit code.
- **Scenario swap keeps coverage.** The fall-through clause of `cli-dispatch`
  ("any other first trailing argument … delegates to `dashboard.py tui`")
  keeps a pinning scenario — the word changes from the retired `html` to the
  neutral `frobnicate`, and the "no page file is written" clause drops (no
  `--out` remains to write anything). The matching test asserts exit `2` and
  `unrecognized arguments` on stderr, mirroring the current test's shape
  minus its html strings; verified premise: `shipd board html --out … --once`
  falls through with exit `2` today (observed in the PR #33 build), and the
  delegate rejects any unknown positional identically.
- **Sweep verification is part of the change.** A task greps the live tree
  (excluding `.shipd/completed/`, `.worktrees/`, `.git/`) and must find no
  remaining reference to the board HTML feature — the allowed unrelated
  matches are exactly `html_url`, `semdiff.py`'s `.html` mapping, and
  research-report URLs.

Risk: another in-flight change touching `board-tui` before this merges would
hit take-newer with a stale-base warning; accepted — the delta is generated
from the current master and the merge warning would surface any race in the
build report.
