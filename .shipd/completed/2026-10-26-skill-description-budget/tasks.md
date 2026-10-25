## 1. Before reading

- [x] 1.1 [req: skill-description-budget] Before any edit, make
      `<scratch>` with `mktemp -d` and an empty `<scratch>/run` directory.
      From `<scratch>/run`, run `claude -p "/context" --output-format json
      --max-turns 1 --plugin-dir "<worktree>/plugins/s" --settings
      '{"enabledPlugins":{"s@shipd":false}}'`, with `<worktree>` the
      worktree's absolute path, confirm exit 0, and save its `result` field
      to `<scratch>/before.md`. Check that its per-skill table lists the
      `s:*` skills exactly once each with Source "Plugin (s)"; if they
      appear twice or not at all, stop and report.
- [x] 1.2 [req: skill-trigger-phrases-kept] Write each skill's current
      trigger phrases to `<scratch>/phrases-before.json` (a map of skill name
      to the list of quoted phrases after `Trigger phrases:` in its folded
      `description`), using the folding rule in plan.md's "Reading the
      description" bullet.

## 2. Budget test

- [x] 2.1 [req: skill-description-budget, skill-description-shape] Create
      `plugins/s/skills/build/tests/test_skill_descriptions.py` per plan.md's
      "Test" bullet: `DESCRIPTION_BUDGET = 300`, a `folded_description(path)`
      helper, `test_every_description_is_within_budget`,
      `test_every_description_is_the_body_one_liner_plus_triggers`, and a
      fixture-text test that a 301-character description is reported with its
      skill name and length. Run `python3 -B -m unittest discover -s
      plugins/s/skills/build/tests -p 'test_skill_descriptions.py'` and see
      the two checkout tests fail.

## 3. Trim the descriptions

- [x] 3.1 [req: skill-description-shape, skill-trigger-phrases-kept] For
      each of the 31 `plugins/s/skills/*/SKILL.md`, replace the frontmatter
      `description: >-` block with a new `description: >-` block whose
      folded text is the skill's `plugins/s/harness/bodies/<name>.md`
      one-liner, a space, and the skill's current `Trigger phrases:` clause
      copied verbatim. Wrap the block's lines at 80 columns with two-space
      indent, as today. Edit nothing else in any SKILL.md.
- [x] 3.2 [req: skill-description-budget, skill-description-shape] Run
      `python3 -B -m unittest discover -s plugins/s/skills/build/tests -p
      'test_skill_descriptions.py'` and confirm it passes.
- [x] 3.3 [req: skill-trigger-phrases-kept] Recompute the phrase map from
      the edited files and compare it with `<scratch>/phrases-before.json`;
      stop and report if any skill's set differs.
- [x] 3.4 [req: skill-description-budget] Bump the patch version in
      `plugins/s/.claude-plugin/plugin.json` to one above the value on
      origin/main.

## 4. After reading

- [x] 4.1 [req: skill-description-budget] Once the edits are done, run
      task 1.1's exact `/context` command (same `--plugin-dir` and
      `--settings`) from `<scratch>/run` and save its `result` field to
      `<scratch>/after.md`. Check that the `s:*` skills appear exactly once
      each with Source "Plugin (s)"; if they appear twice or not at all,
      stop and report. Apply the gain check in plan.md's "Live proof"
      bullet: pass when no `s:*` row in the after table reads `< 20`
      tokens, or when the Skills category total is lower than before. If
      it fails, stop here and report both readings.
- [x] 4.2 [req: skill-description-budget] Write to `<scratch>/readings.md`,
      for the PR body: both `/context` readings, the Skills category total
      before and after, the `s:*` rows at `< 20` tokens in each, the
      gain-check verdict, and the total folded description characters
      before and after. Change no budget or ceiling file.

## 5. Docs and verification

- [x] 5.1 [req: skill-description-budget] In `AGENTS.md`, directly after
      the bullet that starts "**Every change touching `plugins/s/` bumps the
      plugin version**", add one bullet: a skill's `description` is its
      harness body one-liner plus its `Trigger phrases:` clause, at most 300
      folded characters, enforced by
      `plugins/s/skills/build/tests/test_skill_descriptions.py`.
- [x] 5.2 [req: *] Run every `python3 -m unittest discover -s <dir>` line in
      `.github/workflows/ci.yml` and grep each output for `OK`; fix any test
      that asserted removed description text by checking the token is still
      in the skill body, never by restoring the long description.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 111 | 48.3k |
| SubagentHandback | 4 | 4.6k |
| Agent | 5 | 2.7k |
| (no tool) | 0 | 1.2k |
| Skill | 3 | 902 |
| Monitor | 3 | 758 |
| ToolSearch | 2 | 423 |
| SendMessage | 1 | 274 |
| ListAgents | 1 | 110 |
| **Total** | 130 | 59.3k |
