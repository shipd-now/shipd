## 1. Rendering

- [x] 1.1 [req: room-agent-card, room-message-shape] In
      `plugins/s/skills/room/tests/test_room_schema.py`, update the card-prose
      test to expect `<sub>**codex-reviewer** joined the room from codex · skills: review-finding</sub>`,
      and add a test that an agent Message from `copilot-ci`, state
      `completed`, to `builder`, text `done` renders a first prose line
      `**copilot-ci** → builder · completed`, a blank line, then `done`, and
      parses back with `text` exactly `done`; add a case with no `to` and no
      state rendering `**copilot-ci**` alone, and a `user` message rendering
      its text with no header. Run the file and observe the new tests fail.
- [x] 1.2 [req: room-agent-card] In
      `plugins/s/skills/room/scripts/room_schema.py`, change `_card_prose` to
      wrap the joined line in `<sub>` and `</sub>` and to use ` · skills: `
      in place of ` — skills: `; keep the description paragraph unchanged.
- [x] 1.3 [req: room-message-shape] In
      `plugins/s/skills/room/scripts/room_schema.py`, change `_message_prose`
      so an agent Message returns the header `**<agent>**` plus ` → <to>`
      when `to` is set and ` · <state>` when `state` is set, a blank line,
      then `m.text`; a `user` Message returns `m.text`. Confirm parsing reads
      only the marker, so `text` is unchanged, and run
      `python3 -B -m unittest plugins/s/skills/room/tests/test_room_schema.py`
      until it passes.

## 2. One comment per turn

- [x] 2.1 [req: room-message-verb, room-close-verb] In
      `plugins/s/skills/room/tests/test_room.py`, add tests with the fake
      `gh` runner for: a `message --task 10 --state completed` reply by
      `claude-b` whose task's last comment is issue comment 30, a `working`
      Message from `claude-b` (POST recorded, then a DELETE of
      `repos/<repo>/issues/comments/30`, stdout `comment` is the new id); the
      same with the claim from `codex-a` (no DELETE); a DELETE answered
      non-zero (stderr `warning: could not remove claim comment 30`, exit
      `0`); and `close --task 10 --state failed --reason wake-runner-failed`
      by `copilot-ci` over its own claim (POST then DELETE). Run and observe
      them fail.
- [x] 2.2 [req: room-message-verb, room-close-verb] In
      `plugins/s/skills/room/scripts/room.py`, add `_delete(gh, repo,
      comment_id)` calling `gh api -X DELETE
      repos/<repo>/issues/comments/<id>`, and `_own_claim(comments, task,
      agent)` returning the id of the task's last comment when
      `_endpoint(comment)` is the issue endpoint and its parsed Message for
      that task has `agent` equal to the acting agent and state `working`,
      else `None`. In `cmd_message` (the `--task` path, when the posted state
      is not `working`) and in `cmd_close`, read the claim id from the
      comments `_read_room` already returned, post the reply, then delete the
      claim; on `RoomError` from the delete write the warning line to stderr
      and continue. Make `_read_room` return the raw comments list it already
      reads so no second read is needed. Run `test_room.py` until it passes.

## 3. Watch ends with the pull request

- [x] 3.1 [req: room-watch-exit] In `plugins/s/skills/room/tests/test_room.py`,
      add a test where the fake runner answers `gh pr view 7 --json state`
      with `{"state": "MERGED"}` and no task is actionable: stdout holds one
      JSON line with `"closed": "merged"`, the context, and the cursor;
      stderr ends with `the room is closed`; `sleep` was never called; exit
      `0`. Add a second where the state is `OPEN` throughout and the existing
      timeout behavior holds. Update existing watch tests' fake runners to
      answer the state read with `{"state": "OPEN"}`. Run and observe the
      new test fail.
- [x] 3.2 [req: room-watch-exit] In `plugins/s/skills/room/scripts/room.py`
      `cmd_watch`, read `gh pr view <number> --json state` once per poll
      after the comments read; after printing any surfaced task lines, when
      the state is `MERGED` or `CLOSED` print the `closed` line on stdout and
      `watch: <context> is <merged|closed>; the room is closed` on stderr and
      return `0`. Run `test_room.py` until it passes.

## 4. The wake's reply

- [x] 4.1 [req: room-wake-workflow-template] In
      `plugins/s/skills/room/tests/test_room_wake.py`, add a test that the
      `run` job's `copilot -p` line carries `-s` and the prompt text contains
      `GitHub-flavoured markdown` and `fenced`. Run and observe it fail.
- [x] 4.2 [req: room-wake-workflow-template] In
      `plugins/s/integrations/copilot/room-wake.yml`, change the run step to
      `copilot -p "$prompt" -s --allow-all-tools`, and append to the prompt
      the sentence: `Write the reply in GitHub-flavoured markdown: put code
      in fenced blocks with a language, and do not describe the search steps
      you took.` Leave every other line unchanged. Run `test_room_wake.py`
      until it passes.

## 5. Stay mode in the skill

- [x] 5.1 [req: room-skill-loop, room-skill-stops] In
      `plugins/s/skills/room/tests/test_room_skill.py`, add assertions that
      the skill contains `/s:room [<pr>] [stay]`, a stay rule that re-enters
      `watch` after an empty wait, and a closed-room stop naming the `closed`
      line. Run and observe them fail.
- [x] 5.2 [req: room-skill-loop, room-skill-stops] In
      `plugins/s/skills/room/SKILL.md`, change the invocation line to
      `/s:room [<pr>] [stay]` and explain `stay`: the agent stays on the pull
      request for the whole review. In "When to stop", add a first bullet
      **Room closed**: `watch` printed a `closed` line, so the pull request
      merged or closed; report and stop. Scope the **Empty wait** bullet to a
      turn without `stay`, and add that with `stay` the skill re-enters
      `watch` with the cursor printed on stderr. Keep the foreground-only and
      prose-only sections unchanged. Run `test_room_skill.py` until it
      passes.

## 6. Docs and version

- [x] 6.1 [req: room-skill-loop, room-message-shape] Revise `docs/pr-room.md`
      to the documentation standard: add a section "Stay on the pull request"
      explaining `/s:room <pr> stay` and when it ends, and in "Run a turn by
      hand" note that a reply removes the agent's own `working` claim so each
      turn shows as one comment headed by the speaker's name. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/pr-room.md`
      and `wc -l docs/pr-room.md`; confirm exit 0 and 150 lines or fewer.
- [x] 6.2 [req: *] Bump `plugins/s/.claude-plugin/plugin.json`'s `version` one
      patch above `main`'s value at build time.
- [x] 6.3 [req: *] Run
      `python3 -B -m unittest discover -s plugins/s/skills/room/tests` and
      `python3 -B -m unittest discover -s plugins/s/skills/build/tests`, and
      confirm both report OK.
