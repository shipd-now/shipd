## 1. Test and hygiene

- [x] 1.1 [req: cli-dispatch] In
      `plugins/s/skills/build/tests/test_shipd_cli.py`, rewrite
      `test_retired_html_mode_falls_through_to_the_interactive_delegate`
      (~line 209) as
      `test_unknown_board_mode_word_falls_through_to_the_interactive_delegate`:
      run `shipd board frobnicate --once`, assert exit `2` and
      `unrecognized arguments` on stderr; remove the `board.html` out-path,
      the `--out` argument, the file-not-written assertion, and every `html`
      mention in the test body and its comment. Run
      `python3 -m unittest tests.test_shipd_cli` from
      `plugins/s/skills/build` and confirm it passes.
- [x] 1.2 [req: board-tui, board-shipd-theme] Verify the staged spec sweep:
      extract the `board-tui` and `board-shipd-theme` requirement blocks from
      `.shipd/verified/delivery-dashboard/spec.md` and diff each against its
      block in
      `.shipd/planned/purge-html-mentions/specs/delivery-dashboard/spec.md`
      (ignoring the added `base:` line) — the only differences must be
      "(so `board` and `html` also work)" → "(so `board` also works)" and the
      deleted "(the `html` verb's separate inline page CSS is exempt)"
      parenthetical; then confirm `grep -in html` over both delta files and
      the delta in `specs/shipd-cli/spec.md` returns nothing.
- [x] 1.3 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json`
      from `0.6.108` to `0.6.109` (plugin-cache rule in `AGENTS.md`); if the
      merged base has already advanced past `0.6.108`, bump from the current
      value instead.
- [x] 1.4 [req: *] Sweep the two live epic references: in
      `.shipd/epics/update-ui-look-feel/epic.md` (Non-goals, ~line 45) delete
      the sentence "The `html` verb's static page is out of scope." — keeping
      the preceding `.dc.html` mock sentence, which names a design-mock file,
      not the board feature; in `.shipd/epics/shipd-dx/epic.md` (Non-goals,
      ~line 49) delete the clause "; the board's existing `html` verb is
      unchanged" so the sentence ends at "(the port epic also deferred the
      site)." Reflow the touched bullets to the surrounding wrap width.
- [x] 1.5 [req: *] From `plugins/s/skills/build`, run
      `python3 -m unittest discover -s tests` and
      `python3 -m unittest discover -s tests_textual`; both must pass. Then
      from the worktree root run
      `grep -rn html --include="*.md" --include="*.py" --include=shipd . |
      grep -v "^\./\.shipd/completed/\|^\./\.git/\|^\./\.shipd/planned/"` and
      confirm every remaining match is one of the allowed unrelated classes
      named in plan.md (GitHub `html_url` fields, `semdiff.py`'s `.html`
      extension mapping, external URLs in `.shipd/research/` reports, and the
      `.dc.html` design-mock mention in `update-ui-look-feel/epic.md`);
      `.shipd/epics/` must otherwise be clean after task 1.4.
