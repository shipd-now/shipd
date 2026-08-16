## 1. Doctor probe tests and docs

- [x] 1.1 [P1] [req: doctor-verb] In
      `plugins/s/skills/build/tests/test_shipd_cli.py`, extend the doctor
      check tests (the per-check class near line 589): `difft` missing from
      PATH → a `warn difft — ` line naming the review's text-engine
      degradation and the `semdiff doctor --fix` remedy; `difft` present →
      an `ok difft — ` line; the check reported directly after `gh`. Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` and
      observe the new tests fail.
- [x] 1.2 [P1] [req: doctor-remedy-boundaries] In
      `plugins/s/skills/doctor/SKILL.md`: add `difft` to the known parsed
      check names (the list currently naming `pipeline`, `gh`, `textual`,
      `pydantic`, `snapshot`, `statusline`) and add the remedy-table row —
      `warn difft` →
      `python3 "${CLAUDE_PLUGIN_ROOT}/skills/review/scripts/semdiff.py" doctor --fix`,
      runnable on consent, noting it may reach the network (tiered installer:
      Homebrew, cargo, prebuilt binary).
- [x] 1.3 [P1] [req: review-difft-autofix] In
      `plugins/s/skills/review/SKILL.md`, rewrite the Degradation section:
      at review start, when `difft` is not on PATH, run
      `semdiff doctor --fix` once automatically and re-probe; on success
      proceed syntax-aware; on failure print a prominent notice naming the
      text-engine degradation and a manual hint (e.g.
      `brew install difftastic`), add a could-not-verify entry in both human
      and `--json` output, and proceed on the text engine. Keep the existing
      rules that the text engine is stamped `engine: "text"` and raw-file
      dumping stays forbidden.

## 2. Doctor probe implementation

- [x] 2.1 [req: doctor-verb] In `plugins/s/bin/shipd`, add a `check_difft`
      preflight check using stdlib `shutil.which("difft")`, reported directly
      after `gh`: present → `ok difft — found at <path>`; missing →
      `warn difft — not found — semantic reviews degrade to the text engine;
      run /s:doctor or `semdiff doctor --fix``. Wire it into the doctor
      composition beside the existing checks. Re-run
      `python3 -m unittest discover -s plugins/s/skills/build/tests`; all
      tests (including 1.1's) pass.

## 3. Version bump and verification

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      `0.6.124` → `0.6.125` (plugins/s content changed in this change).
- [x] 3.2 [req: *] Run the build suite and the review suite
      (`python3 -m unittest discover -s plugins/s/skills/review/tests`);
      confirm both green.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 99 | 32.2k |
| (no tool) | 0 | 7.0k |
| Edit | 12 | 6.0k |
| Read | 33 | 3.7k |
| Agent | 4 | 1.8k |
| ToolSearch | 2 | 490 |
| **Total** | 150 | 51.0k |
