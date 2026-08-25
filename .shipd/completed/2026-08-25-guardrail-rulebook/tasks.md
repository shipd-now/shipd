## 1. Rulebook engine — tests first

- [x] 1.1 [req: guardrail-rulebook-format, guardrail-rulebook-discovery] In
      `plugins/s/skills/build/tests/test_guardrails.py`, add rulebook cases:
      a valid rule file loads (name from stem, pattern, message body); a
      `mode: remind` file parses mode and `cooldown: 300`; a file with no
      `pattern`, an empty body, or `mode: interrupt` is skipped while a valid
      sibling loads; a repo `<tmp>/.shipd/rules/changelog-comment.md`
      overrides the built-in by name; a `~/.shipd/rules/no-console-log.md`
      (under the test's isolated HOME) denies in a rules-less repo; config
      `disable` drops a built-in; `guardrails: false` disables all. Rewrite
      the v0.6.152 config-`rules` cases (extend/replace registry) as rulebook
      cases, and add the legacy case: a config object carrying `rules` has
      that member ignored. Run the file and observe the new cases fail.
- [x] 1.2 [req: guardrail-remind-output, guardrail-fail-open] Extend
      `test_guardrails.py` with PostToolUse cases: a `mode: remind` repo rule
      fires `hookSpecificOutput.additionalContext` naming rule and message,
      exit 0; a second identical payload with the same `session_id` prints
      nothing; a deny rule is not evaluated on PostToolUse; a remind rule
      does not deny on PreToolUse; a `cooldown: 1` rule re-fires after the
      cooldown elapses (write the state file's epoch directly rather than
      sleeping); an unwritable state directory still emits the reminder; a
      payload with no `session_id` still fires. Run and observe failure.
- [x] 1.3 [req: guardrail-default-rules] Create
      `plugins/s/hooks/rules/changelog-comment.md`,
      `narrating-comment.md`, and `filler-placeholder.md` — frontmatter
      `pattern:` with the exact patterns from the guardrail-default-rules
      delta (no `mode` line; deny is the default), body = the existing
      messages from `guardrails.py`'s `DEFAULT_RULES`.
- [x] 1.4 [req: guardrail-rulebook-format, guardrail-rulebook-discovery, guardrails-key]
      In `plugins/s/skills/build/scripts/guardrails.py`: add the flat
      frontmatter parser (`---`-delimited, first-colon split) and rule-file
      loader with the skip rules from the delta; replace `DEFAULT_RULES`
      content with loading from the plugin's `hooks/rules/` resolved relative
      to `__file__`; implement the three-source discovery walk (ancestor
      `<content-dir>/rules/` via the resolved config `dir`, then
      `~/.shipd/rules/`, then plugin built-ins) with first-wins name dedup;
      keep config `false` and `disable`, ignore a `rules` member and any
      other unrecognized member. Confirm the 1.1 cases pass.
- [x] 1.5 [req: guardrail-remind-output] In `guardrails.py`: branch on
      `hook_event_name` — PreToolUse evaluates only deny rules (existing deny
      output unchanged), PostToolUse evaluates only remind rules and emits
      the `additionalContext` JSON; add cooldown state at
      `~/.shipd/guardrails/<session_id>.json` (rule name → last-fire epoch),
      once-per-session default, `cooldown` seconds re-arm, fire-without-state
      when `session_id` is absent, all state I/O wrapped fail-open. Confirm
      the 1.2 cases pass.

## 2. Hook registration

- [x] 2.1 [req: guardrail-hook-registration] Update the existing hooks.json
      test to assert exactly two events — `PreToolUse` and `PostToolUse` —
      each with matcher `Edit|Write` and the single python3 command on
      `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/guardrails.py`. Run and
      observe it fail.
- [x] 2.2 [req: guardrail-hook-registration] Add the `PostToolUse` entry to
      `plugins/s/hooks/hooks.json`, mirroring the PreToolUse entry. Confirm
      2.1 passes.

## 3. Documentation

- [x] 3.1 [req: guardrails-key-docs] Rewrite `.shipd/README.md`'s
      "Guardrails" section per the guardrails-key-docs delta: rule file
      format and both modes, the three sources and precedence, cooldown
      behavior, the `false`/`disable` config forms with the superseded
      `rules` member noted, and the `SHIPD_GUARDRAILS=off` bypass.
- [x] 3.2 [req: guardrails-key-docs] Update the `"// guardrails"` line in
      `plugins/s/skills/build/references/shipd.config.example.json` to name
      the rulebook directories and the README section, declaring no value.

## 4. Version and verification

- [x] 4.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` `version` from
      `0.6.152` to `0.6.153`.
- [x] 4.2 [req: *] Run the full engine suite —
      `python3 -m unittest discover -s plugins/s/skills/build/tests` from the
      worktree root — and confirm it passes without `textual` or `pydantic`
      installed.

## 5. Standalone guide

- [x] 5.1 [req: guardrails-key-docs] Write `docs/guardrails.md` per the
      guardrails-key-docs delta, matching the tone and shape of the existing
      `docs/*.md` guides: how the hook works (PreToolUse deny, PostToolUse
      remind, added lines only), the rule file format with one worked
      example, the three sources and their precedence, adding/editing/
      overriding rules (including overriding a built-in by filename), the
      `false`/`disable` kill-switches and `SHIPD_GUARDRAILS=off`, cooldown
      behavior, and a "token cost" section stating rules consume no model
      context until one fires, a deny costs the retried edit while a remind
      costs one injected sentence, and the deny-for-certain /
      remind-for-fuzzy authoring guidance.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Edit | 23 | 35.8k |
| Bash | 68 | 25.8k |
| Write | 6 | 15.2k |
| (no tool) | 0 | 10.4k |
| Read | 21 | 2.2k |
| Agent | 2 | 801 |
| SendMessage | 1 | 500 |
| **Total** | 121 | 90.7k |
