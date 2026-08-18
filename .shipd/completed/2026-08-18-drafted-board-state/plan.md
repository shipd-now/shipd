# drafted-board-state
Status: verified

## Idea

Give the delivery board a first-class `drafted` member state and close the
remaining `pr-mode` gaps in doctor and the documentation surfaces.

### Motivation

The shipped `draft-pr-mode` change introduced a `drafted` terminal outcome,
but the board mis-lanes such members as `shipped` (their worktree-derived
state reads `archived` while the PR is still open) and gives them no badge,
and `shipd doctor` passes an invalid `pr-mode` value straight through its
`config` check. The format authority, the copyable config example, the
quickstart, and the constitution likewise predate the key.

### Details

- Board: map the `drafted` outcome explicitly in the heartbeat roster, lane
  a drafted member into `review` (before the archived-to-shipped branch),
  and give it an informational `◇ drafted` signal on the lane card.
- Doctor: the `config` check also resolves `pr-mode`, failing with the
  accessor's own error on an invalid value; no new check name.
- Docs: `pr-mode` sections in the content directory's `README.md` and the
  copyable config example, a quickstart mention, and a constitution
  amendment acknowledging the workspace carve-out.

Affected capabilities: `delivery-dashboard` (added), `shipd-cli` (added),
`shipd-config` (added). Impact:
`plugins/s/skills/build/scripts/heartbeat.py`,
`plugins/s/skills/build/scripts/dashboard.py`, `plugins/s/bin/shipd`,
`.shipd/README.md`,
`plugins/s/skills/build/references/shipd.config.example.json`,
`docs/quickstart.md`, `.shipd/constitution.md`, engine tests, plugin
version bump.

### Non-goals

- No spec-detail modal changes: terminal outcomes already clear the stale
  `stage` from the roster entry, and a drafted member is not parked, so it
  renders as a normal member there.
- No filter-strip, CFD, or metrics changes: the filter strip enumerates no
  outcome kinds, `flow_lane` maps lifecycle states (not outcomes), and a
  draft is not a ship event.
- No change to parked-member semantics: `rejected`/`needs-human`/`stale`
  keep their error-tier treatment untouched.
- No new doctor check name: the documented check list stays stable.

## Implementation

- **Lane choice: `review`.** A drafted member's PR awaits human review and
  merge, which is exactly the `review` lane's meaning; `shipped` is wrong
  (nothing merged) and `building` is misleading (nothing is running). The
  `live == "drafted"` branch in `dashboard._member_column` must sit before
  the `live == "shipped" or state == "archived"` branch, because a drafted
  member's worktree-derived state is `archived` — verified this session:
  `spec_status._member_state` reads a completed archive as `archived`, and
  the current branch order sends it to `shipped`.
- **Signal design: extend the existing single predicate.** The board's own
  architecture routes every card badge through the pure `member_signal`
  predicate ("a single predicate feeds both the card and the modal"), so
  drafted becomes a new informational kind there — `{"kind": "drafted",
  "glyph": "◇", "label": "drafted"}`, rendered in an accent tier at the
  card render sites, never the error color. Rejected alternative: a second
  drafted-only predicate — two seams for one card text.
- **Heartbeat mapping stays behavior-identical but explicit.**
  `_OUTCOME_STATE` already falls through unknown outcomes verbatim, so
  `"drafted": "drafted"` changes nothing at runtime; the entry makes the
  state first-class and greppable, per the shipped change's review finding.
- **Doctor placement: fold into `config`.** `check_config` already owns
  layered-config validity; resolving `resolve_pr_mode(root)` there reuses
  the accessor's error text (observed this session: it names the key,
  offending value, accepted values, and supplying file) and keeps the
  documented check list — ran `plugins/s/bin/shipd doctor` and observed the
  `ok config — content directory …` line this check extends. Rejected
  alternative: a new `pr-mode` check line — grows the documented list for a
  key most repos never declare.
- **Docs mirror the pipeline-grammar precedent.** The `pr-mode-docs`
  requirement mirrors `pipeline-grammar-docs`: format authority section
  plus a named-but-not-declared mention in the copyable example JSON. The
  constitution amendment keeps this repo's own auto-merge rule while
  acknowledging the engine's workspace-level carve-out, closing the
  doc-drift observation from PR #75.
- **Tests land where the seams are.** Stdlib: `tests/test_heartbeat.py`
  (mapping), `tests/test_board_activity.py` (lane + signal, textual-free),
  `tests/test_shipd_cli.py` (config check). Textual:
  `tests_textual/test_dashboard.py` gains one drafted-card render case
  (textual is importable locally per doctor; CI runs that suite
  separately).
- **Version bump** to 0.6.137 in `plugins/s/.claude-plugin/plugin.json`
  (cache snapshot is version-keyed).
- **Risk: glyph/tier plumbing.** The card render sites style the signal by
  kind; a missed site would render `◇` in the error color. Guarded by the
  textual render test asserting the accent-tier class.
