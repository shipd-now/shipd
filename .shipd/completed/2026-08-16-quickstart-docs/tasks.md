## 1. Quickstart

- [x] 1.1 [req: quickstart-doc] Write `docs/quickstart.md`: install
      (copying the exact command from the README's merged install-mode
      section), `shipd doctor`, `/s:onboard`, a first `/s:plan <change>` →
      `/s:build` in the reader's own repository, and `shipd board` /
      `shipd status` — one short section per step with the exact command.

## 2. README restructure

- [x] 2.1 [req: readme-displays-the-auto-mikk-banner] In `README.md`, add
      the short what-it-is introduction directly under the shipd banner
      (at most a few sentences), before any install content.
- [x] 2.2 [req: readme-retains-onboarding-content, quickstart-doc] Reorder
      `README.md` newcomer-first: banner + intro, install section (content
      as shipped by `public-install`), the `docs/quickstart.md` link, the
      Skills table, then the existing engine internals (spec layout,
      lifecycle, `shipd` CLI, statusline, telemetry) unchanged in content.
- [x] 2.3 [req: readme-catalogs-the-plugin-s-skills] Audit the Skills table
      against `plugins/s/skills/*/SKILL.md` frontmatter: every current
      skill listed with `/s:<name>` and a consistent description, no stale
      entries.

## 3. Verify

- [x] 3.1 [req: *] Re-read `README.md` and `docs/quickstart.md` end to end
      confirming every named command exists as documented in the merged
      repo (`install.sh`, `shipd doctor`, `/s:onboard`, `/s:plan`,
      `/s:build`, `shipd board`, `shipd status`); fix any drift found.
