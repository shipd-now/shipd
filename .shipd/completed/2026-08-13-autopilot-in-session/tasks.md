## 1. Mode selection and preflight

- [x] 1.1 [req: deliver-skill] In `plugins/s/skills/autopilot/SKILL.md`, add a
      mode-selection section directly after the requirements preamble: the skill
      runs the **in-session drive** by default, and the detached `claude -p`
      driver only when the invocation asks for a detached run (e.g.
      `/s:autopilot <epic> detached`, or the user asking for a detached or
      unattended run in words).
- [x] 1.2 [req: deliver-skill] In the same file's Phase 2 confirmation section,
      require the confirmation to name which mode the run will use, alongside the
      existing run controls and the `dashboard.py tui --epic <epic>` live-view
      command.
- [x] 1.3 [req: deliver-skill] In the same file, retitle the existing Phase 3 as
      the **detached** run path, leaving its `autopilot.py` invocation, foreground
      requirement, and Phase 4 report relay (needs-human and rejected pointers)
      unchanged and explicitly scoped to that mode.

## 2. The in-session drive loop

- [x] 2.1 [req: in-session-drive] In `plugins/s/skills/autopilot/SKILL.md`, add
      an in-session drive phase that obtains the member order and resolved
      pipeline by running `autopilot.py <epic> --dry-run` and parsing its printed
      member order, stating that the order is never re-derived in the skill.
- [x] 2.2 [req: in-session-drive] In that phase, specify the per-member entry
      stage mapping — `unplanned` enters at `plan`, `ready` enters at `build`, any
      other state is skipped and named in the summary with its state — and note it
      mirrors `_ENTRY_STAGE` in
      `plugins/s/skills/build/scripts/autopilot.py`.
- [x] 2.3 [req: in-session-drive] In that phase, specify per-member setup: create
      the worktree with
      `plugins/s/skills/build/scripts/worktree.sh <member>` (reusing it when it
      already exists), and run every stage for that member with that worktree as
      the working directory.
- [x] 2.4 [req: in-session-drive] In that phase, specify that each stage is run by
      spawning one **general-purpose** sub-agent via the Agent tool, whose message
      is that stage's instruction — the same shape `_stage_prompt` produces in
      `plugins/s/skills/build/scripts/autopilot.py` — and give the plan, build,
      and review stage instructions verbatim.
- [x] 2.5 [req: in-session-drive] In that phase, state that members run one at a
      time and that no headless `claude -p` process is started in this mode.

## 3. Grading and failure handling

- [x] 3.1 [req: in-session-disk-grading] In
      `plugins/s/skills/autopilot/SKILL.md`, add the grading rules as a table:
      plan passes when `spec_status.py status <member>` prints `ready` and
      `spec_lint.py <member>` exits 0; build passes when a `completed/` entry
      ending in `-<member>` exists and `gh pr view change/<member> --json url`
      yields a URL; review passes when the PR head's `semantic-review` status is
      `success` and `review_gate.py resolve --check` reports `unresolved=0`.
- [x] 3.2 [req: in-session-disk-grading] In the same section, state explicitly
      that a stage is graded by reading the repository and never by trusting the
      sub-agent's summary, so a sub-agent reporting success over an ungraded stage
      does not advance the drive.
- [x] 3.3 [req: in-session-asks-human] In the same file, add the failure contract:
      a failed stage grade and a gate rejection each stop the drive and put the
      situation to the user with the member and stage named; no further member is
      started while such a stop is unanswered; the in-session mode never parks a
      member as `needs-human` or `rejected`.
- [x] 3.4 [req: in-session-asks-human] In the same section, state that an
      interrupted in-session run needs no run-state file — re-invoking the skill
      for the same epic re-reads member state from disk and enters each member at
      its current state's stage.

## 4. Board liveness and the run summary

- [x] 4.1 [req: in-session-board-liveness] In
      `plugins/s/skills/autopilot/SKILL.md`, specify the per-member heartbeat:
      `heartbeat.py build-start <member>` when the member begins,
      `heartbeat.py build-stage <member> --stage <stage>` as each stage is
      entered, and `heartbeat.py build-finish <member> --outcome <outcome>` when
      it ends; note the verbs are fail-soft so a heartbeat failure never stops the
      drive.
- [x] 4.2 [req: in-session-drive] In the same file, specify the in-session run
      summary: shipped members with full PR URLs, members stopped for the user
      with the stage that stopped them, and skipped members with their state.

## 5. Ship the plugin change

- [x] 5.1 [req: *] Bump the `version` in
      `plugins/s/.claude-plugin/plugin.json` by one patch increment, as required
      for any change touching `plugins/s/`.
- [x] 5.2 [req: *] Run `bash -n` over
      `plugins/s/skills/build/scripts/worktree.sh` and
      `plugins/s/integrations/statusline.sh`, and run `python3 -m unittest
      discover -s plugins/s/skills/build/tests` to confirm this change broke no
      engine behavior.
- [x] 5.3 [req: *] Confirm
      `plugins/s/skills/build/scripts/autopilot.py` is unmodified by this change:
      run `git diff --stat -- plugins/s/skills/build/scripts/autopilot.py` and
      confirm it reports no changes.
- [x] 5.4 [req: *] Read `plugins/s/skills/autopilot/SKILL.md` end to end and
      confirm every script path it names resolves in the repository, and that the
      detached path's instructions are unchanged from before this change apart
      from being scoped to that mode.

## 6. Validator fix loop

- [x] 6.1 [req: in-session-drive] In `plugins/s/skills/autopilot/SKILL.md`,
      correct the "Member order and pipeline" section: the dry run's printed
      "Member order" contains only `unplanned` members, and every other member —
      including `ready` ones — appears in its `skipped:` lines as
      `skipped:    <member>  (<state>)`. Instruct parsing **both** sections and
      selecting the printed order first, then the skipped entries whose state is
      `ready`, in the order printed. Keep the rule that ordering is taken from the
      dry run and never re-derived in the skill.
- [x] 6.2 [req: in-session-drive] In the same file's "Entry stage per member"
      section, state explicitly that a `ready` member is reached via the skipped
      list (per 6.1) rather than via the printed member order, so the
      `ready` -> `build` row is actually reachable; and that only states other
      than `unplanned` and `ready` are left undriven.
- [x] 6.3 [req: in-session-board-liveness] In the same file's "Board liveness"
      section, correct the claim about what the heartbeat achieves: the per-member
      build heartbeat makes the board's activity indicator report the run as
      active rather than idle, but it does **not** move a member's card into the
      building lane — lane placement reads the member's on-disk lifecycle state
      and the epic-level run heartbeat that only the detached driver writes. State
      that a member driven from `unplanned` keeps an `unplanned` card until its
      plan sub-agent's first artifact write.
- [x] 6.4 [req: *] Re-read `plugins/s/skills/autopilot/SKILL.md` end to end and
      confirm no remaining sentence claims a `ready` member arrives via the
      printed member order, or that the build heartbeat moves a card into the
      building lane.
- [x] 6.5 [req: in-session-drive] In `plugins/s/skills/autopilot/SKILL.md`,
      correct Phase 1's "Show the roster" step: its claim that only `unplanned`
      members are driven is true of the detached mode only. State that the
      detached run drives `unplanned` members and reports every other state,
      while the in-session drive additionally drives `ready` members (entering at
      `build`), leaving only the remaining states undriven.
- [x] 6.6 [req: in-session-drive] In `plugins/s/skills/autopilot/SKILL.md`,
      correct the "Per-member setup" step. `worktree.sh` has no reuse path: a
      second invocation for the same member exits 1 with
      `error: .worktrees/<member> already exists`, so an interrupted run would
      hard-fail on resume. Instruct the drive to test for the existing directory
      first and only create it when absent — e.g. run
      `"${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/worktree.sh" <member>` only
      when `.worktrees/<member>` does not exist, and otherwise use the existing
      worktree as-is. Remove the claim that the script reuses an existing
      worktree.
