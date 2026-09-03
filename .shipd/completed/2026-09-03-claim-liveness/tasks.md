# Tasks — claim-liveness

## 1. Failing tests first

- [x] 1.1 [req: atomic-task-claiming-with-stable-ids, completion-and-release-without-tracking-line-numbers, status-reporting, stale-claim-reclamation] In
      `plugins/s/skills/build/tests/test_claim_task.py`, add failing tests
      per the delta scenarios: (1) `claim --as builder-2` writes a sidecar
      `.tasks.claims` record (id, label, epoch) while `tasks.md` shows only
      `[~]`, and a bare `claim` records the `anon`/session-id default;
      (2) `claim --wait` returns a ready task immediately; blocks through a
      barrier (complete the barrier task from the test a second later and
      assert the same invocation returns the freed task); exits 0 with empty
      stdout and a timeout stderr line under `--timeout 1`; returns at once
      with the no-pending message when nothing is pending; (3) `complete` on
      a `[ ]` task and `release` on a `[x]` task exit non-zero naming
      the state, boxes unchanged (regression for the observed `[x]`→`[ ]`
      flip); (4) `complete --as` mismatching the recorded holder refuses
      naming both labels, while a bare `complete` succeeds regardless;
      successful complete/release remove the record; (5) `status` first line
      is byte-identical, `claimed:` lines carry id/holder/age, a back-dated
      record (rewrite its epoch) gains ` [stale]`, and a record-less `[~]`
      prints unknown holder/age with the stale mark at exit 0;
      (6) `release --stale 30` releases the back-dated and record-less
      claims with one line each, leaves fresh claims, prints the
      no-stale-claims line when none qualify, and refuses an explicit id
      combined with `--stale`. Run the new tests and observe them fail.

## 2. Coordinator implementation

- [x] 2.1 [req: atomic-task-claiming-with-stable-ids, completion-and-release-without-tracking-line-numbers, status-reporting, stale-claim-reclamation] Rework
      `plugins/s/skills/build/scripts/claim_task.sh` per plan.md's
      Implementation: flag parsing for `--as/--wait/--timeout/--stale/
      --stale-after` after the existing positionals; the `.tasks.claims`
      TSV sidecar read/written only under the mkdir lock (record added on
      claim, removed on complete/release, file deleted when empty); the
      claim critical section refactored into a `claim_once` function that
      acquires and releases the lock itself; the `--wait` retry loop
      (5s sleep, 600s default deadline, lock never held while sleeping,
      immediate return on no-pending, timeout to stderr with exit 0);
      complete/release state guards (refuse non-`[~]`, exit 1 naming the
      state) and soft holder verification (refuse only on a mismatched
      explicit `--as`); the `status` `claimed:` lines with age formatting
      and `[stale]` past `--stale-after` (default 30m); and
      `release --stale <mins>` (mutually exclusive with an id, releases
      old-or-record-less claims, prints holder and age per release). Keep
      bash 3.2-compatible constructs, the existing exit codes, and the
      first status line byte-identical.
- [x] 2.2 [req: atomic-task-claiming-with-stable-ids, completion-and-release-without-tracking-line-numbers, status-reporting, stale-claim-reclamation] Run
      the task-1.1 tests and the full existing
      `plugins/s/skills/build/tests/test_claim_task.py`; confirm everything
      passes, including the pre-existing verbs' unchanged behavior.

## 3. Contract and docs

- [x] 3.1 [P1] [req: foreground-claim-discipline] In
      `plugins/s/agents/sub-agent.md`, amend "Your loop" step 2: wait for a
      barrier with `bash <CLAIM_SCRIPT> claim <change> --wait` in the
      foreground of a tool call; never run claim or status poll loops as
      background processes (a detached claim outlives your awareness of
      it); pass a stable personal `--as <label>` — your spawn description's
      role (e.g. `builder-2`) or a short label invented once — on every
      claim, complete, and release.
- [x] 3.2 [P1] [req: foreground-claim-discipline] In
      `plugins/s/skills/build/SKILL.md`, update the "Coordinator script
      reference" section with the new flags and verbs: `claim
      [--as <label>] [--wait [--timeout <secs>]]`, the `status` per-claim
      lines and `--stale-after <mins>`, and `release --stale <mins>`; note
      in Phase 3's fan-out bullet that idle workers wait via `claim --wait`
      rather than polling.
- [x] 3.3 [P1] [req: *] Bump `plugins/s/.claude-plugin/plugin.json`
      `version` from `0.6.171` to `0.6.172`.

## 4. Verification barrier

- [x] 4.1 [req: *] From the repo root run the full stdlib suite,
      `python3 -m unittest discover -s plugins/s/skills/build/tests -p
      "test_*.py"`; confirm green.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 49 | 19.0k |
| Write | 1 | 16.4k |
| Edit | 12 | 9.3k |
| (no tool) | 0 | 1.4k |
| Read | 14 | 975 |
| Agent | 2 | 964 |
| **Total** | 78 | 48.0k |
