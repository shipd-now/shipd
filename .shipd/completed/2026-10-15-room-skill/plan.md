# room-skill
Status: verified
Epic: pr-room
Theme: developer-experience

## Idea

Add the `/s:room` skill and its harness body: join a PR's room, read it,
wait for this agent's turn with `shipd room watch`, reply, and close — with
a `docs/` how-to and the skill registered in `AGENTS.md`, the README, and
the cheatsheet.

### Motivation

Once the room verbs and `watch` land, an agent on any harness can speak the
protocol only if a person tells it every verb and flag by hand, so no two
agents can hold the epic's turn-taking conversation unprompted. This change
gives every harness one loop to follow, and it is the flow the CI wake later
runs.

### Details

- New `plugins/s/skills/room/SKILL.md`, `plugins/s/harness/bodies/room.md`,
  and `plugins/s/harness/references/room.md`.
- New `plugins/s/skills/room/tests/test_room_skill.py` in the room suite
  `room-cli-verb` adds to the `ci` discover list.
- New `docs/pr-room.md`; one-line additions to `AGENTS.md`, `README.md`, and
  `docs/cheatsheet.md`; the plugin version advances one patch above `main`'s
  value at build time.

Affected capabilities: `shipd-room` (added — the skill, after the
`shipd-<skill>` convention). Depends on `room-schema`, `room-cli-verb`, and
`room-watch` merging first; this plan uses their verbs as given and
re-specifies none of their requirements. It reads `room-gate-adoption`'s
`review-finding` skill name only as a string, so it does not wait on it.

### Non-goals

- No change to `room.py`, `room_schema.py`, `review_gate.py`, or any verb's
  flags, output, or exit codes.
- No workflow template or CI wake (`room-action-wake`).
- No code edits, commits, or pushes from inside `/s:room` (Q3).
- No `harness-command-bodies` delta: the id match is directory-driven.

## Implementation

- **Loop.** `/s:room [<pr>]` (PR defaults to the current branch's, as the
  verbs resolve it): (1) `shipd room join <pr> --skill review-finding
  --skill question --skill status` (Q2; user-named skills replace the
  list); (2) `shipd room list <pr>` to show the
  room; (3) `shipd room watch <pr> --since <cursor> --timeout 600` (Q5),
  cursor `0` on entry; (4) for each NDJSON line, `message --task <id>
  --state working`, do the work, then `message --task <id> --state
  completed` or `--state input-required --to <asker>`; (5) re-enter step 3
  with the last line's `cursor`. Every `message` call names `--state`, so
  the skill does not lean on `room-cli-verb`'s default-state rule.
- **Stops.** Empty `watch` (exit 0, empty stdout) → report the cursor and
  end the turn (Q1; relies on `room-watch` Q2 and Q3). `message` exit 1 with
  the round-cap `Error:` → report; the verb already posted `failed` (relies
  on `room-cli-verb` Q1). Any other non-zero exit → relay the `Error:` line
  and stop. No agent name → relay the verb's usage error and name the three
  sources; the skill never invents a name (epic identity Decision).
- **Foreground only.** `watch` runs in the foreground; the skill states that
  a delegated worker never backgrounds it (epic, autopilot rule).
- **Prose only (Q3).** The work step reads code and posts prose. A task
  needing a code change gets an `input-required` reply to the asker naming
  `/s:fix` or `/s:plan`. A `review-finding` task the head already addresses
  is closed `completed` with a note naming the commit (Q4).
- **Body.** `room.md` opens with the description marker and the preamble
  include; the loop sits under `<!-- if:background-tasks -->`; the `else`
  segment runs one `shipd room list <pr> --json`, reports the actionable
  tasks, and ends. Ungated text avoids `subagent`/`sub-agent`, so the
  empty-feature render test holds. A `file-references` gate points at
  `{refs}/room.md`, which holds the NDJSON fields and the stop list.
- **Docs.** `docs/pr-room.md` is a `how-to` linted by `docs_lint.py` in the
  `ci` docs step; flags stay in `shipd room --help`.

Risk: verb flags drift before merge; task 1.1 checks `shipd room --help` and
stops on a gap. Risk: the body nears the size ceiling owned by
`harness-command-bodies` (`body-content`); detail moves to the reference.

## Questions and answers

### Q1: What does `/s:room` do when `watch` returns empty?
- **Question:** Options: (1) report "no actionable task" with the cursor and
  end the turn; (2) re-enter `watch` at once, looping until a task arrives.
  Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1 — a bounded wait per invocation keeps a turn from
  spinning; the user or a later run re-enters with the reported cursor.
- **Queued:** q-pr-room-skill-watch-empty-return

### Q2: Which skills does `/s:room` put on the card by default?
- **Question:** Options: (1) `review-finding` only; (2) none, so only
  addressed tasks surface; (3) a broader list. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 3 — the card defaults to `review-finding`, `question`,
  and `status`, so the agent picks up unaddressed gate findings, questions,
  and status requests; user-named skills replace the list.
- **Queued:** q-pr-room-skill-default-card-skills

### Q3: May `/s:room` edit, commit, or push code?
- **Question:** Options: (1) no — prose replies only, code work handed to
  `/s:fix` or `/s:plan`; (2) yes, within the loop. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1 — the epic's non-goal rules out autonomous code
  changes triggered by a room message; the existing skills own code work.
- **Queued:** q-pr-room-skill-code-edits

### Q4: What does `/s:room` post on an already-addressed finding task?
- **Question:** Options: (1) close it `completed` with a note naming the
  commit or resolution; (2) close it `canceled`, reason `stale`; (3) leave
  it. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1 — the finding was resolved, not abandoned, and a
  closed task drops out of every later `watch`.
- **Queued:** q-pr-room-skill-stale-review-finding

### Q5: What `--timeout` does `/s:room` pass to `watch`?
- **Question:** Options: (1) always `--timeout 600`; (2) none
  interactively, bounded only unattended; (3) user-supplied, no default.
  Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1 — the verb has no default (`room-watch` Q2), so the
  skill bounds every foreground wait to ten minutes.
- **Queued:** q-pr-room-skill-watch-timeout

## Readiness attestation

### Problem and motivation

Without a skill, an agent knows the room verbs only when a person spells
them out, so no unprompted turn-taking happens.

Evidence:

- Epic `pr-room` Design: "**Skill (`/s:room` + harness body).** Join, list,
  pick the actionable task, do the work …; stop at the cap."
- `room-cli-verb` and `room-watch` non-goals both defer the skill here.

### Scope and non-goals

The skill, body, reference, doc, registrations, test, and version bump;
verbs, schema, gate, and CI wake stay with their owners.

Evidence:

- Epic Changes table row `room-skill`; `room-cli-verb` non-goal "No
  `/s:room` skill, harness body, cheatsheet or README rows (`room-skill`)".

### Affected capabilities and files

One new capability and nine files.

Evidence:

- `harness-command-bodies` `body-templates`: ids match `SKILL.md`
  directories; a gated body needs `plugins/s/harness/references/<id>.md`.
- `harness_registry.FEATURES` holds `background-tasks` and
  `file-references`; `bodies/build.md:108-116` is the gate precedent.
- Registration sites: `AGENTS.md:145-169`, `README.md` Orchestration table,
  `docs/cheatsheet.md:35-75`; `.github/workflows/ci.yml:87-97` lints `docs/`.
- Runnable premise: `harness_bodies.render("memory", (), refs_dir="X")` →
  45 lines; `commands()` → 27 ids.
- Runnable premise: `docs_lint.py docs/oracle.md` → exit 0;
  `version_guard.py --base main --head HEAD` → exit 0; `main` is `0.6.283`.
- Runnable premise: `wiki-show --personal` → no store; memory skipped.

### No open task-shaping decision

Every decision is settled by investigation or a PLANNER default.

Evidence:

- Explicit `--state`, agent-name refusal, capability name, docs type:
  investigation of the epic, sibling plans, and repo conventions.
- Empty watch, card skill, prose only, finding close, timeout: PLANNER
  defaults Q1–Q5.
