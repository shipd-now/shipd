## ADDED Requirements

### Requirement: Board scrollbar theme
id: board-scrollbar-theme

The registered `shipd` theme SHALL pin the scrollbar palette to the design
system's muted border tones by exposing scrollbar theme variables that
override textual's accent-derived defaults: the thumb (`scrollbar`)
`#3E3E52`, the hover and active thumb states `#55556A`, and the track,
track-hover, track-active, and corner (`scrollbar-background`,
`scrollbar-background-hover`, `scrollbar-background-active`,
`scrollbar-corner-color`) `#1C1C26`. While the `shipd` theme is active, no
scrollbar color SHALL derive from the theme's primary/accent color.

#### Scenario: Scrollbar variables resolve the muted tones
- **WHEN** the `shipd` theme's CSS variables are resolved on the running app
- **THEN** `scrollbar` resolves `#3E3E52`, `scrollbar-hover` and
  `scrollbar-active` resolve `#55556A`, and `scrollbar-background`,
  `scrollbar-background-hover`, `scrollbar-background-active`, and
  `scrollbar-corner-color` resolve `#1C1C26`

## MODIFIED Requirements

### Requirement: Board modal chrome
id: board-modal-chrome
base: 3dbb6bbd8c6a

The board's three modals — the spec-detail, epic-detail, and epic-run
confirmation screens — SHALL each carry a one-row **accent title bar**: a band
in the theme's accent color spanning the modal's top, naming the modal's
subject (the member's slug, the epic's slug, or the epic run being confirmed)
in a contrasting foreground, with the compact `✕` close control inline at the
bar's right edge (unchanged in size and behavior). Below the title bar the
spec-detail modal SHALL show a **badge meta row** of theme-tinted chips — a
risk chip colored through the theme's risk variables **only when the member
carries a risk rating** (an unrated member's row renders no placeholder risk
chip), a lane chip colored through the member's lane variable, while the
member is being driven a live-stage chip in the muted tier, and the epic
reference — and the epic-detail modal SHALL show a status chip plus theme and
initiative chips when set. The epic-detail modal's member rows SHALL each
carry a **lane badge** colored through the theme variable of that member's
lane, derived by the same lane derivation the board's lanes use. The
spec-detail modal's artifact **tab strip** SHALL be themed through theme
variables — the active tab in the accent, inactive tabs in the muted tier —
and every modal SHALL carry a one-row muted **footer key-hint line** at its
bottom naming that modal's keys. While a detail modal is open, `y` SHALL copy
the modal's subject slug via the app clipboard, and `j`/`k` SHALL scroll the
modal's content pane down/up; in the spec-detail modal `Tab` SHALL activate
the next artifact tab, wrapping past the last. When `o` is pressed in a
detail modal, the app SHALL open that modal's artifact — the spec-detail
modal's active tab file, the epic-detail modal's `epics/<slug>/epic.md` — in
the user's editor as a **suspend launch** built by a pure builder returning
`{"mode": "suspend", "argv": [<editor>, <path>], "cwd": <the file's
directory>}`, with the editor resolved from `$EDITOR` and falling back to
`vi`. If the modal has no such artifact on disk, then `o` SHALL be a no-op.
All new modal chrome SHALL reference colors only through `$` theme variables
(see the Board theme requirement).

#### Scenario: Modals carry an accent title bar with inline close
- **GIVEN** the spec-detail, epic-detail, or epic-run confirmation modal
- **WHEN** the modal opens
- **THEN** its top row is an accent-background title bar naming the modal's
  subject, with the compact `✕` close control inline at the bar's right edge

#### Scenario: The spec-detail modal shows a badge meta row
- **GIVEN** a member with a risk rating being driven through a stage
- **WHEN** its spec-detail modal opens
- **THEN** a badge row below the title bar shows a risk chip colored by the
  member's risk, a lane chip colored by the member's lane, a muted live-stage
  chip, and the epic reference

#### Scenario: An unrated member's modal omits the risk chip
- **GIVEN** a member carrying no risk rating
- **WHEN** its spec-detail modal opens
- **THEN** the badge row renders no risk chip and no `?` placeholder — its
  first chip is the member's lane chip

#### Scenario: The epic-detail modal shows status, theme, and initiative chips
- **GIVEN** an epic with a theme and an initiative
- **WHEN** its epic-detail modal opens
- **THEN** a badge row below the title bar shows the epic's status chip and
  chips naming its theme and initiative

#### Scenario: Epic member rows carry lane badges
- **GIVEN** an open epic-detail modal listing the epic's member specs
- **WHEN** the member rows render
- **THEN** each row carries a badge colored through the theme variable of the
  lane the board's own lane derivation assigns that member

#### Scenario: The artifact tab strip is accent-themed
- **WHEN** the spec-detail modal's artifact tabs render
- **THEN** the active tab is styled with the accent and inactive tabs with the
  muted tier, with every color a `$` theme variable

#### Scenario: Each modal shows its footer key hints
- **GIVEN** the spec-detail, epic-detail, or epic-run confirmation modal
- **WHEN** the modal opens
- **THEN** a one-row muted key-hint line at the modal's bottom names that
  modal's keys

#### Scenario: y copies the modal's subject slug
- **GIVEN** an open spec-detail modal (or epic-detail modal)
- **WHEN** `y` is pressed
- **THEN** the member's slug (or the epic's slug) is copied via the app
  clipboard

#### Scenario: Tab cycles the artifact tabs
- **GIVEN** an open spec-detail modal with more than one artifact tab
- **WHEN** `Tab` is pressed repeatedly
- **THEN** the active tab advances through the artifact tabs, wrapping from
  the last back to the first

#### Scenario: j and k scroll the modal content
- **GIVEN** an open detail modal whose content overflows its pane
- **WHEN** `j` then `k` is pressed
- **THEN** the content pane scrolls down then back up

#### Scenario: o opens the active artifact in the editor
- **GIVEN** an open spec-detail modal showing artifact tabs
- **WHEN** `o` is pressed
- **THEN** a suspend launch is spawned whose argv is the resolved editor
  followed by the active tab's file path

#### Scenario: o without an artifact is a no-op
- **GIVEN** an open spec-detail modal showing the not-yet-planned notice
- **WHEN** `o` is pressed
- **THEN** no launch is spawned and the modal stays open

#### Scenario: The editor launch builder is pure and falls back to vi
- **GIVEN** an environment where `$EDITOR` is unset
- **WHEN** the editor launch builder is called with an artifact path
- **THEN** it returns `{"mode": "suspend", "argv": ["vi", <path>], "cwd":
  <the file's directory>}` without spawning anything, and with `$EDITOR` set
  it uses that editor instead
