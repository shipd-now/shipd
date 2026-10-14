# room-cli-verb
Status: verified
Epic: pr-room
Theme: developer-experience

## Idea

Add `shipd room join | list | message | close`: `room.py` beside the schema,
every GitHub call through an injectable `gh` runner, the `room` config key,
and the `cli-dispatch` amendment that routes the verb to the skill-local
script.

### Motivation

An agent on any harness can parse a room comment once `room-schema` lands,
but it still has no verb to join a PR, read its cards and tasks, or post a
state transition, so no two agents can hold the turn-taking conversation the
epic promises. This change is the harness-agnostic surface every later member
(`watch`, the skill, the CI wake, the gate) calls.

### Details

- New `plugins/s/skills/room/scripts/room.py` with `main(argv=None, gh=None)`
  and the four verbs; new `plugins/s/skills/room/tests/test_room.py` with a
  `FakeGh` dispatcher.
- `spec_common.py`: `room` joins `RECOGNIZED_CONFIG_KEYS`; `resolve_room(root)`
  returns `(agent, max_rounds)`; the example config and `docs/customise.md`
  gain the key; `test_spec_common.py` covers the resolver.
- `plugins/s/bin/shipd`: `room` in `VERB_TABLE` and the banner; a
  script-name-keyed directory override so `room.py` resolves under
  `skills/room/scripts/`; `test_shipd_cli.py` pins it.
- Plugin version advanced one patch above `main`'s value at build time.

Affected capabilities: `pr-room` (modified — the schema member adds it),
`shipd-cli` (modified), `shipd-config` (modified). Depends on `room-schema`
merging first: this plan imports its module as given and re-specifies none of
its requirements.

### Non-goals

- No `watch`, no `since` cursor, no actionable-task predicate (`room-watch`).
- No `/s:room` skill, harness body, cheatsheet or README rows (`room-skill`).
- No workflow template (`room-action-wake`); no change to `review_gate.py`
  (`room-gate-adoption`).
- No validation of `--to` against the cards: a human login is a valid
  addressee (epic: a human may be a task's explicit addressee).

## Implementation

- **Dispatch override, not a second table.** `VERB_TABLE["room"] =
  ("room.py", [])` keeps the per-verb test shape; a module constant
  `SKILL_SCRIPT_DIRS = {"room.py": PLUGIN_ROOT / "skills" / "room" /
  "scripts"}` is consulted at the exec site
  (`SKILL_SCRIPT_DIRS.get(script, SCRIPTS) / script`). Rejected: an in-binary
  `cmd_room` — the constitution keeps network code out of the engine and the
  binary, and `execv` makes the script's output and exit code the binary's
  own.
- **Runner seam copied from `review_gate.py:139-143`.** `_default_gh(args,
  input=None)` runs `["gh", *args]` and returns `(rc, stdout, stderr)`;
  `main(argv=None, gh=None)` takes `gh or _default_gh`; a `RoomError` raised
  anywhere is reported once through `cli_common.err` and exits `1`.
  `cli_common` and `spec_common` are imported after inserting
  `skills/build/scripts` on `sys.path`, as `drive.py:310-314` does;
  `room_schema` is a sibling import.
- **Room read.** `_resolve_room(gh, pr)` → `(repo, number, context)` via `gh
  pr view --json number,url` and `gh repo view --json nameWithOwner`
  (`review_gate._resolve_pr`/`_resolve_repo`). `_read_room(gh, repo, number)`
  calls `gh api repos/<repo>/issues/<n>/comments?per_page=100 --paginate
  --slurp` and the same over `pulls/<n>/comments` (the gate's finding tasks
  live on review comments), flattens both page lists, orders the union by
  comment id, parses each body with `parse_comments` (a gate summary carries
  a card and a Message), and returns `(cards, tasks, raw)`:
  cards are the parsed `AgentCard`s (last card per name wins), tasks are
  `build_tasks` over `(id, Message)` pairs in comment order, `raw` keeps the
  comment id per card for the upsert. Rejected: the gate's single
  `per_page=100` page — a long PR would silently lose tasks.
- **Posting.** `_post(gh, repo, number, body)` POSTs `{"body": body}` with
  `--input -`; `_patch(gh, repo, comment_id, body)` PATCHes; both return the
  parsed response (`id`, `html_url`). Bodies come from
  `room_schema.render_comment`, never hand-built.
- **Identity.** `_agent_name(opts, root)`: `opts.agent` → `SHIPD_ROOM_AGENT`
  → `resolve_room(root)[0]`; none → `parser.error("no agent name — pass
  --agent, set SHIPD_ROOM_AGENT, or declare room.agent")` (usage text, exit
  2). `message`/`close` require a card with that name on the PR.
- **State defaults (Q2).** A `--task` reply without `--state` posts
  `input-required` when `--to` is given, else `working`; `--new` without
  `--state` posts `input-required` with `--to`, else `submitted`.
  `next_state` runs first, so a terminal task fails before any cap check.
- **Cap (Q1).** `at_round_cap(task, agent, max_rounds)` runs after the
  transition check and before posting; at the cap the verb posts `failed` /
  `round-cap` at round `next_round(task, agent)` and exits `1` with the
  `Error:` line. `close` applies no cap. `max_rounds` is
  `--max-rounds` or `resolve_room(root)[1]`.
- **Card version.** `join` fills `version` from
  `plugins/s/.claude-plugin/plugin.json` (`HERE/../../../.claude-plugin/`),
  so a card names the plugin that drives the agent; `harness` and
  `description` are flags, empty when omitted.
- **Output shape.** Mutating verbs print one JSON object on stdout and one
  human line on stderr (the `review_gate` `_cmd_*` convention); `list` prints
  text or `--json`.
- **Config resolver.** `resolve_room(root)` after `resolve_pr_mode`
  (`spec_common.py:1097`): `resolve_config(root)`, absent key → `(None, 6)`;
  shape errors raise `ConfigError` naming the key, member, and provenance.
  Unknown members are ignored so `room-watch` can add its own later.

Risk: `--slurp` needs gh ≥ 2.46; guard by naming the flag in the `Error:`
reason when `gh api` fails. Risk: the schema API drifts before merge; the
first task re-reads the merged module and stops on any missing symbol.

## Questions and answers

### Q1: What does `message` exit with when the round cap fires?
- **Question:** Options: (1) post `failed`/`round-cap`, then exit 1 with an
  `Error: round cap reached on task <id> — posted failed (round-cap)` line;
  (2) exit 0, printing the posted message's JSON and a notice.
  Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1 — the caller's text was not delivered, and
  `cli-conventions` reports a fatal outcome as one `Error:` line and a
  non-zero exit, so a driving flow stops rather than reading a success.
- **Queued:** q-pr-room-message-round-cap-exit-code
- **Relied on by:** room-skill, room-action-wake

### Q2: What state does a `--task` reply carry without `--state`?
- **Question:** Options: (1) mirror the opener rule — `input-required` when
  `--to` is given, `working` otherwise; (2) require `--state` and exit 2
  when absent. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1 — the epic's loop posts `working` on pickup with no
  addressee and `input-required` back to the other party, so the two
  defaults match the two common replies; `completed` stays explicit.
- **Queued:** q-pr-room-task-reply-default-state

## Readiness attestation

### Problem and motivation

Once the schema lands, an agent can parse a room comment but has no verb to
join, read, or post, so no cross-harness conversation can start.

Evidence:

- Epic `pr-room` Design: "the verbs depend on the schema; the skill, the
  watch, and the gate each depend on the verbs".
- `plugins/s/bin/shipd` (`main`, line 2756-2780): `shipd room` falls to the
  usage banner and exits 2 today.

### Scope and non-goals

The change adds the four verbs, the config key, and the dispatch row; watch,
skill, workflow, and gate surfaces stay with their members.

Evidence:

- Epic `pr-room` Changes table rows `room-watch`, `room-skill`,
  `room-action-wake`, `room-gate-adoption`.
- `room-schema` plan `### Non-goals`: "No `gh` call, no verb, no `shipd`
  binary dispatch (`room-cli-verb`)".

### Affected capabilities and files

Three capabilities and eight files, because the verb needs a script, a
dispatch row, a config key, and the tests and docs that guard each.

Evidence:

- Capability `shipd-cli`: `cli-dispatch` (base `82c713fcb1e2`, from
  `spec_status.py base-hash`); capability `shipd-config` (`pr-mode-key`
  pattern at `spec.md:477`); capability `pr-room` (added by `room-schema`).
- Files: `plugins/s/skills/room/scripts/room.py` (new),
  `plugins/s/skills/room/tests/test_room.py` (new), `plugins/s/bin/shipd:80`
  (`VERB_TABLE`) and `:2822` (exec site),
  `plugins/s/skills/build/tests/test_shipd_cli.py:41-46` (`VERBS`),
  `plugins/s/skills/build/scripts/spec_common.py:395` and `:1097`,
  `plugins/s/skills/build/references/shipd.config.example.json`,
  `docs/customise.md:37-57`, `plugins/s/skills/build/tests/test_spec_common.py:3551`,
  `plugins/s/.claude-plugin/plugin.json`.
- Runnable premise: `plugins/s/bin/shipd room` → usage banner, exit 2.
- Runnable premise: `gh api --help` on gh 2.95.0 → lists `--paginate` and
  `--slurp`.
- Runnable premise: `python3 plugins/s/skills/build/scripts/version_guard.py
  --base main --head HEAD` → exit 0 on the untouched worktree.
- Runnable premise: `spec_status.py wiki-show --personal` → no personal store;
  the memory consultation was skipped.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- Dispatch override keyed by script name, runner seam, pagination, identity
  order, card version, output shape: settled by investigation of
  `bin/shipd`, `review_gate.py`, `drive.py`, and the epic Decisions.
- Round-cap exit code: PLANNER default, Q1.
- Default reply state: PLANNER default, Q2.
