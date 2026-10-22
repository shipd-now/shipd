## 1. Claim module

- [x] 1.1 [req: room-review-claim, room-review-status, room-review-claim-cleanup] Create
      `plugins/s/skills/room/tests/test_room_claim.py` with a fake GitHub
      `gh` seam holding refs and commits in dicts: ref create answers `201`
      once and `422 Reference already exists` after, `PATCH` always succeeds,
      commits get `committer.date` from a settable fake clock, and `gh api -i`
      responses carry a `Date` header from the same clock. Add failing tests
      for `acquire` (no claim → won gen 1; live other holder → held; `done` →
      done; `released` → won gen 2; 601 s stale → won gen 2; a lost create
      race → held), `beat`, `fence` (newer generation, wrong holder, 301 s
      old each raise; fresh passes and beats), `claimed_turn` (won runs and
      sets `pending` `room-review/<agent>`; not-done tip after the run writes
      `released`), `can_claim` and `delete_pr_claims`.
- [x] 1.2 [req: room-review-claim, room-review-status, room-review-claim-cleanup] Create
      `plugins/s/skills/room/scripts/room_claim.py` exactly per plan.md's
      Implementation (constants, `claim_prefix`, `holder_id`, `Claim`,
      `server_now`, `acquire`, `beat`, `fence`, `Heartbeat`, `can_claim`,
      `delete_pr_claims`, `set_status`, `claimed_turn`) until 1.1 passes.

## 2. Runners

- [x] 2.1 [req: room-review-claim, room-review-claim-permission, room-review-claim-cleanup] In
      `plugins/s/skills/room/tests/test_room_run_repo.py`, add failing tests
      using the existing `FakeRepoGh` extended with the claim endpoints: a
      held claim skips the turn and leaves the cursor; a `done` claim
      advances the cursor without a turn; `permissions.push: false` refuses a
      reviewer with one `Error:` line and exit `1`; a PR leaving the listing
      gets its claim refs deleted.
- [x] 2.2 [req: room-review-claim, room-review-claim-permission, room-review-claim-cleanup] In
      `plugins/s/skills/room/scripts/room_run_repo.py`, add the permission
      check to `cmd_run_repo` after the agent lock, wrap the reviewer and ci
      `runner(...)` call in `_run_loop` with `room_claim.claimed_turn`, and
      call `room_claim.delete_pr_claims` for each `stale` PR, per plan.md.
- [x] 2.3 [req: room-review-claim, room-review-claim-permission, room-review-claim-cleanup] In
      `plugins/s/skills/room/tests/test_room_run.py`, add failing tests for
      PR mode: a held claim runs no turn and watches again from the same
      cursor; `permissions.push: false` refuses a reviewer before joining; an
      author run is not refused for permission; a closed room deletes the
      PR's claim refs.
- [x] 2.4 [req: room-review-claim, room-review-claim-permission, room-review-claim-cleanup] In
      `plugins/s/skills/room/scripts/room_run.py`, add the permission check
      to `cmd_run` for roles `reviewer` and `ci` after `lock_pr_run`, wrap the
      reviewer and ci `runner(...)` call in `_run_pr` with
      `room_claim.claimed_turn`, and call `room_claim.delete_pr_claims` when
      the room reports the PR closed, per plan.md.

## 3. Poster fence

- [x] 3.1 [req: gate-poster-room-claim-fence] In
      `plugins/s/skills/review/tests/test_review_gate.py`, add failing tests:
      with `SHIPD_ROOM_CLAIM` set and `--room-agent`, a newer generation or a
      301 s old tip makes `post` write nothing and fail with a
      `room claim lost` line; a fresh claim posts, writes a `done` claim
      commit and a `success` `room-review/<agent>` status; without the
      variable no claim call is made.
- [x] 3.2 [req: gate-poster-room-claim-fence] In
      `plugins/s/skills/review/scripts/review_gate.py` `post`, add the lazy
      `room_claim` import, the two `fence` calls (before the first
      `_upsert_summary` and before the first `_post_review`), the
      `room claim lost` failure, and the `done` beat plus `success` status
      after submission, per plan.md.

## 4. Skill, docs, version

- [x] 4.1 [req: gate-poster-room-claim-fence] In
      `plugins/s/skills/room/SKILL.md` `## Reviewing`, add the rule that a
      `room claim lost` post failure ends the turn with the line relayed and
      nothing else posted; keep `test_room_skill.py` passing.
- [x] 4.2 [req: room-review-claim, room-review-status, room-review-claim-permission, room-review-claim-cleanup] Write
      `docs/room-review-claims.md` as a concept doc per the shipd
      documentation standard: claims, heartbeat, takeover, the poster fence,
      the `room-review/<agent>` status and how to require it through
      `merge.required_checks`, push permission, cleanup, and that runners
      older than `0.6.345` do not claim. Run `docs_lint.py` on it.
- [x] 4.3 [req: room-review-claim, gate-poster-room-claim-fence] Add a
      pointer to `docs/room-review-claims.md` in `docs/room-run.md`, keeping
      it within 150 lines, and a sentence on the claim fence to the
      `## Room-reviewer flags` section of
      `docs/semantic-review-reference.md`. Run `docs_lint.py` on both. Bump
      `plugins/s/.claude-plugin/plugin.json` from `0.6.344` to `0.6.345`.

## 5. Verify

- [x] 5.1 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/room/tests` and `python3 -m unittest discover -s
      plugins/s/skills/review/tests`, and grep each output for `OK`/`FAILED`.
