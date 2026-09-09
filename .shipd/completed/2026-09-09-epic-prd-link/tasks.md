## 1. Engine

- [x] 1.1 [req: epic-header-metadata] Add tests: in
      `plugins/s/skills/build/tests/test_spec_common.py` assert
      `EPIC_METADATA_KEYS == ("Theme", "Initiative", "PRD")`; in
      `plugins/s/skills/build/tests/test_spec_lint.py` (temp workspace
      fixtures) assert an epic carrying `PRD: <slug>` with the PRD hosted by
      a chain member lints clean via `--epic`; an unresolvable `PRD:` errors
      naming the expected `prd.md` path; a non-kebab `PRD:` value errors; an
      epic without the line lints exactly as before; `Profile:` remains
      rejected. In `plugins/s/skills/build/tests/test_spec_status.py` assert
      `epic-show` renders the `PRD` metadata line for an epic carrying one.
      Run the new tests and observe them fail.
- [x] 1.2 [req: epic-header-metadata] In
      `plugins/s/skills/build/scripts/spec_common.py` extend
      `EPIC_METADATA_KEYS` to `("Theme", "Initiative", "PRD")`; in
      `plugins/s/skills/build/scripts/spec_lint.py` add
      `check_prd_reference(root, pairs, errors)` beside
      `check_initiative_reference` per the plan (resolve via
      `sc.resolve_prd`, error naming the expected path or the missing
      workspace) and call it from `lint_epic` directly after
      `check_initiative_reference`. Confirm the tests from 1.1 pass.

## 2. Documentation surfaces

- [x] 2.1 [req: epic-header-metadata] Update every enumeration of the epic
      metadata keys to include the optional `PRD: <kebab-prd>` line (noting
      it must resolve to a workspace PRD): the metadata bullet near
      `.shipd/README.md:753`; the epic contract bullet near
      `plugins/s/skills/epic/SKILL.md:375` and that skill's emission
      template header block; and `plugins/s/harness/references/epic.md`
      (template header lines 8-9 and the contract sentence near line 53).

## 3. Version and verification

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` `version` to
      the next free patch (0.6.196 if main still sits at 0.6.195).
- [x] 3.2 [req: *] Run the full engine suite
      (`python3 -m unittest discover plugins/s/skills/build/tests`) and
      confirm it passes.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 73 | 20.2k |
| Edit | 21 | 6.1k |
| (no tool) | 0 | 2.5k |
| Read | 23 | 2.3k |
| Agent | 2 | 707 |
| SendMessage | 1 | 497 |
| **Total** | 120 | 32.2k |
