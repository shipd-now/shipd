## 1. Installer notice

- [x] 1.1 [req: install-script] Add failing tests to
      `plugins/s/skills/build/tests/test_install.py`: a successful
      `install.sh` run prints the auto-update notice (the `/plugin`
      marketplace toggle for `shipd`, the `"autoUpdate": true` settings
      alternative, the next-launch apply note) and touches no file under
      the temp HOME's `.claude/` beyond what the stub `claude` writes; the
      missing-`claude` abort prints no notice.
- [x] 1.2 [req: install-script] Implement the notice in `install.sh` on the
      success path (plain stdout, POSIX sh, after the PATH hint). Run the
      1.1 tests green.

## 2. Docs

- [x] 2.1 [req: install-mode-docs] In `README.md`'s install-mode section,
      add the auto-update paragraph: the `/plugin` → Marketplaces → `shipd`
      toggle, the `"autoUpdate": true` settings entry form, apply semantics
      (next session start, or `/reload-plugins`), and
      `claude plugin update s@shipd` as the manual fallback.
- [x] 2.2 [req: install-mode-docs] Add the same enable step, condensed, to
      `docs/quickstart.md`'s install step.

## 3. Doctor hint and settings default

- [x] 3.1 [req: install-mode-docs] In `plugins/s/bin/shipd`, extend the
      stale-`snapshot` warn detail to name enabling marketplace
      auto-update alongside `claude plugin update s@shipd` (the check's
      semantics, levels, and exit contract unchanged); update the pinned
      hint assertion in
      `plugins/s/skills/build/tests/test_shipd_cli.py`.
- [x] 3.2 [req: install-mode-docs] Add `"autoUpdate": true` to the `shipd`
      entry under `extraKnownMarketplaces` in `.claude/settings.json`.

## 4. Ship

- [x] 4.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` to the next free number.
- [x] 4.2 [req: *] Run `plugins/s/skills/build/tests/` with no `textual`
      installed; green.
