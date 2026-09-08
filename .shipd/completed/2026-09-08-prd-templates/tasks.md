## 1. Drift-guard first

- [x] 1.1 [req: prd-template-files] Add
      `plugins/s/skills/build/tests/test_prd_templates.py`: resolve the
      templates dir relative to the test file
      (`…/tests/../../prd/references`); for each tier in
      `sc.PRD_TEMPLATE_TIERS` assert the file `<tier>.md` exists, its `## `
      heading lines in document order equal `sc.PRD_TIER_SECTIONS[tier]`
      exactly, its `Template:` line names the tier, line 1 starts with `# `,
      and its `Status:` line says `draft`; assert the directory holds no
      other `.md` files; and fill a temp-workspace PRD from `basic.md`
      (title placeholder → directory slug, guidance lines → plain text) and
      assert `spec_lint.lint_prd` appends no errors. Run the module and
      observe every test fail — the templates do not exist yet.

## 2. Templates

- [x] 2.1 [req: prd-template-files] Under `plugins/s/skills/` create the new
      `prd/references/` directory holding the three templates — `basic.md`,
      `standard.md`, and `comprehensive.md` — per the plan's skeleton shape:
      `# <prd-slug>` placeholder title, `Status: draft`,
      `Template: <tier>`, blank line, then the tier's registry sections in
      order, each heading followed by one italic single-line guidance
      sentence describing what the `/s:prd` interview must establish there
      (problem/why-now, proposed solution, measurable success criteria,
      affected users, concrete requirements, explicit exclusions, risks and
      mitigations, rollout approach, unresolved questions — matched to the
      section). Confirm the tests from 1.1 pass.

## 3. Version and verification

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` `version`
      from `0.6.190` to `0.6.191`, then run
      `claude plugin validate plugins/s` and confirm it passes with the new
      `skills/prd/references/` directory present.
- [x] 3.2 [req: body-templates] In
      `plugins/s/skills/build/tests/test_harness_bodies.py`, narrow
      `ShippedTemplateTest.test_every_command_has_exactly_one_body_template`'s
      skill enumeration to directories under `plugins/s/skills/` that contain
      a `SKILL.md` file, with a docstring note that a skill-less directory
      (e.g. `prd/references/` shipped ahead of its skill) is not a command.
      Touch nothing in `harness_bodies.py`. Run the module and confirm it
      passes with `skills/prd/` present.
- [x] 3.3 [req: *] Run the full engine suite
      (`python3 -m unittest discover plugins/s/skills/build/tests`) and
      confirm it passes.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 58 | 12.8k |
| Read | 10 | 901 |
| SendMessage | 1 | 633 |
| Agent | 2 | 555 |
| (no tool) | 0 | 275 |
| ToolSearch | 1 | 162 |
| Write | 5 | 47 |
| Edit | 2 | 34 |
| **Total** | 79 | 15.4k |
