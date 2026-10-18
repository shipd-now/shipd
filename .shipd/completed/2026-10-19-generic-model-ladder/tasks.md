## 1. The generic ladder in the engine

- [x] 1.1 [req: stage-model-resolution, model-ladder-key] In
      `plugins/s/skills/build/tests/test_spec_common.py`, add tests:
      `DEFAULT_MODEL_LADDER` equals the pinned tuple; `resolve_model_ladder`
      returns a declared `models` list and the default when none is declared;
      a malformed `models` (a string, or a list holding an empty string) makes
      reading the configuration raise a `ConfigError` naming `models`;
      `resolve_model_tier("tier-below", None, ["big", "mid", "small"])` is
      `mid`; an off-ladder anchor resolves to itself for both below-tiers; and
      an empty ladder resolves them to the anchor. Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests -p 'test_spec_common.py'`
      and observe the new tests fail.
- [x] 1.2 [req: stage-model-resolution, model-ladder-key] In
      `plugins/s/skills/build/scripts/spec_common.py`, rename `MODEL_LADDER`
      to `DEFAULT_MODEL_LADDER`, add `"models"` to `RECOGNIZED_CONFIG_KEYS`,
      add a `resolve_model_ladder(config=None)` resolver and the `models`
      validation (a list of non-empty strings, else a `ConfigError` naming
      `models` and the file), and give `resolve_model_tier` a `ladder=None`
      parameter that resolves against the passed ladder, falling back to the
      anchor when the anchor is not on it.

## 2. The autopilot threads the ladder

- [x] 2.1 [req: stage-model-resolution] In
      `plugins/s/skills/build/tests/test_autopilot.py`, add tests: a declared
      `models` key makes a stage's `tier-below` resolve against it; the dry
      run prints the resolved ladder; the run report carries the ladder and the
      anchor. Run the suite and observe the new tests fail.
- [x] 2.2 [req: stage-model-resolution] In
      `plugins/s/skills/build/scripts/autopilot.py`, resolve the ladder once
      per run from the run's root with `sc.resolve_model_ladder`, thread it to
      every `sc.resolve_model_tier` call and to `_tier_anchor` (whose top is
      the resolved ladder's first entry), print it beside the anchor in the
      dry run, and record it in both report dicts.

## 3. The descriptions everywhere

- [x] 3.1 [req: stage-model-resolution, model-ladder-key] Replace the
      Claude-alias wording with the declared-ladder wording in
      `plugins/s/skills/autopilot/SKILL.md` (the ladder-top note),
      `plugins/s/skills/build/SKILL.md` (the `subagent_model` table),
      `plugins/s/harness/bodies/autopilot.md`, and
      `plugins/s/harness/references/autopilot.md`: each SHALL name the `models`
      config key and the default ladder rather than the alias `fable`.
- [x] 3.2 [req: model-ladder-key] In `docs/customise.md`'s configuration table,
      add a `models` row: the strongest-first model ladder the symbolic tiers
      resolve against, defaulting to the engine's built-in ladder. Author it
      through the documentation standard and run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/customise.md`.

## 4. Version bump

- [x] 4.1 [req: *] In `plugins/s/.claude-plugin/plugin.json`, change `version`
      from `0.6.325` to `0.6.326`.

## 5. Verify

- [x] 5.1 [req: *] Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` and
      `python3 -m unittest discover -s evals/tests`; both exit 0. Run
      `python3 plugins/s/skills/build/scripts/spec_lint.py generic-model-ladder`
      and confirm `OK`. Confirm end to end: a temp repo declaring
      `{"models": ["big", "mid", "small"]}` makes `autopilot.py <epic>
      --dry-run --session-model big` print the declared ladder and resolve the
      stages against it.
