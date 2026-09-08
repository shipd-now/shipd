# Tasks — project-name-rule

## 1. Relaxed name rule in validate_workspace

- [x] 1.1 [req: project-registry-semantics] In
      `plugins/s/skills/build/tests/test_spec_common.py`
      (`ValidateWorkspaceTest`): replace `test_non_kebab_slug_errors` with
      `test_identifier_style_names_validate_clean` asserting a registry
      declaring projects `APISchema` and `api_schema2` (each with
      `{"repos": ["r1"]}` / `{"repos": ["r2"]}`) returns no errors; add
      `test_name_with_whitespace_errors` asserting a project named
      `API Schema` yields an error containing `API Schema`; add
      `test_casefold_duplicate_names_error` asserting projects `APISchema`
      and `apischema` yield an error containing both names. Run the class
      and observe the new tests fail against the current kebab rule.
- [x] 1.2 [req: workspace-focus] In the same test file: add
      `test_mixed_case_focus_validates_clean` asserting
      `{"focus": "APISchema", "projects": {"APISchema": {"repos": ["r"]}}}`
      returns no errors; rewrite `test_non_kebab_focus_errors` as
      `test_malformed_focus_errors` using `focus: "not valid"` (whitespace)
      against a declared `alpha` project, asserting an error naming `alpha`.
      Run and observe the new/changed tests fail.
- [x] 1.3 [req: project-registry-semantics, workspace-focus] In
      `plugins/s/skills/build/scripts/spec_common.py`: add
      `PROJECT_NAME_RE = re.compile(r"^[A-Za-z0-9]+(?:[-_.][A-Za-z0-9]+)*$")`
      directly below `KEBAB_RE` with a comment that it governs workspace
      project names only. In `validate_workspace`: check registry keys with
      `PROJECT_NAME_RE`, error text
      `"project name '%s' is not a valid project name (ASCII letters and digits joined by '-', '_' or '.')"`;
      after the key loop, report
      `"project names '%s' and '%s' collide under case folding"` for any two
      declared names equal under `str.casefold()` (first-seen name first);
      check `focus` with `PROJECT_NAME_RE` and reword its malformed-value
      error to say "valid project name" instead of "kebab-case project
      slug"; update the docstring's kebab wording. Confirm the tests from
      1.1 and 1.2 pass and the rest of `test_spec_common.py` stays green.

## 2. Initiative brief Project: value

- [x] 2.1 [req: initiative-brief-format] In
      `plugins/s/skills/build/tests/test_spec_lint.py`, in the existing
      `InitiativeBriefLintTest` class (line 2121): add a test where the workspace registry
      declares project `APISchema` and a structurally valid brief carries
      `Project: APISchema`, asserting `lint_initiative` reports no errors.
      Run it and observe it fail on the current kebab gate.
- [x] 2.2 [req: initiative-brief-format] In
      `plugins/s/skills/build/scripts/spec_lint.py` (`lint_initiative`
      metadata loop, currently line 859): validate the `Project:` value with
      `sc.PROJECT_NAME_RE` and the error text
      `"brief.md metadata `%s: %s` value is not a valid project name"`;
      update the kebab wording in the `lint_initiative` docstring and the
      `_check_brief_project` docstring block (lines 778–810). Confirm 2.1
      passes and the rest of `test_spec_lint.py` stays green.

## 3. Prose and version

- [x] 3.1 [req: initiative-brief-format] In
      `plugins/s/skills/initiative/SKILL.md` line 120: change the `Project:`
      description from "kebab-case" to "a project name (ASCII letters and
      digits joined by '-', '_' or '.')", keeping the rest of the line
      intact.
- [x] 3.2 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` `version` from
      `0.6.190` to `0.6.191`, then run the full engine suite
      `python3 -m unittest discover plugins/s/skills/build/tests` from the
      worktree root and confirm it passes.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 56 | 8.4k |
| Edit | 16 | 4.7k |
| (no tool) | 0 | 3.4k |
| Read | 13 | 1.0k |
| Agent | 2 | 737 |
| ToolSearch | 1 | 3 |
| **Total** | 88 | 18.2k |
