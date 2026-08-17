## 1. Failing tests and the wording sweeps

- [x] 1.1 [P1] [req: gate-poster] In
      `plugins/s/skills/review/tests/test_review_gate.py`, add marker-migration
      tests: `render_summary` output opens with `<!-- shipd-semantic-review -->`;
      `post` against a fake `gh` whose existing summary comment carries the
      legacy `<!-- am-semantic-review -->` marker PATCHes that comment (no
      second summary is POSTed) and the edited body opens with the new marker;
      `resolve`/`autoreply` recognize a gate thread rooted in a legacy-marker
      body. Run `python3 -m unittest discover -s plugins/s/skills/review/tests`
      and observe the new tests fail.
- [x] 1.2 [P1] [req: flow-timeseries] In
      `plugins/s/skills/build/tests/test_metrics.py` (and
      `plugins/s/skills/build/tests_pydantic/test_pipeline_show.py` where it sets the env), add
      env-migration tests: `SHIPD_FLOW_LOG_DIR` resolves the flow-log dir;
      `AM_FLOW_LOG_DIR` alone still resolves it (legacy fallback); with both
      set, `SHIPD_FLOW_LOG_DIR` wins; empty `SHIPD_FLOW_LOG_DIR` disables
      recording. Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` and
      observe the new tests fail.
- [x] 1.3 [P1] [req: *] Wording sweep outside the master library, boundary-
      anchored per plan.md's Implementation: in `plugins/s/skills/*/SKILL.md`,
      `plugins/s/agents/*.md`, `plugins/s/integrations/statusline.sh`, engine
      script comments/docstrings under `plugins/s/skills/*/scripts/`,
      `docs/portable-workspaces.md` (its `plugins/am` → `plugins/s`),
      `.shipd/README.md` (title `# am/ …` → `# .shipd/ — the shipd spec
      library` and its `am/` tree label), and the three
      `evals/cases/*/fixture/.shipd/README.md` copies: replace `am:<skill>` →
      `shipd:<skill>`, the stale `am/`-prefixed constitution path → `.shipd/constitution.md`, and
      brand prose (`the lean \`am\` artifacts` → `the lean shipd artifacts`,
      `an am spec-driven build` → `a shipd spec-driven build`, etc.). Do NOT
      touch: `review_gate.py`/review SKILL.md marker strings (task 2.1),
      `metrics.py` env names (task 2.2), time-of-day `am`/`pm` strings, video
      vocabulary entries, or anything under `.shipd/completed/`.
- [x] 1.4 [P1] [req: *] Wording sweep inside `.shipd/verified/`, same anchored
      substitutions (`am:<skill>` → `shipd:<skill>`, the stale `am/`-prefixed constitution path →
      `.shipd/constitution.md`, brand-prose `` `am` `` → shipd), across every
      capability EXCEPT `shipd-port` (deliberate legacy examples),
      `video-pipeline` (time-of-day strings), and the two delta-owned files
      `semantic-review`/`delivery-metrics` (their `am` tokens are retired by
      this change's deltas at merge). Then run
      `python3 plugins/s/skills/build/scripts/spec_lint.py --root .` and
      confirm the master library lints clean.
- [x] 1.5 [P1] [req: *] Rename the arbitrary `plugins/am` fixture paths to
      `plugins/s` in `plugins/s/skills/build/tests/test_tui_bootstrap.py`
      (lines ~44, ~85) and `plugins/s/skills/build/tests/test_spec_gate.py`
      (line ~163), assertions unchanged; confirm those two files' tests still
      pass.

## 2. Contract migrations

- [x] 2.1 [P2] [req: gate-poster] In
      `plugins/s/skills/review/scripts/review_gate.py`: set
      `MARKER = "<!-- shipd-semantic-review -->"`, add
      `LEGACY_MARKER = "<!-- am-semantic-review -->"`, and make every read-side
      identification (summary upsert lookup, `reply`/`autoreply`/`resolve`
      thread recognition) match either marker while all writes emit only
      `MARKER`. Update the marker mentions in
      `plugins/s/skills/review/SKILL.md`. Re-run the review suite; all tests
      including 1.1's pass.
- [x] 2.2 [P2] [req: flow-timeseries] In
      `plugins/s/skills/build/scripts/metrics.py`: rename
      `FLOW_LOG_ENV = "SHIPD_FLOW_LOG_DIR"`, add
      `FLOW_LOG_ENV_LEGACY = "AM_FLOW_LOG_DIR"`, and resolve the flow-log dir
      as new-then-legacy (winning variable's empty string disables), config
      layers unchanged. Update docstrings. Re-run the build suite; all tests
      including 1.2's pass.

## 3. Residual scan, bump, and verification

- [x] 3.1 [req: *] Run the residual scan from plan.md's Implementation
      (`grep -rnw am` over plugins/s, docs, README.md, AGENTS.md, install.sh,
      action.yml, .shipd/verified, .shipd/README.md, evals) and confirm every
      remaining hit is on the allowed-survivor list (shipd-port legacy
      examples, time-of-day strings, video vocabulary, and the delta-owned
      pre-merge tokens in verified/semantic-review + verified/delivery-metrics).
      Fix any other survivor and re-run until the scan is clean.
- [x] 3.2 [req: *] Read main's current version in
      `plugins/s/.claude-plugin/plugin.json` (0.6.127 at planning) and bump
      this branch's copy one patch above it (expected `0.6.128`).
- [x] 3.3 [req: *] Run all CI suites — build tests, `tests_textual`,
      `tests_pydantic` (skip-clean without pydantic), review tests,
      video-ingest tests — and confirm green.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 216 | 92.7k |
| (no tool) | 0 | 15.0k |
| Edit | 22 | 12.2k |
| Read | 39 | 8.8k |
| Write | 3 | 4.8k |
| SendMessage | 2 | 2.0k |
| Agent | 4 | 1.6k |
| ToolSearch | 4 | 1.1k |
| TaskStop | 1 | 24 |
| **Total** | 291 | 138.2k |
