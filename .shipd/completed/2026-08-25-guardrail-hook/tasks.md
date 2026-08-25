## 1. Guardrail engine — tests first

- [x] 1.1 [req: guardrail-added-line-matching, guardrail-deny-output, guardrail-default-rules, guardrail-fail-open]
      Add `plugins/s/skills/build/tests/test_guardrails.py` covering: Edit
      added-line extraction (a line present in both `old_string` and
      `new_string` is not evaluated), Write full-content scan, non-Edit/Write
      `tool_name` exits 0 silently, each of the three built-in rules denying
      its spec scenario line, deny stdout shape
      (`hookSpecificOutput.permissionDecision == "deny"`, reason contains the
      rule name, message, and offending line), clean edit exiting 0 with empty
      stdout, a `files` glob excluding a non-matching path, non-JSON stdin
      exiting 0, `SHIPD_GUARDRAILS=off` bypass, and an uncompilable config
      rule being skipped while built-ins still deny. Drive the script via
      `subprocess` with piped stdin (pattern: existing tests). Run the file
      and observe it fail — `guardrails.py` does not exist yet.
- [x] 1.2 [req: guardrails-key] Extend `test_guardrails.py` with config-key
      cases against a temp repo carrying `.shipd-config.json` (pass the temp
      dir as the payload's `cwd`): `"guardrails": false` allows everything, a
      `disable` list drops one built-in while others stay active, a config
      rule (`no-console-log`) denies, a same-named config rule replaces the
      built-in's pattern, and a malformed value (`"loud"`) behaves as
      undeclared. Run and observe failure.
- [x] 1.3 [req: guardrail-added-line-matching, guardrail-deny-output, guardrail-default-rules, guardrail-fail-open]
      Implement `plugins/s/skills/build/scripts/guardrails.py` (stdlib-only):
      read the PreToolUse JSON from stdin; honor `SHIPD_GUARDRAILS=off`
      first; extract added lines per the delta (`Edit`: `new_string` lines
      not exactly present among `old_string` lines; `Write`: all `content`
      lines; anything else: exit 0); define the three built-in rules with the
      exact patterns and messages from `guardrail-default-rules`; evaluate
      rules with `re.search` per line and `fnmatch` file globs; on match,
      print the deny JSON and exit 0; wrap the whole entry point so any
      exception exits 0 with no output.
- [x] 1.4 [req: guardrails-key] In `guardrails.py`, resolve the registry:
      import sibling `spec_common`, call `resolve_config(payload cwd,
      falling back to process cwd)` and take the merged dict (first element
      of the returned tuple); apply the `guardrails` key per the
      `guardrails-key` delta (false → allow all; object → replace-by-name,
      append, then `disable`; malformed → undeclared; uncompilable pattern →
      skip that rule). Confirm all of `test_guardrails.py` now passes.

## 2. Hook registration

- [x] 2.1 [req: guardrail-hook-registration] In `test_guardrails.py`, add a
      test that parses `plugins/s/hooks/hooks.json` and asserts exactly one
      event `PreToolUse`, matcher `Edit|Write`, and a single command entry of
      type `command` invoking
      `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/guardrails.py` via
      `python3`. Run and observe it fail — the file does not exist yet.
- [x] 2.2 [req: guardrail-hook-registration] Add `plugins/s/hooks/hooks.json`
      with that single PreToolUse entry, exactly as the delta's scenario
      states. Confirm the test from 2.1 passes.

## 3. Documentation

- [x] 3.1 [req: guardrails-key-docs] Add a `### Guardrails — the
      \`guardrails\` key` section to `.shipd/README.md` next to the existing
      "PR mode" section (`.shipd/README.md:308`), covering: the `false` form,
      the object form (`disable`, `rules` with
      `name`/`pattern`/`message`/`files`), the three built-in rule names
      active when undeclared, standard layered per-key resolution, and the
      `SHIPD_GUARDRAILS=off` bypass.
- [x] 3.2 [req: guardrails-key-docs] Add a `"// guardrails"` comment line to
      `plugins/s/skills/build/references/shipd.config.example.json` mirroring
      the existing `"// pr-mode"` line: name the optional key, point at the
      README section, declare no value.

## 4. Version and verification

- [x] 4.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` `version` from
      `0.6.151` to `0.6.152`.
- [x] 4.2 [req: *] Run the full engine suite —
      `python3 -m unittest discover -s plugins/s/skills/build/tests` from the
      worktree root — and confirm it passes without `textual` or `pydantic`
      installed (the new module must import stdlib only).

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 57 | 22.3k |
| Edit | 14 | 8.0k |
| Write | 3 | 5.8k |
| (no tool) | 0 | 4.5k |
| Agent | 2 | 1.6k |
| Read | 8 | 892 |
| **Total** | 84 | 43.3k |
