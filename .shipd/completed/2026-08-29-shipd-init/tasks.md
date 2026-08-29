# Tasks — shipd-init

## 1. Engine verb

- [x] 1.1 [req: layout-init-verb] Add a `TestInitVerb` class to
      `plugins/s/skills/build/tests/test_spec_status.py` covering: a fresh
      root gets `verified/`/`planned/`/`completed/` created under `.shipd/`
      with three `created` lines, the `all shipd directories are ready`
      summary, and exit 0; a root whose `verified/` already holds a spec file
      keeps that file byte-identical, reports `exists` for it and `created`
      for the other two, exit 0; a second run reports all three `exists` and
      exits 0; a regular file at `.shipd` (and, in a second case, at
      `.shipd/planned`) makes the verb create nothing, print an `Error:` line
      naming the path, and exit 1; a root config `{"dir": "specs"}` places
      the layout under `specs/`. Run the class and observe it fail — the
      `init` verb does not exist yet.
- [x] 1.2 [req: layout-init-verb] Implement the verb in
      `plugins/s/skills/build/scripts/spec_status.py`: a `cmd_init(root)`
      handler (resolve via `sc.specs_dir(root)`, check-then-create with
      `os.makedirs(..., exist_ok=True)`, raise `StatusError` naming any
      non-directory blocker before creating anything, print per-directory
      `created`/`exists` lines relative to the root then
      `all shipd directories are ready`), an `init` subparser with the shared
      `--root` default, and the `if args.verb == "init":` dispatch line in
      `main`. Confirm the 1.1 tests pass.

## 2. Binary dispatch

- [x] 2.1 [req: cli-dispatch] In
      `plugins/s/skills/build/tests/test_shipd_cli.py`, add tests that
      `shipd init --root <tmpdir>` creates the three layout directories and
      exits 0 with output ending `all shipd directories are ready`, and that
      the `shipd --help` banner lists `init` among the verbs. Run them and
      observe both fail — the binary has no `init` verb yet.
- [x] 2.2 [req: cli-dispatch] In `plugins/s/bin/shipd`: add
      `"init": ("spec_status.py", ["init"])` to `VERB_TABLE`, add an
      `init [--root DIR]` row to `USAGE` (wording: `create the content
      directory layout (safe to re-run)`), and extend the module docstring's
      deliberate-exceptions sentence with `init` as a sixth exception that
      writes only empty layout directories, never a spec artifact. Confirm
      the 2.1 tests pass.

## 3. Plan-skill guard and version

- [x] 3.1 [P1] [req: missing-layout-guard] In
      `plugins/s/skills/plan/SKILL.md`, update the Requirements paragraph
      ("When that layout is missing...") so the accepted-scaffold action runs
      the engine verb `python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/
      spec_status.py" init` (the same function behind `shipd init`) instead
      of hand-scaffolding the directories; keep the stop-and-ask shape and
      the "Missing content-directory layout" bullet under "What still stops
      the flow" consistent with it. Docs-only, no test.
- [x] 3.2 [P1] [req: *] Bump `"version"` in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.160` to `0.6.161`.

## 4. Verification barrier

- [x] 4.1 [req: *] Run the full engine suite from the worktree root with
      `python3 -m unittest discover -s plugins/s/skills/build/tests` and
      confirm it passes (it must not require `textual`/`pydantic`); then run
      `python3 plugins/s/skills/build/scripts/spec_lint.py shipd-init` and
      confirm exit 0.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 79 | 19.3k |
| Write | 6 | 11.5k |
| Edit | 15 | 2.2k |
| Read | 20 | 1.8k |
| Agent | 2 | 1.1k |
| (no tool) | 0 | 624 |
| **Total** | 122 | 36.5k |
