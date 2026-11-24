## 1. One waiting helper

- [x] 1.1 [req: store-push-debounce] In
      `plugins/s/skills/workspace/tests/test_store_sync.py`, replace
      `TestDelayedDebounce.test_a_burst_of_writes_ends_in_one_push` with
      three tests, one per new scenario of `store-push-debounce`: "A second
      helper exits while the first waits", "A later write extends the wait",
      and "An abandoned lock is taken over" (create the `.lock` file beside
      the token path and set its mtime 120 seconds back with `os.utime`).
      Find the lock file by listing `self.tokens` for names ending `.lock`.
      Run the file and observe the new tests fail.
- [x] 1.2 [req: store-push-debounce] In
      `plugins/s/skills/workspace/scripts/store_sync.py`, implement the
      token deadline, `_lock_path`, `_claim_lock`, `_holds_lock`,
      `_release_lock`, and the new `run_delayed` exactly as `plan.md`
      `## Implementation` specifies. Update the docstrings of `_token_path`
      and `run_delayed`. Run
      `python3 -m unittest discover -s plugins/s/skills/workspace/tests` and
      observe every test pass.
- [x] 1.3 [req: store-push-debounce] Bump the `version` in
      `plugins/s/.claude-plugin/plugin.json` from 0.6.384 to 0.6.385. Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` and
      confirm the summary line reads `OK`.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 36 | 22.8k |
| Write | 2 | 4.2k |
| SubagentHandback | 2 | 2.8k |
| Agent | 2 | 935 |
| (no tool) | 0 | 262 |
| ToolSearch | 1 | 158 |
| **Total** | 43 | 31.1k |
