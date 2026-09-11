## 1. Lower the wait default

- [x] 1.1 [P1] [req: atomic-task-claiming-with-stable-ids] In `plugins/s/skills/build/tests/test_claim_task.py`, add a test pinning the shipped `--wait` default to 90 seconds: assert the `TIMEOUT=` assignment in `plugins/s/skills/build/scripts/claim_task.sh` reads 90, and assert the script's own header/usage text states 90 rather than 600. Run it and observe it fail — the script still defaults to 600.
- [x] 1.2 [P2] [req: atomic-task-claiming-with-stable-ids] In `plugins/s/skills/build/scripts/claim_task.sh`, change `TIMEOUT=600` to `TIMEOUT=90` and update the header comment that states the default, so both read 90. Confirm the test from task 1.1 passes and the existing wait tests (`test_wait_blocks_through_a_barrier_then_claims`, `test_wait_times_out_empty_on_stdout`, `test_wait_returns_at_once_when_nothing_is_pending`) still pass.
- [x] 1.3 [P3] [req: atomic-task-claiming-with-stable-ids] In `plugins/s/agents/sub-agent.md`, change the wait bullet's stated default from 600 to 90, and state that the call is meant to fit inside one foreground tool call and is simply re-issued when it times out empty.
- [x] 1.4 [P3] [req: atomic-task-claiming-with-stable-ids] In `plugins/s/skills/build/SKILL.md`, change the coordinator reference's stated `--timeout` default from 600 to 90, so the fourth site naming the default agrees with the other three.

## 2. Forbid ending a turn on a held claim

- [x] 2.1 [P3] [req: foreground-claim-discipline] In `plugins/s/skills/build/tests/test_subagent_contract.py`, add a test asserting the worker contract's loop section requires completing or releasing a claimed task before the worker ends its turn, and names awaiting a long-running verification as one such stop. Run it and observe it fail — the contract carries no such rule yet.
- [x] 2.2 [P4] [req: foreground-claim-discipline] In `plugins/s/agents/sub-agent.md`, add that rule to the loop section, beside the existing never-claim-in-the-background bullet: a worker never ends its turn holding a claim, and completes or releases first — including when it stops to await a long-running verification. Confirm the test from task 2.1 passes.

## 3. Orchestrator stale-claim check

- [x] 3.1 [P4] [req: foreground-claim-discipline] In `plugins/s/skills/build/tests/test_subagent_contract.py` (or whichever module guards the build skill's prose, matching where the existing coordinator-reference assertions live), add a test asserting the build skill's fan-out phase directs the orchestrator to run `status --stale-after` between rounds and to act on a reported stale claim. Run it and observe it fail.
- [x] 3.2 [P5] [req: foreground-claim-discipline] In `plugins/s/skills/build/SKILL.md`'s Phase 3, add that step: between fan-out rounds run `claim_task.sh status <change> --stale-after <mins>`, and on a `[stale]` line either resume the holder or reclaim with `release --stale`. State that `claim` never reclaims on its own, so a slow-but-alive worker is not robbed. Confirm the test from task 3.1 passes.

## 4. Ship

- [x] 4.1 [P5] [req: *] Bump the version in `plugins/s/.claude-plugin/plugin.json` from `0.6.207` to `0.6.208`.
- [x] 4.2 [P6] [req: *] Run the engine suite, `python3 -m unittest discover -s plugins/s/skills/build/tests`, and confirm it passes with the new tests included.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 123 | 40.5k |
| Edit | 11 | 6.9k |
| (no tool) | 0 | 5.7k |
| Agent | 4 | 3.6k |
| ToolSearch | 1 | 3.1k |
| Read | 12 | 2.2k |
| SendMessage | 2 | 1.1k |
| **Total** | 153 | 62.9k |
