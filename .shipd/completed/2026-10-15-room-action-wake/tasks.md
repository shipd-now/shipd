## 1. Precondition and version

- [x] 1.1 [req: room-wake-workflow-template] Merge `main` into the change
      branch after `room-schema`, `room-cli-verb` and `room-watch` have
      merged; confirm `plugins/s/skills/room/scripts/room.py` exists with the
      `join`, `list`, `message`, `close` and `watch` subcommands, that
      `message` accepts `--task`, `--to`, `--state` and a positional text
      after `--`, that `close` accepts `--state` and `--reason`, and that a
      `watch` NDJSON line carries `comment`, `to`, `last_agent`, `text` and a
      task id under `task` or `id`. Stop and report if any is missing.
- [x] 1.2 [req: copilot-room-wake] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` to one patch above the value
      `main` carries.

## 2. Copilot verb --room

- [x] 2.1 [req: copilot-room-wake, copilot-verb] In
      `plugins/s/skills/build/tests/test_copilot_verb.py` add tests for the
      five `copilot-room-wake` scenarios and one asserting plain `remove`
      leaves an installed wake set in place; run them and observe them fail.
- [x] 2.2 [req: copilot-room-wake] In `plugins/s/bin/shipd` add constants
      `ROOM_WAKE_WORKFLOW` (`.github/workflows/room-wake.yml`),
      `ROOM_RUNTIME_DIR` (`.github/shipd-room`) and `ROOM_RUNTIME`, an
      ordered tuple of the five plugin-relative paths named in the plan,
      plus `ROOM_MANAGED` (workflow first, then the five runtime targets).
- [x] 2.3 [req: copilot-room-wake] In `plugins/s/bin/shipd` add
      `room_wake_states(root, version)` returning `[(relative, state,
      detail)]` in `ROOM_MANAGED` order, mirroring `copilot_states`: the
      workflow by its `# shipd-copilot v(\S+)` marker; each runtime file
      `foreign` when the workflow marker is absent, `stale` when its bytes
      differ from `PLUGIN_ROOT/<path>`, else `installed`; the workflow
      downgraded to `stale` while any runtime file is not `installed`.
- [x] 2.4 [req: copilot-room-wake] In `plugins/s/bin/shipd` add
      `_room_add(root, version)` (render the template via the `{version}`
      replace, read the five runtime files and their source modes, prepare
      all payloads before writing, write each with `_atomic_write`, print
      `wrote <path>` lines) and `_room_remove(root)` (delete owned files,
      then `os.rmdir` each directory under `.github/shipd-room` deepest
      first while empty, stopping at the first non-empty one).
- [x] 2.5 [req: copilot-room-wake, copilot-verb] In `cmd_copilot` add a
      `--room` store_true flag: with `add`/`remove` it computes foreign
      paths from `room_wake_states` and dispatches to `_room_add` /
      `_room_remove`; without it the existing four-file path runs unchanged;
      the bare report prints the existing block, then `room wake set:` and
      one `  <state> <path> — <detail>` line per `room_wake_states` entry.
      Run the 2.1 tests and the whole `test_copilot_verb.py` until they pass.

## 3. Workflow template

- [x] 3.1 [req: room-wake-tests] Create
      `plugins/s/skills/room/tests/test_room_wake.py` with helpers that read
      `plugins/s/integrations/copilot/room-wake.yml`, split it into the
      `guard`, `run` and `reply` job texts by their `  <name>:` headers, and
      extract a step's `run: |` block by step name; a recording stub
      `room.py` (writes its argv as one JSON line to a log, prints canned
      stdout from an env var) placed at
      `room.py` under `.github/shipd-room/` in a temp dir; and a
      runner that rewrites `/usr/bin/python3` to `sys.executable`, sets
      `GITHUB_OUTPUT` to a temp file, and runs the script with `bash`.
- [x] 3.2 [req: room-wake-workflow-template] In `test_room_wake.py` add
      tests for the five `room-wake-workflow-template` scenarios plus: the
      first line is `# shipd-copilot v{version}`; both triggers carry
      `types: [created]`; the guard `if:` names `vars.SHIPD_ROOM_AGENT`
      and `<!-- shipd-room `; `run` installs `@github/copilot@1.0.80`; the
      guard reports not-actionable when `COPILOT_CONFIGURED` is `false`.
      Run them and observe them fail.
- [x] 3.3 [req: room-wake-workflow-template] Write
      `plugins/s/integrations/copilot/room-wake.yml` per the plan's
      "Three jobs", "Triggers and prefilter", "Guard step", "Runner step",
      "Reply state" and "Credential hygiene" decisions: header comment
      explaining the jobs, the variable, the secret and the
      no-self-trigger limit; top-level `permissions: contents: read`;
      `guard` and `reply` with `issues: write` and `pull-requests: write`;
      the PR number as `github.event.issue.number ||
      github.event.pull_request.number`; the guard's
      `COPILOT_CONFIGURED: ${{ secrets.COPILOT_GITHUB_TOKEN != '' }}`;
      multi-line outputs written with a random heredoc delimiter. Run the
      section 3 tests until they pass.

## 4. Docs

- [x] 4.1 [req: copilot-room-wake] Create `docs/room-wake-reference.md`
      (a reference doc; `docs/copilot-review-reference.md` is at its
      250-line cap) covering the room wake set: a table of the six paths
      and their roles, the `shipd copilot add --room` / `remove --room`
      verbs, the `SHIPD_ROOM_AGENT` variable, the `COPILOT_GITHUB_TOKEN`
      secret, the reply marker line, and the known limit that replies
      posted with the workflow token wake no other workflow. Add a pointer
      to it from `docs/copilot-review-reference.md` without taking that
      doc over its cap (fold it into an existing line or sentence). Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py` on both
      docs and fix its findings until it exits 0.

## 5. Verification

- [x] 5.1 [req: *] Run `python3 -B -m unittest discover -s
      plugins/s/skills/room/tests -v` and `python3 -B -m unittest discover
      -s plugins/s/skills/build/tests -v`; grep each output for `OK` and
      `FAILED` (not the tail). Run `python3
      plugins/s/skills/build/scripts/version_guard.py --base main --head
      HEAD` and `python3 plugins/s/skills/build/scripts/spec_lint.py
      room-action-wake`; all exit 0.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 92 | 19.2k |
| (no tool) | 0 | 6.4k |
| Read | 7 | 1.3k |
| SubagentHandback | 8 | 74 |
| Write | 7 | 74 |
| Agent | 5 | 8 |
| **Total** | 119 | 27.1k |
