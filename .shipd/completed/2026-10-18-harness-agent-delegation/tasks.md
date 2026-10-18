## 1. Name the agents in the delegation branches

- [x] 1.1 [req: delegation-agent-ids] In
      `plugins/s/skills/build/tests/test_harness_bodies.py`, add tests: the
      `build`, `ask`, and `autopilot` bodies rendered with `subagents` declare
      `shipd-sub-agent` (build, autopilot) and `shipd-oracle` (ask); the `build`
      body rendered without `subagents` names no `shipd-sub-agent` and carries
      the single-agent branch. Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests -p 'test_harness_bodies.py'`
      and observe the new tests fail.
- [x] 1.2 [req: delegation-agent-ids] In `plugins/s/harness/bodies/build.md`,
      change the `<!-- if:subagents -->` branch's opening line to direct the
      harness to spawn `shipd-sub-agent` executors ("spawn one `shipd-sub-agent`
      executor per currently-claimable task …"). Change nothing else in the file.
- [x] 1.3 [req: delegation-agent-ids] In `plugins/s/harness/bodies/ask.md`,
      change the `<!-- if:subagents -->` branch to name `shipd-oracle` as the
      helper agent it directs the harness to delegate the search to. Change
      nothing else in the file.
- [x] 1.4 [req: delegation-agent-ids] In `plugins/s/harness/bodies/autopilot.md`,
      change the `<!-- if:subagents -->` branch to name `shipd-sub-agent` as the
      per-stage worker it directs the harness to run. Change nothing else in the
      file.

## 2. Version bump

- [x] 2.1 [req: *] In `plugins/s/.claude-plugin/plugin.json`, change `version`
      from `0.6.323` to `0.6.324`.

## 3. Verify

- [x] 3.1 [req: *] Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests -p 'test_harness_bodies.py'`,
      then `python3 -m unittest discover -s plugins/s/skills/build/tests -p 'test_harness_generate.py'`
      and the whole `python3 -m unittest discover -s plugins/s/skills/build/tests`;
      all exit 0. Run
      `python3 plugins/s/skills/build/scripts/spec_lint.py harness-agent-delegation`
      and confirm it prints `OK`. Confirm a rendered `cursor` `build` body names
      no `shipd-sub-agent` while a rendered `claude-code` one does.
