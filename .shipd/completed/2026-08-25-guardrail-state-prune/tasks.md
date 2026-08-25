## 1. Prune-on-write

- [x] 1.1 [req: guardrail-state-prune] In
      `plugins/s/skills/build/tests/test_guardrails.py`, add a
      `StatePruning` case class on the existing isolated-HOME base covering:
      a stale (`os.utime` eight days back) sibling `.json` in
      `~/.shipd/guardrails/` is deleted when a remind rule fires; a fresh
      sibling survives; a week-old non-JSON entry survives; a PostToolUse
      payload matching no remind rule leaves the stale file in place; and a
      final in-process case for sweep failure: `unittest.mock.patch` on
      `guardrails.os.remove` raising `OSError`, then call
      `guardrails.save_state` directly with a stale sibling present, and
      assert no exception propagates and the session's own state file was
      written. Run the file and observe the new cases fail.
- [x] 1.2 [req: guardrail-state-prune] In
      `plugins/s/skills/build/scripts/guardrails.py`: add
      `PRUNE_AGE_SECONDS = 7 * 24 * 3600` and `prune_state_dir(directory,
      now)` deleting only regular `*.json` files older than the threshold,
      each unlink individually guarded; call it from `save_state` after the
      successful write, inside the existing fail-open posture. Confirm the
      1.1 cases pass.

## 2. Documentation

- [x] 2.1 [req: guardrail-state-prune] Add one sentence to
      `docs/guardrails.md`'s cooldown section and one to `.shipd/README.md`'s
      Guardrails cooldown paragraph: state files from past sessions are
      removed automatically about a week after their last use.

## 3. Version and verification

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` `version` from
      `0.6.153` to `0.6.154`.
- [x] 3.2 [req: *] Run the full engine suite —
      `python3 -m unittest discover -s plugins/s/skills/build/tests` from the
      worktree root — and confirm it passes without `textual` or `pydantic`
      installed.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 31 | 8.2k |
| Edit | 8 | 6.2k |
| Write | 1 | 4.8k |
| (no tool) | 0 | 3.7k |
| Read | 15 | 1.9k |
| Agent | 2 | 820 |
| **Total** | 57 | 25.6k |
