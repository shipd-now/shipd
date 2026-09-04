## 1. Trust ledger and consent gate

- [x] 1.1 [req: hook-trust-ledger, hook-consent-gate] Add failing tests to
      `plugins/s/skills/build/tests/test_worktree_engine.py` (pointing `HOME`
      at a per-test temp dir): an untrusted configured hook makes the create
      path exit `3` with the worktree kept, the hook unrun, and output naming
      the declaring config, the items, and `hooks trust`; `hooks add`
      auto-trusts so a subsequent create runs the hook unprompted; a hand-edit
      to the trusted list invalidates trust; a malformed
      `~/.shipd-trust.json` is treated as empty without crashing. Run them and
      observe them fail.
- [x] 1.2 [req: hook-trust-ledger] In
      `plugins/s/skills/build/scripts/worktree.py`, add the ledger helpers:
      trust path (`os.path.expanduser("~/.shipd-trust.json")`), fingerprint
      (`hashlib.sha256` over `json.dumps(items, separators=(",", ":"))`),
      a loader treating a missing/unreadable file as `{}`, and a recorder
      keyed by `os.path.realpath(source)` that warns on stderr and returns on
      write failure.
- [x] 1.3 [req: hook-consent-gate] In `worktree.py`, add
      `ensure_hooks_trusted(items, source)` — trusted or empty list returns
      immediately; untrusted with `sys.stdin.isatty()` prints the source and
      items and prompts (`y`/`yes` records trust and returns, anything else
      refuses); untrusted non-TTY reports the source, items, and
      `hooks trust`, and refuses. Wire it before both `run_hooks` call sites
      (`cmd_create` and the `hooks run` verb); a refusal exits
      `HOOK_FAILURE_EXIT` with the created worktree left in place.
- [x] 1.4 [req: hook-trust-ledger] In `worktree.py`, after a successful
      `hooks add` or `hooks remove` config write, re-resolve the effective
      hooks and record trust for the resulting `(source, items)`; confirm the
      1.1 tests now pass.
- [x] 1.5 [req: worktree-hooks-trust-verb] Add failing tests to
      `test_worktree_engine.py`: `hooks trust` records the resolved list so a
      following non-TTY create runs hooks unprompted, and `hooks trust` with
      nothing configured exits non-zero leaving the ledger unchanged. Run and
      observe them fail.
- [x] 1.6 [req: worktree-hooks-trust-verb] Implement the `hooks trust` verb in
      `worktree.py` (resolve, print source and items, record, exit 0; nothing
      configured → report and exit non-zero without writing); confirm the 1.5
      tests pass.

## 2. Documentation

- [x] 2.1 [req: portable-workspaces-doc] In `docs/portable-workspaces.md` §8,
      add the inherited-hooks warning (a shared workspace repo's tracked
      config supplies `post-worktree-scripts` to member repos beneath it; the
      first-run consent gate prompts on a TTY, refuses with exit `3`
      non-interactively; `worktree.py hooks trust` records consent
      explicitly) and the concurrent-answer paragraph (two clones answering
      the same pending question conflict on that block's `Answer:` line —
      keep exactly one answer, never both).

## 3. Version bump and verification

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` `version` to
      `0.6.178`, then run the full engine suite
      `python3 -m pytest plugins/s/skills/build/tests/ -q` (no `textual`
      installed) and confirm it passes.

## 4. Content-keyed trust and conditional auto-trust (validation fixes)

- [x] 4.1 [req: hook-trust-ledger] In
      `plugins/s/skills/build/tests/test_worktree_engine.py`, add failing
      tests: (a) in a git repo whose *tracked, committed* `.shipd-config.json`
      declares hooks, `hooks trust` at the repo root followed by `hooks run`
      from inside a created worktree executes the hooks unprompted; (b) with a
      tracked untrusted item already declared, `hooks add "echo mine"` records
      no ledger entry and a following non-TTY create refuses with both items
      listed; (c) the ledger file's keys are list fingerprints (not paths).
      Update existing assertions that read the ledger as path-keyed. Run and
      observe the new tests fail.
- [x] 4.2 [req: hook-trust-ledger] In
      `plugins/s/skills/build/scripts/worktree.py`, rework the ledger to be
      fingerprint-keyed: `record_trust` writes
      `{<fingerprint>: <declaring config realpath>}` entries,
      `hooks_trusted` checks fingerprint membership only, and
      `_trust_after_write` records only when the effective list *before* the
      write was trusted or empty (capture it before writing the config).
      Confirm the 4.1 tests pass.
- [x] 4.3 [req: hook-consent-gate] In `worktree.py`, make the non-TTY refusal
      and the declined-consent report name the full resume path — `hooks
      trust`, then `hooks run` run from the created worktree (print the
      worktree path when the create path produced one) — and update the tests
      asserting the message. Confirm the suite section passes.
- [x] 4.4 [req: portable-workspaces-doc] In `docs/portable-workspaces.md` §8,
      state that the ledger is keyed by the exact command list, so consent
      travels across checkouts and worktrees of the same list, and that
      registering with `hooks add` never trusts previously-declared unseen
      items; then run the full engine suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) and
      confirm it passes.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 129 | 40.6k |
| Edit | 52 | 32.0k |
| Read | 34 | 7.9k |
| (no tool) | 0 | 6.1k |
| Agent | 4 | 1.9k |
| ToolSearch | 1 | 78 |
| Write | 3 | 13 |
| **Total** | 223 | 88.6k |
