# board-stall-buttons
Status: verified

## Idea

Restyle the delivery board's action controls into the Shipd mock's two-tier
button hierarchy and redesign the epic-detail stall banner as the mock's
tinted accent-bar error panel with resume-safe retry copy.

### Motivation

The stall banner still renders as a solid error-red block with white text and
a default-styled Retry, and the board's buttons carry ad-hoc accent tints,
while the "Shipd Board TUI" design mock specifies a calmer tinted banner with
a red accent bar and a solid-accent primary / elevated-secondary control
hierarchy. This lands the mock's look for the buttons and the stalled/error
message on the `update-ui-look-feel` epic.

### Details

- Two shared button tiers in `BoardApp.CSS`: `.button-primary` (solid
  `$primary`, `$background` text, bold) and `.button-secondary` (`$bg-hover`
  background, `$fg-muted` text) — applied to the stall banner's Retry
  (primary) and the epic-run confirmation's Yes (primary) / No (secondary).
- Segmented grouping control: `.mode-active` becomes a solid accent block
  with dark bold text; inactive `.mode-button`s sit on `$bg-hover` with
  `$fg-muted` text.
- Modal accent title-bar `✕` closes render as dark glyphs on the accent bar
  itself (`$accent` background, `$background` glyph) instead of a
  `$primary 25%` chip.
- Stall banner redesign in `EpicDetailScreen`: an `$error 10%` tinted panel
  with a one-cell solid `$error` bar down its left edge; rows top to bottom —
  bold error-colored `STALLED` with a right-aligned muted parked summary, one
  line per parked member (slug, muted stage, reason as a `$warning`-on-tint
  chip), a muted reassurance line, and an action row with the primary
  `Retry run` button plus a right-aligned subtle `parked <age> ago` label
  from the heartbeat's `updated_at`.
- Drop the then-unused `shipd-on-error` theme variable.

Affected capabilities: `delivery-dashboard` (modified). Impact:
`plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests_textual/test_dashboard.py`,
`plugins/s/.claude-plugin/plugin.json` (version bump); no new dependencies.

### Non-goals

- No "View log" control on the banner — Retry stays the banner's only action
  (user decision).
- No board-level "● N stalled" header chip — that belongs to the filter
  strip's `board-filters` member.
- No changes to stall detection, retry dispatch, diff-aware refresh, or any
  aggregation semantics — this is presentation only.
- No new theme colors: every style resolves existing `SHIPD_THEME` variables.

## Implementation

- **Banner structure.** `#epic-stall-banner` becomes a
  `Horizontal(id="epic-stall-banner")` holding a one-cell
  `Static("", classes="stall-accent-bar")` (`width: 1; background: $error`)
  and a `Vertical(classes="stall-body")` with the content rows; the banner
  container carries `background: $error 10%; height: auto; margin: 0 0 1 0`
  and the body `padding: 0 1`. Rejected: a `border-left` on the banner —
  textual edge borders draw box glyphs, not a guaranteed solid cell, while a
  background-filled Static is deterministic.
- **Row composition and classes** (all colors via theme variables):
  - Header `Horizontal`: `Static("STALLED", classes="stall-title")`
    (`color: $text-error; text-style: bold; width: auto`) and
    `Static("%d member(s) parked · needs-human" % len(parked), classes="stall-summary")`
    (`width: 1fr; text-align: right; color: $fg-muted`).
  - Per parked member a `Horizontal(classes="stall-member-row")`: slug
    `Static` in the default foreground (`width: auto`), stage `Static`
    (`color: $fg-muted; margin: 0 0 0 2; width: auto`), reason
    `Static(classes="stall-reason-chip")`
    (`color: $warning; background: $warning 10%; padding: 0 1; margin: 0 0 0 2; width: auto`).
    Stage falls back to `?` and reason to `""` exactly as today.
  - `Static(_STALL_NOTE, classes="stall-note")` (`color: $fg-muted`) with the
    module constant `_STALL_NOTE = "Safe to retry — every step is
    checkpointed, so the run resumes from the last durable state. Nothing
    runs twice."` — verified against `autopilot.py`: `_entry_stage` re-enters
    each member at its first unsatisfied stage and non-unplanned members are
    skipped, so the claim is accurate.
  - Action `Horizontal`: `Button("Retry run", id="epic-retry",
    classes="button-primary")` (id and `on_button_pressed` wiring unchanged)
    and `Static(_age(hb.get("updated_at"), verb="parked"),
    classes="stall-age")` (`width: 1fr; text-align: right; color: $fg-subtle`),
    where `hb` is the epic's heartbeat dict.
- **`_age` grows a verb parameter.** `_age(updated_at, verb="updated")`
  formats `"<verb> %ds/%dm/%dh ago"` and the missing-timestamp fallback
  `"<verb> ?"`; every existing call site keeps its behavior via the default.
  Rejected: string-replacing the prefix at the call site — fragile against
  the fallback shape.
- **Button tier CSS** in `BoardApp.CSS`:
  `.button-primary { background: $primary; color: $background; text-style: bold; height: 1; border: none; padding: 0 2; width: auto; min-width: 0; }`
  with `:hover { background: $accent-dim; }`;
  `.button-secondary { background: $bg-hover; color: $fg-muted; height: 1; border: none; padding: 0 2; width: auto; min-width: 0; }`
  with `:hover { background: $bg-active; }`. `EpicRunConfirmScreen.compose`
  tags Yes `button-primary` and No `button-secondary`.
- **Segmented control.** `.mode-button` gains
  `background: $bg-hover; color: $fg-muted;`; `.mode-active` becomes
  `background: $primary; color: $background; text-style: bold;`.
- **Title-bar closes.** A `BoardApp.CSS` (and matching modal-CSS where the
  title bar is styled per-screen) override
  `.modal-title-bar .compact-button { background: $accent; color: $background; }`
  with `:hover { background: $accent-dim; }`. Non-title-bar compact buttons
  (search clear, group-header `▶`/`≡`) keep today's `$primary 25%` tint.
- **Theme cleanup.** Remove `shipd-on-error` from `SHIPD_THEME.variables`
  once its lone consumer (the white-on-red banner) is gone; no other
  reference exists.
- **Tests.** `tests_textual/test_dashboard.py` is amended in place following
  the suite's convention of resolving expected colors through
  `app.get_css_variables()`; the literal white-rgb, three-cell-inset
  geometry, and blank-header-row assertions are removed with the design that
  mandated them. Where 10%-alpha backgrounds make blended-rgb assertions
  brittle, tests assert the declared style (color with alpha / class
  presence) rather than a blended literal.
- **Risk:** the run-confirm Yes/No restyle must not change button ids or the
  dispatch wiring — assertions on `epic-run-yes`/`epic-run-no` behavior stay
  untouched, and the existing behavioral tests guard this.
- **Version bump** owed by the cache-snapshot rule:
  `plugins/s/.claude-plugin/plugin.json` `0.6.56` → `0.6.57`.
