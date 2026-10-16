## 1. Shared resolve mutation

- [x] 1.1 [req: room-finding-thread-resolve] In
      `plugins/s/skills/room/tests/test_room_schema.py`, add a test that
      `room_schema.RESOLVE_THREAD_MUTATION` contains
      `resolveReviewThread(input:{threadId:$threadId})`, and in
      `plugins/s/skills/review/tests/test_review_gate.py` a test that
      `review_gate` has no `_RESOLVE_MUTATION` attribute and that `resolve`
      sends `room_schema.RESOLVE_THREAD_MUTATION` as its mutation query.
      Run both suites with `python3 -B -m unittest` and observe the new
      tests fail.
- [x] 1.2 [req: room-finding-thread-resolve] Move the `_RESOLVE_MUTATION`
      string from `plugins/s/skills/review/scripts/review_gate.py` to
      `plugins/s/skills/room/scripts/room_schema.py` as
      `RESOLVE_THREAD_MUTATION` (text unchanged), delete the old constant,
      and make `review_gate._resolve_thread` pass
      `room_schema.RESOLVE_THREAD_MUTATION`. Run
      `python3 -B -m unittest discover -s plugins/s/skills/review/tests`
      and `python3 -B -m unittest discover -s plugins/s/skills/room/tests`
      until both report OK.

## 2. Thread replies

- [x] 2.1 [req: room-finding-thread-reply, room-message-verb] In
      `plugins/s/skills/room/tests/test_room.py`, extend `FakeGh`: a POST on
      `repos/<repo>/pulls/<n>/comments` appends a review comment (fresh id,
      `user.login` `bot`, the payload `body`, `in_reply_to_id` from the
      payload's `in_reply_to`, an `html_url`) and returns it; a DELETE on
      `repos/<repo>/pulls/comments/<id>` removes a review comment; add a
      `review_posts()` helper returning `(in_reply_to, body)` per review
      POST. Keep every existing dispatch branch. Add a `review_msg_comment`
      helper (a `msg_comment` placed in `review_comments`). Add tests: (a)
      review comment 900 opens a `review-finding` task from
      `semantic-review`; `message 7 --task 900 --state working "looking"`
      as `claude-b` records one POST on the `pulls` endpoint path `repos/<owner>/<repo>/pulls/7/comments` with
      `in_reply_to` 900 and a marker holding `taskId` 900, and no issue
      POST; (b) with review comment 950 a `working` claim from `claude-b`
      on task 900, `message 7 --task 900 --state input-required --to
      semantic-review "why?"` records the thread POST then a DELETE of
      the `pulls` endpoint path `repos/<owner>/<repo>/pulls/comments/950`; (c) an issue task reply still POSTs
      on the `issues` endpoint path `repos/<owner>/<repo>/issues/7/comments`; (d) `message --task 900` at the
      round cap posts its `failed` Message on the thread; (e) a `watch 7
      --once --max-rounds 1` round-cap post on task 900 is on the thread.
      Run `python3 -B -m unittest plugins/s/skills/room/tests/test_room.py`
      and observe (a), (b), (d), (e) fail.
- [x] 2.2 [req: room-finding-thread-reply, room-message-verb] In
      `plugins/s/skills/room/scripts/room.py`: add
      `_finding_root(comments, task)` returning `task.id` when the comment
      whose `id` equals `task.id` has `_endpoint(...) == "review"`, else
      `None`; add `_post_reply(gh, repo, number, thread, body)` running
      `gh api -X POST repos/<repo>/pulls/<n>/comments --input -` with
      `{"body": body, "in_reply_to": thread}` through `_gh_json`; give
      `_post_message` a `thread=None` keyword that routes to `_post_reply`
      when set (keep any `login`/`role` keywords already there). Pass
      `thread=_finding_root(comments, task)` from `cmd_message`'s reply and
      cap paths, `cmd_close`, and `_cap_task` (give `_cap_task` the
      `comments` list `cmd_watch` already holds). Change `_own_claim` to
      accept a last comment from either endpoint and return `(id,
      endpoint)` or `None`, and `_drop_claim` to DELETE
      `repos/<repo>/pulls/comments/<id>` for `review` and the issue path
      otherwise, keeping the existing warning text. Update the module
      docstring. Run `test_room.py` until it passes.

## 3. Resolve on completed

- [x] 3.1 [req: room-finding-thread-resolve] In
      `plugins/s/skills/room/tests/test_room.py`, extend `FakeGh` to answer
      `["api", "graphql", ...]`: a query carrying `reviewThreads` returns
      the configured threads (`{"id", "isResolved", "comments": {"nodes":
      [{"databaseId": ...}]}}`), a query carrying `resolveReviewThread`
      marks the thread named by `threadId=<id>` resolved; record both, and
      allow failing either through `fail`. Add tests on finding task 900
      with thread `PRRT_1`: (a) `close 7 --task 900 "Fixed in abc1234"`
      records the thread POST, the lookup, then the mutation with
      `threadId=PRRT_1`, exit 0; (b) `message 7 --task 900 --state
      completed "done"` resolves the same way; (c) `close --state
      canceled` records no mutation; (d) an already resolved thread gets no
      mutation; (e) a failing mutation prints `warning: could not resolve
      the review thread for task 900`, stdout holds the reply JSON, exit 0;
      (f) no matching thread prints the same warning, exit 0; (g) a
      completed reply on an issue task makes no `graphql` call. Run
      `test_room.py` and observe (a), (b), (d), (e), (f) fail.
- [x] 3.2 [req: room-finding-thread-resolve] In
      `plugins/s/skills/room/scripts/room.py`, add `THREAD_LOOKUP_QUERY`
      (variables `$owner:String!`, `$name:String!`, `$number:Int!`;
      `repository.pullRequest.reviewThreads(first:100)` with `id`,
      `isResolved`, `comments(first:1){nodes{databaseId}}`) and
      `_resolve_finding_thread(gh, repo, number, task_id)`: run `gh api
      graphql -f query=<q> -f owner=<o> -f name=<n> -F number=<n>`, pick
      the thread whose first comment's `databaseId` equals `task_id`, and
      when it is unresolved run `gh api graphql -f
      query=<room_schema.RESOLVE_THREAD_MUTATION> -f threadId=<id>`; a
      missing thread, a non-zero exit, or unparseable output writes exactly
      `warning: could not resolve the review thread for task <id>` (lower
      case, through `sys.stderr.write`) and returns. Call
      it from `cmd_message` and `cmd_close` after `_drop_claim` when the
      posted state is `completed` and `_finding_root(...)` is not `None`.
      Run `test_room.py` until it passes.

## 4. Skill text

- [x] 4.1 [req: room-skill-no-code] In
      `plugins/s/skills/room/tests/test_room_skill.py`, add tests that the
      flattened `SKILL.md` contains `author`, `review-finding`,
      `headRefName`, `git push`, `--force`, `/s:fix`, `/s:plan`, and
      `never edits, commits, or pushes code`, and that
      `hb.render("room", ("background-tasks",), refs_dir=REFS)` contains
      `author`, `headRefName`, `/s:fix`, and `/s:plan`. Run
      `python3 -B -m unittest plugins/s/skills/room/tests/test_room_skill.py`
      and observe failures.
- [x] 4.2 [req: room-skill-no-code] In `plugins/s/skills/room/SKILL.md`,
      replace the `## Prose only` section with `## Prose, and the author's
      fix`: the role is the `role` on this agent's own card in `shipd room
      list <pr> --json`; with role `author` on a surfaced `review-finding`
      task, check `gh pr view <pr> --json headRefName` equals `git branch
      --show-current` and `git status --porcelain` is empty, make the
      smallest fix, run the tests covering the touched files, `git
      commit`, plain `git push` (never `--force`, never another branch),
      then `shipd room close <pr> "Fixed in <short sha>: <one line>" --task
      <id> --state completed`, which replies on the finding's thread and
      resolves it; if any check or the tests fail, push nothing and use the
      prose hand-off. Every other role never edits, commits, or pushes
      code and hands off to `/s:fix` or `/s:plan`. Update the frontmatter
      `description` to match, and step 4's bullets to point at this
      section. Keep the existing loop and stop text.
- [x] 4.3 [req: room-skill-no-code] Apply the same rule, shortened, to
      `plugins/s/harness/bodies/room.md` (the paragraph beginning "You post
      prose only" and the description marker) and to the `## Replies`
      section of `plugins/s/harness/references/room.md`. Run
      `test_room_skill.py` until it passes.

## 5. Docs and version

- [x] 5.1 [req: room-skill-docs] In `docs/multi-agent-pr.md`, replace the
      paragraph "Room traffic uses issue comments only. ..." with: room
      traffic uses issue comments, except a review finding, whose messages
      reply on the finding's own review thread; a `completed` reply resolves
      that thread, so the merge's conversation check sees it closed. Keep the
      file at 100 lines or fewer. In `docs/pr-room.md`, rewrite `## Keep the
      room to prose` to state that an agent with role `author` commits a
      finding's fix to its own pull request and closes the task naming the
      commit, while every other role answers in prose and hands off to
      `/s:fix` or `/s:plan`. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py
      docs/multi-agent-pr.md docs/pr-room.md` and confirm exit 0.
- [x] 5.2 [req: *] Bump `plugins/s/.claude-plugin/plugin.json`'s `version`
      one patch above `main`'s value at build time.
- [x] 5.3 [req: *] Run `python3 -B -m unittest discover -s
      plugins/s/skills/room/tests`, `python3 -B -m unittest discover -s
      plugins/s/skills/review/tests`, and `python3 -B -m unittest discover
      -s plugins/s/skills/build/tests`; grep each output for `OK` and
      confirm none reports `FAILED`.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 2 | 586 |
| **Total** | 2 | 586 |
