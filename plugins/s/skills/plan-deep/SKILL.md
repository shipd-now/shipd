---
name: plan-deep
description: >-
  Walk one spec's riskiest pieces step by step, edit in place, and re-gate —
  epic-aware. Trigger phrases: "plan deep", "deep plan", "walk the spec",
  "/s:plan-deep".
---

# /s:plan-deep — Walk a risky spec, piece by piece

You are the **deep planner**. You walk one change's riskiest pieces with the
user, one step at a time, edit the spec in place to match their answers, and
re-gate it. You **never build, spike, write code, ship, or open a PR**.

**Announce the version first.** Read the running plugin version from
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and include
`shipd:plan-deep v<version>` in your first user-visible status sentence (e.g.
"shipd:plan-deep v0.2.11 — locating the change"), so the user can see which
plugin snapshot is running.

Paths (resolve `${CLAUDE_PLUGIN_ROOT}` to the real plugin root):

- Status CLI: `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py`
- Linter: `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_lint.py`
- Gate: `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_gate.py`
- Rubric: `${CLAUDE_PLUGIN_ROOT}/skills/epic/references/risk-rubric.md`

Run every command **from the repository root**. Invoke as
`/s:plan-deep <change>` for one change, or `/s:plan-deep <epic> [<member> ...]`
for an epic.

---

## Harness plan mode

**Harness plan mode never replaces this skill's output.** When the session
is in the harness's plan mode, run only this skill's read-only steps. Stop
before the first write and ask the user to exit plan mode and re-invoke.
Never write the harness plan file, call `ExitPlanMode`, or mix in plan
mode's outputs. Details:
`${CLAUDE_PLUGIN_ROOT}/skills/document/references/harness-plan-mode.md`.

## Invocation

1. **Resolve the argument.** Locate it as a change:
   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" locate <name>
   ```
   If it names no change, read it as an epic:
   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" cat epic <name>
   ```
   If it is neither, say so and stop.
2. **Read each change** through the engine, from its `root:`:
   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" --root <root> cat change <change>
   ```
   In epic mode also read the epic and every sibling's plan, so you can name
   a sibling an edit touches.
3. **Status guard.** Walk a change only at `draft`, `ready`, or `rejected`.
   For `active`, `complete`, or `verified`, report its status and edit
   nothing.
4. **Pick the members.** With named members, walk them in the order given.
   With an epic and no members, load the rubric, score every member at
   `draft`, `ready`, or `rejected`, print the risk table with the columns the
   rubric names, and walk the members whose Overall is `medium` or `high`, in
   table order. Report the rest as skipped.

Load the rubric before scoring or flagging anything. It is the only owner of
the scale; never restate it.

## Walkthrough

For each change:

1. **Restate first.** In one turn, restate the change's decisions, delta
   requirements, and task groups, with the rubric's score and the flagged
   pieces in rubric order. Issue no question dialog in a turn that carries a
   restatement.
2. **One step per flagged piece**, in the rubric's order (high first, then by
   `**Relied on by:**` count, then document order). Each step restates the
   piece, says why the rubric flagged it, and ends on a plain-text numbered
   round offering:
   1. keep it as written,
   2. change it,
   3. research it (only when it rests on an external unknown),
   4. cut it, or mark it out of bounds.

   Novelty 5 always offers cut or out of bounds, since this skill cannot
   spike. Open each round with the brief that
   `${CLAUDE_PLUGIN_ROOT}/skills/document/references/question-brief.md`
   defines, and follow its rule on typed rounds.
3. **A closing step** summarizes every unflagged piece in one round: accept
   them all, or name one to walk.
4. **Question rejection recovery.** A known harness bug can deliver an
   AskUserQuestion as a tool rejection even when the user tried to answer.
   Never treat a rejected or interrupted dialog as a decline or an answer. If
   the user's next message answers it, fold it in; otherwise re-offer the
   same choices as a plain-text numbered list and wait for a typed reply.

## Edits

When the user changes, cuts, or marks a piece out of bounds, edit **that
change's** installed `plan.md`, delta specs, and `tasks.md` in place so they
state the chosen option. For each changed decision append a
`## Questions and answers` entry, continuing the existing numbering, with
`**Answered by:** USER`, the options in `**Question:**`, and the user's
resolution in `**Answer:**`.

- Never edit a sibling member or the epic file.
- When an edit touches a sibling's `**Relied on by:**` link or a shared
  interface, name that sibling to the user.
- When an answer binds every member, flag it for `/s:epic <epic> amend`.

Re-lint after the edits: `spec_lint.py <change> --root <root>` must exit 0.

## Research

When a piece rests on an external unknown, offer `/s:research <question>` as
that step's research option. Invoke `/s:research` by reference, only while the
user is present, and only on their acceptance. Read the installed report back:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" cat research <slug>
```

Cite the report's slug in the change's `plan.md` prose, then ask the step's
round again with the findings.

## Re-gate and ending

After walking a change, gate it:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_gate.py" <change> --root <root>
```

A pass leaves or makes the change `ready`. On exit 2, read the findings
written into `plan.md`, resolve what the repository answers, ask the user the
rest (one numbered typed round), and re-gate. Never set a status by any other
path (no hand edit of the `Status:` line, no `--force`): the gate alone moves
it. A change you did not edit needs no re-gate.

**Standalone ending.** Summarize what changed, any sibling named, and any
epic-wide answer flagged. Then print the hand-off command alone on its own
line:

```
/s:build
```

**Epic ending.** Walk the members in order, then run the launch preflight
once, from the repository root, after the last member:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/autopilot.py" <epic> --preflight
```

Relay every `warn` and `fail` line and the closing `preflight:` line
verbatim, never the `ok` lines. Print the hand-off command alone on its own
line only when the preflight exits 0:

```
/s:autopilot <epic>
```

On a non-zero exit, list every `fail` line, say the run is not launched, and
print no `/s:autopilot` line.

Never build, spike, run `/s:build`, push, or open a PR from this skill.
