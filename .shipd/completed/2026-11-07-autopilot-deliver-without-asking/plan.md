# autopilot-deliver-without-asking
Status: verified
Planned-at: 03600e3627f6d86762314e2623d9979d8e0322d4
Gated-hash: 0de20ec2752d

## Idea

`/s:autopilot <epic>` starts delivering every driven member the moment it is invoked, with no confirmation question.

### Motivation

A user who calls `/s:autopilot` to deliver an epic unattended gets stuck: the skill stops at a run-controls dialog and drives nothing until someone answers. A user who wants a narrower run, such as only the first member, says so in the invocation instead.

### Details

- Replace Phase 2's AskUserQuestion ("Deliver all members", "Deliver one member first", "Cancel") with a printed **launch brief**, then drive at once.
- Read the run controls (`--max-members`, `--timeout`, `--max-resumes`, `--parallel`) from the invocation, flags or plain words; every control not named takes its default.
- Keep the failing-preflight stop as the run's only stop before the drive.
- Mirror the change in the harness body and reference, the `epic-autopilot` spec, and the contract test; bump the plugin version.

Affected capabilities: `epic-autopilot` (modified: `deliver-skill`, `in-session-park-and-continue`). Impact: `plugins/s/skills/autopilot/SKILL.md`, `plugins/s/harness/bodies/autopilot.md`, `plugins/s/harness/references/autopilot.md`, `plugins/s/skills/build/tests/test_autopilot_skill_contract.py`, `plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No change to `autopilot.py`, its flags, or its defaults.
- No change to the preflight rubric or its `fail` stop.
- No change to `/s:epic-grill`'s hand-off to `/s:autopilot`.

## Implementation

- **Controls come from the invocation.** The skill maps flags (`--max-members 1`) and plain words ("just the first spec", "one member", "serial") to the four controls; any control not named takes its default (`--max-members` unlimited, `--timeout` 1800, `--max-resumes` 4, `--parallel` 3). Rejected: keeping the dialog with "Deliver all" preselected — any dialog still blocks an unattended call.
- **No Cancel option.** A user who does not want a run does not invoke the skill. Rejected: a "type cancel within N seconds" window — it adds a wait for no gain.
- **Launch brief replaces the dialog.** Phase 2 becomes "Phase 2 — Launch brief": print the mode, the resolved controls with which came from the invocation, the dry run's member list, the `--waves --parallel N` output for in-session runs, every `warn` line, and the `dashboard.py tui --epic <epic>` live-view command. Then start the drive in the same turn. The skill issues no AskUserQuestion and no typed question round anywhere in the run.
- **In-session `--max-members N`.** The in-session drive drives at most N members, taken in the waves mode's order; the rest are reported as unreached. This keeps "just the first spec" meaningful in the default mode.
- **Harness body.** `plugins/s/harness/bodies/autopilot.md` section 2 becomes "Launch brief"; keep its controls table; delete its three-choice paragraph, its "Brief every question" paragraph, and its `<!-- if:question-dialogs -->` block, since the body asks nothing.
- **Wording anchors.** Replace "the last question of the run" with "The run asks no question" in the skill and body; replace "After the Phase 2 confirmation" / "After the launch confirmation" with "Once the launch brief prints".
- **Test.** `test_confirmation_is_the_last_question` becomes `test_the_run_asks_no_question`: assert "The run asks no question" in skill and body, and assert neither contains "Deliver one member first" nor "AskUserQuestion to confirm".

- **Question-brief roster.** `test_question_brief_contract.py` classifies a skill as asking when its SKILL.md names `AskUserQuestion`; autopilot now names it only in prohibitions, so the roster skips any skill stating "The run asks no question". Rejected: rewording the prohibitions to avoid the literal, which weakens them.

Risk: a user launches a full run by mistake and spends model time. The launch brief names the controls and the dashboard first, and the preflight still blocks an unapproved epic, so the epic approval stays the human gate.

## Readiness attestation

### Problem and motivation

`/s:autopilot` stops at a confirmation dialog before it drives anything, so a user calling it to deliver unattended gets stuck.

Evidence:

- `plugins/s/skills/autopilot/SKILL.md:94-129` issues the AskUserQuestion with three choices.
- Requirement `deliver-skill` mandates "confirm the run controls with the user — the last question of the run".

### Scope and non-goals

The skill, its harness body and reference, two requirements, and one test change; the driver, preflight, and epic-grill stay untouched.

Evidence:

- In scope: `plugins/s/skills/autopilot/SKILL.md:94-140`, `plugins/s/harness/bodies/autopilot.md:39-66`, `plugins/s/harness/references/autopilot.md:134`.
- Out of scope: `plugins/s/skills/build/scripts/autopilot.py`, `plugins/s/skills/epic-grill/SKILL.md:255-269`.

### Affected capabilities and files

One capability with two requirements, and five files, because the confirmation is described in the skill, its harness copies, the spec, and a contract test.

Evidence:

- Capability `epic-autopilot`: `deliver-skill` (base ccba3353289e), `in-session-park-and-continue` (base ebbf0d03e1cf), hashes from `spec_status.py base-hash`.
- Files: `plugins/s/skills/autopilot/SKILL.md`, `plugins/s/harness/bodies/autopilot.md`, `plugins/s/harness/references/autopilot.md`, `plugins/s/skills/build/tests/test_autopilot_skill_contract.py:48`, `plugins/s/.claude-plugin/plugin.json:4` (0.6.366).
- Runnable premise: `autopilot.py --help` → exit 0, lists `--max-members`, `--parallel`, `--timeout`, `--max-resumes`.
- Runnable premise: `autopilot.py autonomous-delivery --waves --parallel 3` → exit 0, printed `Waves for epic ... (cap 3)`.

### No open task-shaping decision

Every task-shaping decision is settled by investigation and the user's request; none remain.

Evidence:

- Where controls come from (the invocation, defaults otherwise): the user's request.
- Cancel option dropped: the user's request (not invoking is the cancel).
- Dialog replaced by a printed launch brief: investigation of Phase 2's content.
- In-session `--max-members` applies in wave order: investigation of the waves mode.
- Personal memory store: absent, so no preference applied.
