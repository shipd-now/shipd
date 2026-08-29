# Tasks — init-research-dir

## 1. Engine verb and its tests

- [x] 1.1 [req: layout-init-verb] In
      `plugins/s/skills/build/tests/test_spec_status.py`'s `TestInitVerb`,
      extend the enumerated set to four directories: fresh-create expects a
      `created` line for `research/` too; the no-clobber case seeds
      `.shipd/research/probe/report.md` alongside the existing spec fixture
      and asserts it survives byte-identical with `research` reported
      `exists`; the idempotent case expects four `exists` lines; add a
      blocker case with a regular file at `.shipd/research`; update the class
      docstring. Run the class and observe the new assertions fail — init
      still creates three.
- [x] 1.2 [req: layout-init-verb] In
      `plugins/s/skills/build/scripts/spec_status.py`: extend `LAYOUT_DIRS`
      to `("verified", "planned", "completed", "research")`, and update the
      documentation that enumerates the set — the `LAYOUT_DIRS` comment, the
      `cmd_init` docstring, and the module docstring's `init` verb entry.
      Confirm the 1.1 tests pass.

## 2. CLI test

- [x] 2.1 [req: layout-init-verb] In
      `plugins/s/skills/build/tests/test_shipd_cli.py`, update
      `test_init_creates_the_layout_and_reports_ready` to assert the
      four-directory set (including `research/`). No change to
      `plugins/s/bin/shipd` itself — the usage row stays generic.

## 3. Documentation and version

- [x] 3.1 [P1] [req: missing-layout-guard] In
      `plugins/s/skills/plan/SKILL.md`, update the missing-layout guard's
      minimal-layout wording to name `verified/`, `planned/`, `completed/`,
      and `research/`; leave the stop-and-ask shape and the
      `spec_status.py init` scaffold action unchanged.
- [x] 3.2 [P1] [req: layout-init-verb] In `.shipd/README.md`, directly after
      the fenced on-disk layout block, add one short paragraph recording that
      `shipd init` (delegating to `spec_status.py init`) creates `verified/`,
      `planned/`, `completed/`, and `research/` and never clobbers existing
      content, and that every other directory in the layout appears lazily
      when its engine first installs something.
- [x] 3.3 [P1] [req: *] Bump `"version"` in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.161` to `0.6.162`.

## 4. Verification barrier

- [x] 4.1 [req: *] Run the full engine suite from the worktree root with
      `python3 -m unittest discover -s plugins/s/skills/build/tests` and
      confirm it passes; then run
      `python3 plugins/s/skills/build/scripts/spec_lint.py init-research-dir`
      and confirm exit 0.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 73 | 16.2k |
| Write | 4 | 4.3k |
| (no tool) | 0 | 2.0k |
| Edit | 14 | 1.9k |
| Read | 13 | 803 |
| Agent | 2 | 480 |
| ToolSearch | 1 | 448 |
| SendMessage | 1 | 414 |
| **Total** | 108 | 26.6k |
