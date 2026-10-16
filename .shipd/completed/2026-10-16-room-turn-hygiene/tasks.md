## 1. One resolver

- [x] 1.1 [req: room-gh-seam] In `plugins/s/skills/room/tests/test_room.py`, add tests for the four resolver scenarios (URL, `--repo`, neither, conflict) and for the watch state read carrying `--repo`. Extend `FakeGh` so `pr view` accepts a `--repo` argument and records it. Run them and observe them fail.
- [x] 1.2 [req: room-gh-seam] In `plugins/s/skills/room/scripts/room.py`, add a `--repo` argument to the shared `common` parser in `build_parser` and change `_resolve_room(gh, pr, repo=None)` to take the repository from a `/pull/<n>` URL, then `repo`, then `gh repo view`. Raise `RoomError` naming both on a conflict, and add `--repo` to `gh pr view` when a repository is known.
- [x] 1.3 [req: room-gh-seam] In `room.py`, pass `opts.repo` from `cmd_join`, `cmd_list`, `cmd_message`, `cmd_close`, and `cmd_watch` into `_resolve_room`. Change `_pr_closed` to `_pr_closed(gh, repo, number)` adding `--repo <repo>`, and update its call in `cmd_watch`. Confirm task 1.1's tests pass.

## 2. Open tasks

- [x] 2.1 [req: room-list-verb, room-watch-exit] In `test_room.py`, add tests for the two `list --open` scenarios and the two watch scenarios (closed line `open` empty, and listing an `input-required` task with the stderr `unresolved task` line before the closed line). Update `test_merged_pull_request_closes_the_watch` to expect `"open": []`. Run them and observe them fail.
- [x] 2.2 [req: room-list-verb] In `room.py`, add `OPEN_STATES = ("working", "input-required")` and a `--open` flag on the `list` subparser; filter tasks to `OPEN_STATES` in both the text and JSON paths of `cmd_list`.
- [x] 2.3 [req: room-watch-exit] In `room.py` `cmd_watch`, build the `open` list from the poll's `tasks` (`task`, `state`, `to`, `skill`), add it to the closed line, and print `watch: <n> unresolved task(s): #<id> <state>, ...` on stderr before the `the room is closed` line when it is not empty. Confirm tasks 2.1's tests pass and run `python3 -m unittest discover -s plugins/s/skills/room/tests`.

## 3. Skill, harness, docs

- [x] 3.1 [req: room-skill-stops, room-skill-merge-rule] In `plugins/s/skills/room/tests/test_room_skill.py`, add tests for the three skill scenarios and the harness-body scenario. Run them and observe them fail.
- [x] 3.2 [req: room-skill-stops] In `plugins/s/skills/room/SKILL.md`, extend the "Room closed" stop to report the `closed` line's `open` tasks as unresolved with id and state, and add a rule that every verb receives the user's pull request URL, or `--repo` when the user names a repository.
- [x] 3.3 [req: room-skill-merge-rule] In `SKILL.md`, add a short "Merging" section stating the reviewer rule from the delta spec, naming `gh pr merge`, `shipd room list <pr> --open --json`, `working`, and `input-required`.
- [x] 3.4 [req: room-skill-merge-rule, room-skill-stops] Mirror 3.2 and 3.3 in `plugins/s/harness/bodies/room.md` (inside the `background-tasks` segment) and in the stop list of `plugins/s/harness/references/room.md`, which also gains the `open` field in the watch output notes.
- [x] 3.5 [req: room-skill-stops, room-skill-merge-rule] In `docs/pr-room.md`, state in the "Know when a turn ends" section that the `closed` line lists unresolved tasks, add the merge rule and the URL and `--repo` forms, and run `python3 plugins/s/skills/document/scripts/docs_lint.py docs/pr-room.md` until it exits 0.
- [x] 3.6 [req: *] Bump `plugins/s/.claude-plugin/plugin.json`'s `version` by one patch above the value `main` carries, and run `python3 -m unittest discover -s plugins/s/skills/room/tests` and `version_guard.py --base main --head HEAD` to confirm both pass.
