## 1. Tests first

- [x] 1.1 [req: room-run-rereview, room-run-ci-findings] In `plugins/s/skills/room/tests/test_room_run.py`, add the tests listed in plan.md's Tests section and replace "test_an_empty_ci_reviewer_keeps_the_single_watch" with the slicing test. Run the file and confirm the new tests fail.

## 2. Runner

- [x] 2.1 [req: room-run-rereview] In `plugins/s/skills/room/scripts/room_run.py`, add "_sync_head", keep the last known head for author runs, call the helper after a no-task slice and after an ok turn, and remove the per-turn before read, as plan.md's Head tracking and Where the check runs sections describe.
- [x] 2.2 [req: room-run-ci-findings] In `plugins/s/skills/room/scripts/room_run.py`, make every author run watch in slices with the idle-line stderr filter, as plan.md's Slicing section describes. Run the room tests and confirm they pass.

## 3. Docs and version

- [x] 3.1 [req: room-run-rereview] In `docs/room-run.md`, update "Re-review after a push" and the CI section's last paragraph as plan.md's Docs section describes. Run `plugins/s/skills/document/scripts/docs_lint.py docs/room-run.md` and confirm it exits 0.
- [x] 3.2 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` by one patch. Run every suite `.github/workflows/ci.yml` runs and confirm each reports OK.
