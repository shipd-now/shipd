# autopilot-unattended-run
Status: verified
Epic: autopilot-preflight
Theme: reliability
Planned-at: 74b18964fded67e7d7be448ebcff7c4a6eae5836
Gated-hash: b8cb6ea1fbc4

## Idea

Make `/s:autopilot`'s in-session drive unattended for real: Phase 1 runs the
launch preflight and any `fail` stops the launch, the Phase 2 confirmation
becomes the last question, every build entry is preceded by a sync-and-drift
step whose `revise` verdict re-plans without a human, and every failure parks
the member while the drive carries on with the members that do not depend on
it.

### Motivation

A user who launches `/s:autopilot` expects to walk away, but the in-session
drive still stops on the first failed grade or gate rejection and asks, builds
on plans nobody re-checked against `main`, and never tells a plan stage that
no one is present — so the user returns to a waiting question instead of a
report.

### Details

- Phase 1 runs `autopilot.py <epic> --preflight`; a `fail` line stops before
  Phase 2; `warn` lines ride into the confirmation brief.
- Before each member's build entry: `git fetch origin main` and `git merge
  --no-edit origin/main` in its worktree, `spec_status.py drift <member>
  --base origin/main --json`, and on drift a `/s:drift` sub-agent — `holds`
  builds, `revise` re-plans in place and re-gates with `--base origin/main`,
  `conflict` parks.
- A failed grade, gate rejection, failing command entry, sync conflict, or
  drift error or conflict parks the member; dependents are held; the drive
  continues; a bounded merge wait covers dependents of a shipped member.
- The plan-stage and re-plan instructions state that no human is present.
- The final report lists shipped, parked (reason and resume pointer), blocked,
  and skipped members.

Affected capabilities: `epic-autopilot` (modified `deliver-skill`,
`in-session-drive`; removed `in-session-asks-human`; added
`in-session-prebuild-drift`, `in-session-park-and-continue`,
`in-session-unattended-prompts`). Impact:
`plugins/s/skills/autopilot/SKILL.md`, `plugins/s/harness/bodies/autopilot.md`,
`plugins/s/harness/references/autopilot.md`, new
`plugins/s/skills/build/tests/test_autopilot_skill_contract.py`,
`plugins/s/.claude-plugin/plugin.json`. No engine code, no new dependency.

### Non-goals

- No change to `autopilot.py`'s run path, `_stage_prompt`, or any engine verb:
  `detached-drift-replan` owns the detached driver.
- No change to `/s:plan`, `/s:drift`, or the gate; the no-human contract lives
  in this drive's own spawn instructions.
- No new status for a parked member; the six plan statuses stay.
- No change to the detached mode's Phase 3 and 4 beyond the shared Phase 1.

## Implementation

- **Phase 1 is the preflight verb.** Step 1 runs `autopilot.py <epic>
  --preflight` (text form) and relays every line; any `fail` stops the flow,
  naming the failing lines and their remedies, driving nothing; `warn` lines
  are carried into the Phase 2 brief. `epic-show`, `pipeline-show`, and the
  dry run stay as roster and preview. Rejected: re-deriving the checks in the
  skill — the verb composes them.
- **The confirmation is the last question.** Phase 2's AskUserQuestion stays;
  after it the in-session drive issues no AskUserQuestion and no typed round.
  Because the `members` check fails on `unplanned` and `draft`, a launched run
  holds only `ready` and `archived` members, so the first `--waves` call
  returns build waves only; the plan-stage instruction stays for the entry
  walk's completeness and gains the no-human paragraph.
- **Pre-build step**, once per member, when its walk reaches an entry whose
  `stage` is `build` (built-in or replaced), before that entry's heartbeat:
  1. Sync (Q1): in `.worktrees/<member>` run `git fetch origin main`, then
     `git merge --no-edit origin/main`; a non-zero merge runs `git merge
     --abort` and parks `sync-conflict`.
  2. Measure: `spec_status.py --root .worktrees/<member> drift <member> --base
     origin/main --json`; exit 0 builds; exit 4 judges; exit 1 parks
     `drift-error` with the `Error:` line.
  3. Judge (Q3): spawn one general-purpose sub-agent, cwd the worktree, with
     the drift instruction (a verbatim block in the skill: run `/s:drift
     <member> --base origin/main --json` and end the turn with that object
     alone); read `verdicts[0].verdict`; a missing or unparseable object parks
     `drift-error`.
  4. `holds` builds; `conflict` parks `drift-conflict` naming the verdict's
     `contradicts`; `revise` spawns one sub-agent with the re-plan instruction
     (verbatim block): revise `planned/<member>/` in place per the verdict's
     `revise:` pointer and reason, no human present, oracle before own
     recommendation, never a question, never against a `USER` entry or an
     epic Decision, then `spec_gate.py <member> --base origin/main`. Grade
     from disk — `spec_status.py status <member>` prints `ready`,
     `spec_lint.py <member>` exits 0, `spec_gate.py <member> --check` exits 0
     — else park `replan-failed`. Then build; the step does not repeat.
  Rejected: the verbs' default `main` base — from a worktree the fetched tip
  is not reachable as local `main` (`fetch origin main:main` is refused while
  `main` is checked out), and the re-gate's stamp must anchor on the same ref
  the measurement used.
- **Park and continue.** The parked set lives in the session — no run-state
  file, and the plan statuses are the fixed six. Reasons: `grade-failed
  <stage>`, `gate-rejected`, `command-failed <entry> exit <rc>`,
  `sync-conflict`, `drift-error`, `drift-conflict`, `replan-failed`. On a
  park: `heartbeat.py build-finish <member> --outcome parked`, no further
  entry for that member, the wave's other in-flight sub-agents run to their
  end and are graded, and the next round and wave continue. Every `--waves`
  re-run is preceded by `git fetch origin main`; parked members are dropped
  from the returned waves, and a `blocked` entry whose `waiting_on` names a
  parked or held member is marked held (to a fixpoint); a wave emptied this
  way is skipped. Rejected: asking — the epic names Phase 2 as the last
  question.
- **Merge wait (Q2).** When no runnable wave remains but `blocked` holds
  entries that are not held, poll `gh pr view change/<dep> --json state` for
  each `waiting_on` every 60 seconds, up to the confirmed `--timeout` seconds
  in total; once every such dependency is `MERGED`, fetch and re-run
  `--waves`; on the bound expiring or a `CLOSED` state, end the run listing
  those members as blocked. The driven build already watches its own PR to
  `MERGED`, so the wait is a backstop for a timed-out ship.
- **Prompts.** The plan-stage instruction and the re-plan instruction both
  end with the paragraph: no human is available during this run; consult the
  oracle for a decision the repository cannot settle; on `INSUFFICIENT` adopt
  the recommended default and record it in the ledger; never open a question
  round or an AskUserQuestion.
- **Report.** Shipped by wave with full PR URLs; Parked per member with its
  reason, stage or step, and pointer from the reference's table:
  `gate-rejected` and `replan-failed` at `rejected` → `/s:plan <member>`;
  `grade-failed build`, `command-failed`, `sync-conflict` → `/s:build
  <member>` in `.worktrees/<member>` or re-run `/s:autopilot <epic>`;
  `grade-failed review` → the review instruction's post flow on the PR URL;
  `drift-conflict` → settle the named `Q<n>` or Decision (`/s:epic <epic>
  amend` for a Decision), re-gate, re-run `/s:autopilot <epic>`; Blocked as
  `held by <parked>` or `waiting on <dep>` with the re-run pointer; Skipped
  with state.
- **Harness text.** Body step 1 runs `--preflight` and stops on `fail`; the
  `subagents` gate paragraph describes the in-session drive as parking and
  continuing with a pre-build drift step; step 4 gains a parked line. The
  body stays under 150 rendered lines (107 today) and keeps `subagent` and
  `AskUserQuestion` inside gates. The reference's "Failure contract" and
  "Resuming" sections are rewritten and a "Pre-build drift step" section with
  the pointer table is added.
- **Contract test** `test_autopilot_skill_contract.py` in the shape of
  `test_epic_grill_contract.py` pins the vocabulary across skill, body, and
  reference.
- **Version bump** `plugins/s/.claude-plugin/plugin.json` to the next patch
  above `main` at build time (`0.6.293` when planned).

Risks: a `revise` sub-agent that re-gates without changing anything passes the
grade — accepted, the trust the detached enrich path already grants; the merge
wait spends wall-clock inside the session — bounded by `--timeout`.

## Questions and answers

### Q1: Which ref does the pre-build sync and drift step anchor on?
- **Question:** Options: (1) in the worktree `git fetch origin main` and
  `git merge --no-edit origin/main`, then pass `--base origin/main` to
  `spec_status.py drift`, `/s:drift`, and the re-gate `spec_gate.py <member>
  --base origin/main`, never touching the main checkout; (2) fast-forward the
  main checkout's `main` and leave every verb on its default base.
  Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** USER accepted the default, one decision with
  detached-drift-replan Q1: `git fetch origin main`, then `origin/main` where
  it resolves else `main`, merged into the worktree and passed as `--base` to
  the drift verb, `/s:drift`, and the re-gate; the main checkout is untouched.
- **Queued:** q-autopilot-drift-sync-base-ref

### Q2: Does the drive wait for a shipped dependency's PR to merge?
- **Question:** Options: (1) wait, bounded — poll `gh pr view change/<dep>
  --json state` every 60 seconds up to `--timeout`, fetch and re-run
  `--waves` on `MERGED`, end listing the dependents as blocked on the bound
  or `CLOSED`; members blocked on a parked member are never waited for; (2)
  stop at once as wave-dependency-order's text says. Recommendation: (1).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option 1. The epic frames build waves as waiting for the
  dependency's merge and makes the launch confirmation the last question of a
  run that goes to its end; the sibling's stop wording is a pending PLANNER
  default, and the house pattern is a bounded PR watch that is acted on, not
  awaited forever.
- **Cited:** epic/autopilot-preflight, verified/build-spec-lifecycle,
  verified/epic-autopilot

### Q3: How does the drive obtain the drift verdict and run the re-plan?
- **Question:** Options: (1) one general-purpose sub-agent per flagged
  member running `/s:drift <member> --base origin/main --json` and ending
  with the object, then on `revise` a second sub-agent revising
  `planned/<member>/` in place under the no-human rule and re-gating, graded
  from disk; (2) the orchestrator invokes `/s:drift` through the Skill tool
  and revises in its own context. Recommendation: (1).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option 1. The skill never plans a member itself and a re-plan
  is planning; the drive's mechanism for every model-run stage is a sub-agent
  in the worktree graded from the repository; the no-human contract belongs
  in this drive's spawn instruction and delta, not in `/s:plan` or
  `/s:drift`.
- **Cited:** verified/epic-autopilot,
  queue q-epic-grill-deferred-question-contract-home, epic/autopilot-preflight

## Readiness attestation

### Problem and motivation

The in-session drive stops and asks on the first failure, builds on
unre-checked plans, and never tells a plan stage that no one is present.

Evidence:

- Epic `autopilot-preflight`: Introduction, Decisions "The launch
  confirmation is the last question" and "Mid-run drift is re-planned, not
  asked", Design "Orchestration layer".
- `plugins/s/skills/autopilot/SKILL.md:440-462` — "Failure contract: ask,
  never park"; `:280-284` — the plan instruction names no absence of a human.

### Scope and non-goals

Skill text, harness body and reference, one contract test, and the manifest;
the detached driver, the verbs, `/s:plan`, and `/s:drift` stay out.

Evidence:

- Epic `## Changes` rows `detached-drift-replan` (the run path) and
  `grill-preflight-handoff`; `autopilot.py:587-640` `_stage_prompt` is not
  edited.
- `drift-skill` plan `### Non-goals`: the loop around the verdict belongs
  here.

### Affected capabilities and files

One capability and five files, because the drive is skill prose with a
harness mirror and a test pinning its vocabulary.

Evidence:

- `epic-autopilot`: `deliver-skill` base `7c347a4f3a75`, `in-session-drive`
  base `f5cd571e1a2b`, `in-session-asks-human` base `7c3cf0ae8089`.
- `plugins/s/skills/autopilot/SKILL.md:52-121` Phases 1–2, `:220-244`
  "Running a wave", `:271-315` stage instructions, `:406-424` grading,
  `:440-470` failure contract and resume, `:496-505` run summary;
  `plugins/s/harness/bodies/autopilot.md:11-28`, `:73-79`, `:81-99`;
  `plugins/s/harness/references/autopilot.md:95-118`;
  `plugins/s/skills/build/tests/test_epic_grill_contract.py:1-30`;
  `test_harness_bodies.py:197` forbidden tokens, `:436-455` the 150 ceiling.
- Runnable: `autopilot.py autopilot-preflight --waves --parallel 3 --json` →
  one object with `waves`, member `after` lists, `skipped`, exit 0.
- Runnable: `gh pr view <merged PR> --json state,mergedAt,headRefName` →
  `"state":"MERGED"`, exit 0.
- Runnable: `git fetch origin main:main` → `fatal: refusing to fetch into
  branch 'refs/heads/main' checked out at …`; `git fetch origin main` → exit
  0; `git -C .worktrees/autopilot-unattended-run merge-base HEAD origin/main`
  → `eef0a72…`.
- Runnable: `harness_bodies.render('autopilot', FEATURES)` → 107 lines;
  bare render → 104 lines.
- Runnable: `spec_status.py locate autopilot-unattended-run` → exit 1 (fresh
  name); `/s:plan`'s locate branch reports and stops on any non-`rejected`
  status (`skills/plan/SKILL.md` "Enrichment mode").
- Runnable: `heartbeat.py build-finish --help` → `--outcome OUTCOME` is
  free-form.

### No open task-shaping decision

Three decisions existed; all are settled.

Evidence:

- Sync and drift base ref: PLANNER default, Q1, oracle `INSUFFICIENT`.
- Bounded merge wait: oracle, Q2.
- Verdict and re-plan as sub-agents: oracle, Q3.
- Park reasons, held-dependent rule, step placement, pointer table:
  investigation.
