## 1. Pure parked-signal predicate

- [x] 1.1 [req: board-parked-member-signal] In
      `plugins/s/skills/build/tests/test_board_activity.py` (the stdlib suite
      that loads dashboard with `textual` absent via `_load_dashboard_stdlib`),
      add a failing test for a new `dashboard.member_signal(member, entry)`:
      a `rejected` board-state member returns `{"kind":"rejected","glyph":"⚠",
      "label":"rejected","reason":<entry reason>}`; a `needs-human` entry returns
      `⛔`/`needs-human`; an entry with `stale: True` and `stage:"died 8h ago"`
      returns `†`/`stale (died 8h ago)`; a `driving`/`ready`/`shipped` member
      returns `None`. Run it and observe it fails (no such function).
- [x] 1.2 [req: board-parked-member-signal] In
      `plugins/s/skills/build/scripts/dashboard.py`, add `member_signal` beside
      `_member_column` (above the module-scope `textual` import, so it stays
      dependency-free). Check `entry.get("stale")` first (label
      `stale (<entry stage>)`, glyph `†`), then resolve
      `state = entry.get("state") or member.get("state")` and map `rejected` →
      `⚠`/`rejected` and `needs-human` → `⛔`/`needs-human`, carrying
      `entry.get("reason")`; return `None` otherwise. Confirm 1.1 passes.

## 2. Lane card marker

- [x] 2.1 [req: board-parked-member-signal] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, near the
      existing `_bare_card` `_card_text` tests, add failing tests that a card
      whose member/entry is `rejected` renders `"[$text-error]⚠[/] <slug>[$fg-muted] · rejected[/]"`,
      a `needs-human` entry renders the `⛔`/`· needs-human` form, and a
      stale-marked driving entry (`stale: True`, `stage:"died 8h ago"`) renders
      the `†`/`· stale (died 8h ago)` form. Run and observe failure.
- [x] 2.2 [req: board-parked-member-signal] In `TaskCard._card_text`
      (`dashboard.py`), after the `shipped` branch compute
      `signal = member_signal(self.member, self.entry)` and, when set, return
      the error-tier glyph + slug + muted state label; otherwise fall through to
      the unchanged risk-glyph / driving-stage path. Confirm 2.1 passes and the
      existing risk/driving/shipped `_card_text` tests still pass.

## 3. Modal state chip and reason callout

- [x] 3.1 [req: board-parked-member-signal] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add failing
      tests that mount `MemberDetailScreen` for: (a) a `rejected` member whose
      entry carries `stage:"gate"` and a `reason` — the badge row contains an
      error-tier state chip reading `rejected`, no `stage:` chip, and a mounted
      callout (`#member-signal-callout` or class) whose text is the `reason`;
      (b) a `needs-human` member with no `reason` — the state chip is present
      and no callout is mounted; (c) a `driving` member at stage `build` — the
      muted `stage: build` chip is present and no state chip or callout is
      mounted. Run and observe failure.
- [x] 3.2 [req: board-parked-member-signal] In the spec-detail modal `compose`
      (`dashboard.py` around the badge-row build), compute
      `signal = member_signal(m, entry)`; render an error-tier state chip
      (`classes="modal-badge badge-error"`) when `signal` is set, and guard the
      existing muted stage chip to `entry.get("state") == "driving"`. When
      `signal` and `signal["reason"]`, mount a `member-signal-callout`
      (a `Horizontal` with a `.signal-accent-bar` Static + a `.signal-reason`
      Static carrying the reason, `markup=False`) above the artifact tabs.
      Confirm 3.1 passes.
- [x] 3.3 [req: board-parked-member-signal] In `dashboard.py`, add the CSS: a
      `.badge-error` chip (`background: $error 25%; color: $text-error;`) beside
      `.badge-muted` in the app CSS, and the `member-signal-callout` rules in
      `MemberDetailScreen.CSS` (`background: $error 10%`, a `width: 1` full-height
      `$error` `.signal-accent-bar`, and a `.signal-reason` in `$warning` with
      `padding: 0 1`), mirroring `#epic-stall-banner`. All colors through `$`
      theme variables.

## 4. Repaint on parked flip

- [x] 4.1 [req: board-parked-member-signal] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add a test that
      `_lane_signature` for a member differs between a `driving` render and a
      `rejected` render of the same member, so the diff-aware refresh repaints
      the affected lane. If the existing signature already distinguishes them,
      the test documents it; otherwise fold the parked state into the signature.

## 5. Plugin version bump

- [x] 5.1 [req: board-parked-member-signal] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` (0.6.72 → 0.6.73) so the cached
      plugin snapshot picks up the board change on `claude plugin update`.

## 6. Verify

- [x] 6.1 [req: board-parked-member-signal] Run the full stdlib suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) and the
      textual suite (`python3 -m unittest discover -s
      plugins/s/skills/build/tests_textual`, after `pip install -r
      requirements.txt`); both green.
