## 1. Engine constants and path helpers

- [x] 1.1 [req: prd-store-format, prd-tier-registry] Add PRD tests to
      `plugins/s/skills/build/tests/test_spec_common.py`: `PRD_STATUSES` is
      `("draft", "approved", "superseded")`; `PRD_TEMPLATE_TIERS` is
      `("basic", "standard", "comprehensive")`; `PRD_TIER_SECTIONS` maps every
      tier to a complete tuple and nests additively (assert
      `set(basic) < set(standard) < set(comprehensive)` and the exact
      house-style section lists from the plan); `PRD_METADATA_KEYS` is
      `("Initiative",)`; `prds_dir`/`prd_path` build
      `<ws>/<content-dir>/prds/<slug>/prd.md` honoring a configured content
      dir; `resolve_prd` finds a PRD hosted by a chain member and returns
      `None` when nothing resolves. Run the new tests and observe them fail.
- [x] 1.2 [req: prd-store-format, prd-tier-registry] In
      `plugins/s/skills/build/scripts/spec_common.py`, add a PRD block beside
      the workspace-content block (near line 1267): the four constants and
      the `prds_dir`, `prd_path`, and `resolve_prd` helpers, `resolve_prd`
      following `resolve_initiative_brief`'s chain walk. Confirm the tests
      from 1.1 pass.

## 2. Linter

- [x] 2.1 [req: prd-lint-mode, prd-store-format, prd-tier-registry] Add PRD
      tests to `plugins/s/skills/build/tests/test_spec_lint.py`, driving both
      `lint_prd` directly and the CLI `--prd` mode against temp workspaces:
      a conforming PRD per tier lints clean (exit 0); title/directory
      mismatch, unknown `Status:`, missing `Template:` line, unknown
      `Template:` value, unrecognized metadata key, unresolvable
      `Initiative:`, and a missing tier section each produce one finding
      naming the PRD path; a `basic` PRD is not held to `standard` sections;
      extra sections pass; `--prd` from a root with no discoverable
      workspace exits non-zero with the no-workspace error; a malformed PRD
      in the workspace leaves the flagless library lint unaffected. Run the
      new tests and observe them fail.
- [x] 2.2 [req: prd-lint-mode] In
      `plugins/s/skills/build/scripts/spec_lint.py`, add `lint_prd(ws_root,
      slug, errors)` beside `lint_initiative` (near line 805) implementing
      the plan's grammar and tier-section walk, and wire a `--prd <slug>`
      parser flag and dispatch branch mirroring `--initiative`
      (`sc.find_workspace_root`, the no-workspace error, target label
      `prd '<slug>'`). Update the module docstring's CLI usage line to
      include `[--prd <slug>]`. Confirm the tests from 2.1 pass.

## 3. Version and verification

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` `version` from
      `0.6.189` to `0.6.190`.
- [x] 3.2 [req: *] Run the full engine suite
      (`python3 -m unittest discover plugins/s/skills/build/tests`) and
      confirm it passes.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 61 | 11.1k |
| Edit | 9 | 5.4k |
| Read | 20 | 807 |
| Agent | 2 | 728 |
| (no tool) | 0 | 131 |
| Monitor | 1 | 17 |
| ToolSearch | 1 | 6 |
| **Total** | 94 | 18.2k |
