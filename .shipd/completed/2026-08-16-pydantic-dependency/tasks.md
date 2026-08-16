# Tasks — pydantic-dependency

## 1. Dependency groundwork (docs and pins)

- [x] 1.1 [req: *] Amend `.shipd/constitution.md`'s stdlib-only bullet
      (Technology constraints): name two scoped exceptions — `textual`
      (dashboard `tui` rendering, as today) and `pydantic`
      (declared-pipeline validation only, lazily imported) — keeping the
      shared invariant that every engine script stays importable with
      neither installed.
- [x] 1.2 [req: *] Rewrite `AGENTS.md`'s "The delivery board's one
      third-party dependency" section to cover both pinned dependencies and
      their scopes (board `tui` → `textual`; declared-pipeline validation →
      `pydantic`), keeping the note that the stdlib test suite
      `plugins/s/skills/build/tests/` never installs either and always
      passes without them.
- [x] 1.3 [req: doctor-remedy-boundaries] Add `pydantic>=2.12,<3` to
      `requirements.txt` under the existing header comment, extending that
      comment to state the pipeline-validation scope and that both ranges
      are mirrored in `plugins/s/skills/doctor/SKILL.md`'s remedy table.
- [x] 1.4 [req: *] In `.github/workflows/ci.yml`, rename the
      "Install textual (board tui dependency)" step to cover both
      third-party dependencies (e.g. "Install third-party deps (board tui +
      pipeline validation)"); change no step ordering — the stdlib engine
      suite keeps running before the install.

## 2. Doctor check (test-first)

- [x] 2.1 [req: doctor-verb] In
      `plugins/s/skills/build/tests/test_shipd_cli.py`, add tests for a
      `check_pydantic` function mirroring the existing `check_textual`
      tests: with an injected `find_spec` stub returning a spec →
      `("ok", "pydantic", ...)`; returning `None` (and raising
      `ImportError`/`ValueError`) → `("warn", "pydantic", ...)` whose detail
      mentions pipeline validation and `pip install -r requirements.txt`;
      and assert `default_checks` includes a `pydantic` entry between
      `textual` and `snapshot`. Run the suite and observe the new tests
      fail — `check_pydantic` does not exist yet.
- [x] 2.2 [req: doctor-verb] In `plugins/s/bin/shipd`, add
      `check_pydantic(find_spec=importlib.util.find_spec)` directly after
      `check_textual` (same probe shape: `find_spec("pydantic")`,
      `ImportError`/`ValueError` → not found), returning
      `("ok", "pydantic", ...)` when importable and `("warn", "pydantic",
      ...)` naming declared-pipeline validation as the only affected surface
      with the `pip install -r requirements.txt` hint; append `check_pydantic()`
      to `default_checks` after `check_textual()`. Confirm 2.1's tests pass.
- [x] 2.3 [req: doctor-remedy-boundaries] In
      `plugins/s/skills/doctor/SKILL.md`: add `pydantic` to step 2's check
      enumeration, and add a remedy-table row `warn pydantic` — not
      importable → `python3 -m pip install "pydantic>=2.12,<3"`, runnable on
      consent, with the note that the range mirrors `requirements.txt` and
      the two must change together.

## 3. Close out

- [x] 3.1 [req: *] Bump the `version` in
      `plugins/s/.claude-plugin/plugin.json`.
- [x] 3.2 [req: *] Verify: run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` with
      pydantic **not** installed and confirm the whole suite passes
      (dependency-freeness holds); run `plugins/s/bin/shipd doctor` on this
      machine and confirm it now prints a `warn pydantic — ` line and still
      exits `0`.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 56 | 19.4k |
| Edit | 14 | 5.5k |
| (no tool) | 0 | 5.3k |
| Read | 19 | 2.4k |
| ToolSearch | 1 | 921 |
| Agent | 2 | 832 |
| SendMessage | 1 | 499 |
| Write | 1 | 323 |
| **Total** | 94 | 35.2k |
