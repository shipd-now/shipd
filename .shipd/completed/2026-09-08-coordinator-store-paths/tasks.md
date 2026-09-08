## 1. Coordinator base resolution (claim_task.sh)

- [x] 1.1 [req: atomic-task-claiming-with-stable-ids] In
      `plugins/s/skills/build/tests/test_claim_task.py`, add fixtures and
      tests for the resolution legs, mirroring the suite's existing
      subprocess-driven style: (1) a store fixture — a consumer git repo
      whose `.shipd-config.json` declares an absolute `store_root` pointing
      at a separate directory, with the change's `tasks.md` under
      `<store>/<consumer basename>/planned/<change>/` — proving `status`,
      `claim`, and `complete` operate on the store's tasks file (counts,
      the `- [~]`/`- [x]` rewrites, and the `.tasks.claims` sidecar all land
      there); (2) a renamed-dir fixture (`dir: ".agents/.shipd"`) proving
      the `content-dir:` leg; (3) a malformed `.shipd-config.json` beside a
      change under plain `.shipd/planned/` proving the literal fallback.
      Run the new tests and observe the store and renamed-dir ones fail
      against the current script.
- [x] 1.2 [req: atomic-task-claiming-with-stable-ids] In
      `plugins/s/skills/build/scripts/claim_task.sh`, add
      `SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)` near the
      top (mirroring `worktree.sh:52`), and replace the three hardcoded
      paths at lines 139-141: run
      `python3 "$SCRIPT_DIR/spec_status.py" config-show 2>/dev/null` once,
      capture the output, parse `store:` and `content-dir:` with
      `sed -n 's/^store: //p' | head -n 1` (and likewise for
      `content-dir:`), set `BASE` to the store when non-empty, else the
      content dir, else `.shipd`, and derive
      `TASKS`/`LOCK`/`CLAIMS` as `$BASE/planned/${CHANGE}/...`. Update the
      header comment's `.shipd/planned` mentions to say the base is
      resolved through the engine.
- [x] 1.3 [req: atomic-task-claiming-with-stable-ids] Run the full
      `plugins/s/skills/build/tests/` suite (unittest discover, no `-t`
      flag); confirm the new tests pass and every pre-existing
      `test_claim_task.py` test passes unmodified.

## 2. Store-aware remove guard (worktree.sh)

- [x] 2.1 [req: worktree-guard-content-dir] In
      `plugins/s/skills/build/tests/test_worktree.py`, add guard tests over
      a store-configured worktree fixture (consuming repo with a linked
      worktree for change `x`, config declaring an absolute `store_root`):
      (1) the store's per-repo folder holding a planned directory for
      change `x` → `remove x` refuses exit 2 with a reason naming that
      store directory; (2) a
      `- [~]` line in that dir's `tasks.md`, and separately a
      `.tasks.lock` there → refusal with the claim/lock reason; (3) only an
      unrelated `planned/y/` in the store and a clean worktree → `remove x`
      succeeds exit 0. Run the new tests and observe (1) and (2) fail
      against the current script.
- [x] 2.2 [req: worktree-guard-content-dir] In
      `plugins/s/skills/build/scripts/worktree.sh`, extend the remove
      guard block (lines 220-265): capture the existing
      `config-show --root "$WORKTREE"` output into a variable once, parse
      `content-dir:` from it exactly as today plus a new `store:` parse;
      when the store value is non-empty, add three scoped checks against
      `"$store/planned/$CHANGE"` — directory exists → append an
      unshipped-change reason naming that path (no
      `planned_is_base_content` carve-out); its `tasks.md` matches
      `- \[~\]` → append the in-progress-claim reason; a `.tasks.lock`
      there → append the lock reason. Leave the in-worktree scan untouched.
- [x] 2.3 [req: worktree-guard-content-dir] Run the full
      `plugins/s/skills/build/tests/` suite; confirm the new guard tests
      pass and every pre-existing `test_worktree.py` /
      `test_worktree_engine.py` test passes unmodified.

## 3. Ship hygiene

- [x] 3.1 [req: *] Bump the patch version in
      `plugins/s/.claude-plugin/plugin.json` (read the current value and
      increment the patch component), per the repo's plugin-snapshot rule.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 63 | 18.3k |
| Edit | 15 | 6.4k |
| Read | 21 | 2.6k |
| (no tool) | 0 | 1.4k |
| Agent | 2 | 1.1k |
| **Total** | 101 | 29.8k |
