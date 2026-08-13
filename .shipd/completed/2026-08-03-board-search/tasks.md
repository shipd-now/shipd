## 1. Pure search helpers

- [x] 1.1 [req: board-search] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add a pure
      test class for two new `dashboard` helpers: `_search_matches(query,
      epic_slug, initiative, member_slug)` — True on a case-insensitive
      substring hit in any of the three fields, True for an empty or
      whitespace query, False otherwise (a None initiative never matches) —
      and `_highlight_slug(slug, query)` — returns the slug with the first
      case-insensitive matched span wrapped in `[$accent]…[/]`, and the slug
      unchanged for an empty query or no match. Run the class and observe it
      fail.
- [x] 1.2 [req: board-search] In
      `plugins/s/skills/build/scripts/dashboard.py`, implement
      `_search_matches` and `_highlight_slug` as module-level helpers beside
      `_lane_contents`/`_lane_signature`, exactly per 1.1's contract. Confirm
      1.1 passes.

## 2. Signature folds the query

- [x] 2.1 [req: board-search] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, extend the
      `_lane_signature` tests: equal for an unchanged board when the same
      `search_query` is passed; differs when only the query changes. Update
      every existing `_lane_signature(...)` call in the suite to the new
      three-argument form (`cards, group_by_epic, search_query`). Run and
      observe the new assertions fail.
- [x] 2.2 [req: board-search] In `dashboard.py`, add the `search_query`
      parameter to `_lane_signature` and fold it into the signature tuple
      alongside `group_by_epic`; update the `_render_lanes` call site to pass
      `self.search_query`. Confirm 2.1 passes.

## 3. Controls-strip search UI

- [x] 3.1 [req: board-search] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add
      pilot-driven app tests against the two-epic fixture board: pressing
      `/` focuses `#board-search-input`; typing a member-slug query mounts
      only matching cards; a query hitting an epic slug (or initiative)
      keeps that epic's members mounted; a slug-matched card's content
      carries the `[$accent]` highlight span; `#board-search-count` shows
      the match count and blanks when cleared; `escape` in the input
      restores all cards; pressing `#board-search-clear` restores all
      cards; with grouping on, an epic with no matching members mounts no
      `epic-group` header in any lane; an unchanged-board refresh under an
      active query retains the same card widget instances. Run and observe
      failures.
- [x] 3.2 [req: board-search] In `dashboard.py`, add a `SearchInput(Input)`
      subclass and mount the search widgets in `BoardApp.compose`'s
      `#controls-strip`: `SearchInput` (id `board-search-input`), a `✕`
      `Button` (id `board-search-clear`, classes `compact-button`), and a
      `Static` match-count label (id `board-search-count`). Add the
      app-level `Binding("slash", "focus_search", "Search", key_display="/")` and
      `action_focus_search` focusing the input, plus
      `BoardApp.search_query = ""` in `__init__` and an
      `on_input_changed` handler (guarded by the input id) that stores the
      value and awaits `_render_lanes()`.
- [x] 3.3 [req: board-search] In `dashboard.py`'s `_render_lanes`, filter
      each lane's `_lane_contents` cards through `_search_matches`
      (initiative resolved via `_find_epic`) before signature computation
      and mounting; thread a `search_query=""` keyword into
      `TaskCard.__init__` and render the slug in `_card_text` through
      `_highlight_slug`; pass the query at both `TaskCard` construction
      sites in `_render_lanes`/`_mount_epic_groups`.
- [x] 3.4 [req: board-search] In `dashboard.py`, finish count and clear:
      `_render_lanes` sets `#board-search-count` to `"%d matches"` (matching
      members across lanes) when the query is non-empty, else `""`; a
      `_clear_search()` helper empties the input's value and refocuses the
      first `TaskCard` when one exists; `SearchInput`'s `escape` binding
      calls it; `BoardApp.on_button_pressed` routes the
      `board-search-clear` id to it before the epic-control marker checks.
      Confirm every 3.1 test passes.

## 4. Verify and ship

- [x] 4.1 [req: *] Run the full `tests_textual` suite (`python3 -m unittest
      discover -s plugins/s/skills/build/tests_textual`) and the stdlib
      suite without `textual` (`python3 -m unittest discover -s
      plugins/s/skills/build/tests`); both must pass — the stdlib suite
      unmodified.
- [x] 4.2 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` from 0.6.39 to 0.6.40.
