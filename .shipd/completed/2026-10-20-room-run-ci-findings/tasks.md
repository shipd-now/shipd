## 1. Tests first

- [x] 1.1 [req: room-run-ci-findings] In `plugins/s/skills/room/tests/test_room_run.py`, let the fake gh serve `api --paginate repos/<repo>/pulls/<n>/reviews` from a scripted list, and add the tests listed in plan.md's Tests section. Run the file and confirm the new tests fail.

## 2. Runner

- [x] 2.1 [req: room-run-ci-findings] In `plugins/s/skills/room/scripts/room.py`, add `--ci-reviewer` to the `run` parser as plan.md's Parser section describes.
- [x] 2.2 [req: room-run-ci-findings] In `plugins/s/skills/room/scripts/room_run.py`, add `_ci_reviews` and `_ci_prompt`, the watch slices with the stderr filter, and the CI turn, as plan.md's Implementation describes. Run the room tests and confirm they pass.

## 3. Docs and version

- [x] 3.1 [req: room-run-ci-findings] In `docs/room-run.md`, add `--ci-reviewer` to the flag table and a short section on the CI turn: what triggers it, that a pushed fix re-runs the CI reviewer and requests re-reviews, and that a reply does not clear the CI verdict. Keep the doc lint-clean.
- [x] 3.2 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` by one patch above `main`. Run the full plugin test suite and the repo validation, and confirm both pass.
