## 1. Contract test

- [x] 1.1 [req: init-wizard-steps] In
      `plugins/s/skills/build/tests/test_init_skill_contract.py`, replace the
      `self.assertIn("AskUserQuestion", self.skill)` line in
      `test_both_texts_carry_the_vocabulary` with a new test method
      `test_wizard_uses_one_settings_sheet` that asserts: both `self.skill`
      and `self.body` contain `settings sheet` and `Already set (kept):`;
      `self.skill` contains `3 draft, 7 false`; neither contains
      `one key per`. Run
      `python3 -m unittest plugins/s/skills/build/tests/test_init_skill_contract.py`
      and observe the new test fail.

## 2. The skill

- [x] 2.1 [req: init-wizard-steps, init-constitution-starter] In
      `plugins/s/skills/init/SKILL.md`, change the intro sentence "You ask one
      question per key and write each answer through `shipd config set`." to
      "You show every key on one settings sheet, take one typed reply, and
      write each answer through `shipd config set`."
- [x] 2.2 [req: init-wizard-steps, init-constitution-starter] In
      `plugins/s/skills/init/SKILL.md` section `## 3. The wizard`, replace the
      opening "Ask one key per AskUserQuestion…" paragraph with the settings
      sheet rules from `plan.md` `## Implementation` and the change's
      `artefacts/settings-sheet.md`: print one settings sheet as plain response
      text, open no AskUserQuestion, and end the turn. Embed the artefact's
      fresh-project sheet verbatim in a `text` code block. Keep the key table
      and add a column for each key's sheet gloss, copied from the artefact.
      Add the reply grammar bullets, the `Already set (kept):` block rule,
      the section-run numbering rule, and the one re-print then stop rule,
      all copied from the artefact.
- [x] 2.3 [req: init-wizard-steps] In the same section, rewrite the
      **Detect what is set** paragraph: set keys go in the
      `Already set (kept):` block with their provenance and get no line
      number; "nothing left to set up" prints when no numbered line remains.
- [x] 2.4 [req: init-wizard-steps] In the same section, rewrite the
      **Write each answer** paragraph and its two bullets: write `dir` and
      `store_root` first, then run `spec_status.py init`, then the config keys
      in sheet order, then the constitution; collect `config set` exit-1
      failures, relay their `error:` and `hint:` lines, and print one retry
      sheet with only the failed lines plus any other key an `error:` line
      names, written first; skip a second failure with a note and never print
      a second retry sheet.
- [x] 2.5 [req: init-constitution-starter] In the same section, rewrite the
      **The constitution (step 5)** paragraph so the starter is the sheet's
      `constitution` line (`add` | `skip`), present only in the bare wizard
      and only when `<content_dir>/constitution.md` is absent; keep the
      `cp -n` block unchanged.
- [x] 2.6 [req: init-wizard-steps] In the same section, replace the
      **Brief every question** paragraph with: "The sheet's gloss column is
      the brief for each key. The `workspace` section's single path dialog
      still follows
      `${CLAUDE_PLUGIN_ROOT}/skills/document/references/question-brief.md`."
- [x] 2.7 [req: init-wizard-steps] In `plugins/s/skills/init/SKILL.md`
      step 1, change "**While `unattended` is true, open no dialog**" to
      "**While `unattended` is true, print no sheet and open no dialog**".

## 3. The harness body

- [x] 3.1 [req: init-wizard-steps, init-constitution-starter] In
      `plugins/s/harness/bodies/init.md`, rewrite steps 3–6 to match task
      group 2: one settings sheet (name `Already set (kept):`, the reply forms
      `ok` and `<n> <value>`, the write order, the one retry sheet, the
      constitution line). Replace the closing **Brief every question**
      paragraph with the sentence from task 2.6, using
      `plugins/s/skills/document/references/question-brief.md` as the path
      (written in the body without the `plugins/s/` prefix). Keep every
      token `test_both_texts_carry_the_vocabulary` checks.

## 4. README and version

- [x] 4.1 [req: init-wizard-steps] In `README.md` line 263, change "a guided
      first-run wizard that asks one question per setting (where files live,
      how changes ship, personal stores, session behaviour)" to "a first-run
      wizard that shows every setting on one numbered sheet (where files
      live, how changes ship, personal stores, session behaviour), accepts
      them with `ok` or changes lines like `3 draft`".
- [x] 4.2 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json`
      one patch above the version the main branch carries.

## 5. Verify

- [x] 5.1 [req: *] Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` and
      confirm it reports `OK`, including
      `test_wizard_uses_one_settings_sheet`.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 15 | 8.3k |
| SubagentHandback | 2 | 2.4k |
| Agent | 2 | 793 |
| (no tool) | 0 | 260 |
| Monitor | 1 | 76 |
| **Total** | 20 | 11.8k |
