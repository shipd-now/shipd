---
name: epic-grill
description: >-
  Plan every unplanned member of an approved epic in one pass: order the
  members by dependency, plan each through /s:plan with its human questions
  deferred, check the plans against each other, ask the whole question agenda
  in one final round, amend the plans to the answers, gate every member, and
  hand off to /s:autopilot. Never builds. Use when asked to "grill an epic",
  "plan the whole epic", or "/s:epic-grill". Trigger phrases: "grill an epic",
  "plan the whole epic", "/s:epic-grill".
---

# /s:epic-grill — Plan a whole epic, ask once

You are the **epic grill**. You plan every unplanned member of one approved
epic, collect every open human decision into a single final round, then
reconcile the plans and gate them together. You **never build, ship, or open a
PR**, and you **never edit the epic file**; the hand-off is `/s:autopilot`.

**Announce the version first.** Read the running plugin version from
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and include
`shipd:epic-grill v<version>` in your first user-visible status sentence (e.g.
"shipd:epic-grill v0.2.11 — reading the epic"), so the user can see which
plugin snapshot is running.

Paths (resolve `${CLAUDE_PLUGIN_ROOT}` to the real plugin root):

- Status CLI: `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py`
- Linter: `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_lint.py`
- Gate: `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_gate.py`
- Worktree helper: `${CLAUDE_PLUGIN_ROOT}/bin/shipd`

Run every command **from the repository root**. The epic slug is the sole
argument to `/s:epic-grill <epic>`.

---

## Preflight (read-only)

1. Read the epic only through the engine:
   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" epic-show <epic> --json
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" cat epic <epic>
   ```
2. **Stop rule.** If the epic is missing, or its status is neither `ready` nor
   `active`, report the status and plan nothing. A `draft` epic still needs
   approval.
3. **Select members.** Take every member in the `unplanned` lane plus every
   member whose state is `draft` (a planned member an earlier, interrupted
   grill left unfinished). Report every other member with its state and leave
   it untouched. If nothing is selected, say so and stop.
4. **Order the selection by dependency**, judged from the epic's Decisions,
   Design, and member descriptions: a member whose output another consumes
   comes first. Break ties by ascending risk, then table order.
5. **Print the order** before planning the first member, one line per member
   with the reason it sits there, then continue without asking.

## Planning

Plan the selected members **one at a time, in the printed order**, so each
planner can read the plans before it. Keep a running list of
`<slug>: <worktree root>` for every member planned or already `draft`.

- **`unplanned` member.** Create its worktree, then spawn the planner:
  ```
  "${CLAUDE_PLUGIN_ROOT}/bin/shipd" worktree <member>
  ```
  The worktree root is `.worktrees/<member>`. Spawn **one general-purpose
  sub-agent** for the member and wait for it before starting the next. Give it
  this instruction verbatim, filling the placeholders:

  ```
  Run /s:plan for the change `<member>`, a member of the epic `<epic>`,
  planned by /s:epic-grill. No human is available during this run.
  Work in its worktree `.worktrees/<member>` (already created) and install
  the change there.
  Members already planned in this run (read each with
  `spec_status.py --root <root> cat change <slug>`; keep names, interfaces,
  and shared decisions consistent with them): <slug>: <root>, ...
  Consult the oracle as /s:plan prescribes, but open no question round. For
  every decision the oracle leaves open (INSUFFICIENT, an advisory ANSWER, or
  no verdict), adopt your recommended default as a settled decision and record
  a `## Questions and answers` entry with `**Answered by:** PLANNER`: the
  options in `**Question:**` with the default first, the default in
  `**Answer:**`, and `**Queued:**` when the oracle filed one.
  Install the change through spec_emit.py and stop at Status: draft. Do not
  run spec_gate.py; /s:epic-grill gates every member after its final round.
  End your turn with `DEFERRED:` and one line per PLANNER entry
  (`Q<n> | <summary> | <options, default first>`), or `DEFERRED: none`.
  ```
- **`draft` member.** Do not re-plan it. Find its worktree root:
  ```
  python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" locate <member>
  ```
  and add the `root:` it prints to the running list. Its `PLANNER` entries are
  read from disk later like any other.

**Grade every planner from disk**, never from its report:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" --root <worktree> status <member>
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_lint.py" <member> --root <worktree>
```

The member passes only if `status` prints `draft` and the linter exits 0. A
failed grade: **stop and ask the human** what to do (retry the planner, fix by
hand, or drop the member); do not plan on past it.

## Consistency pass

When every selected member is `draft`, read each one:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" --root <worktree> cat change <member>
```

Check the plans against each other and against the epic's Decisions: names,
interfaces, data shapes, ordering assumptions, and who owns what.

- **Repository-settled mismatch** (e.g. one plan says `--defer`, its consumer
  says `--deferred`): fix it in place in the member's installed artifacts,
  silently. The repository and the plans settle which side is right.
- **Human-only conflict**: add a `PLANNER` entry to the ledger of **each**
  affected member, with the options and the default you would adopt.
- **Shared master requirement.** Note every pair of members whose deltas
  modify the same master requirement; the later one goes stale once the
  first ships. Carry the pair into the hand-off.

After any edit, re-run the linter on that member; it must still exit 0.

## Final round

Build the agenda from the **`PLANNER` entries on disk** in every selected
member's `plan.md` (not from the `DEFERRED:` blocks, so a resumed run and a
cut-off planner read the same agenda). Merge entries that pose the same
decision into one question naming every member and `Q<n>` it covers.

- **Empty agenda: ask nothing** and go to Amend and gate.
- Otherwise ask the whole agenda here, after the consistency pass and never
  before it, through **AskUserQuestion** calls of **at most four questions
  each**. Each question names its member(s) and `Q<n>` references; the adopted
  default is the **first option, marked "(Recommended)"**. Put all context in
  the question and option text. The turn that issues a dialog carries **no
  other substantive prose**, because the harness can drop it.
- **Question rejection recovery.** A known Claude Code bug can deliver an
  AskUserQuestion as a tool rejection even when the user tried to answer.
  Never treat a rejected or interrupted dialog as a decline or an answer. If
  the user's next message answers it, fold it in; otherwise re-offer the same
  choices as a plain-text numbered list and wait for a typed reply.

**Capture the answers.** For each answered entry carrying a `**Queued:**`
slug, distill the answer into one durable sentence or two and classify it
against `${CLAUDE_PLUGIN_ROOT}/skills/ask/references/capture-rubric.md`:
include it with `wiki-queue-answer <slug> --answer "<answer>"`, exclude it
with `wiki-queue-discard <slug> --reason "<why>"`, or, when the rubric makes
it consent-gated, capture it with `--advisory` only on the user's express yes
and discard otherwise. Pass the bare slug and run the verbs as
`spec_status.py --root <root> wiki-queue-answer ...`.

## Amend and gate

For each answered decision:

1. Edit the affected installed artifacts of each member (`plan.md`, delta
   specs, `tasks.md`) in place so they state the chosen option. Never leave
   the default behind when the user chose another.
2. Rewrite the ledger entry's `**Answered by:**` to `USER` and its
   `**Answer:**` to the user's resolution.
3. **Epic-wide answers.** Where an answer binds every member, do **not** edit
   the epic; flag it for the user to apply with `/s:epic <epic> amend`.

Then gate every selected member:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_gate.py" <member> --root <worktree>
```

Exit 0 promotes the member to `ready`. On exit 2, read the findings written
into the member's `plan.md`: resolve what the repository answers, ask the
human (one dialog, as above) about the rest, then re-gate. **Never set a
member's status by any other path** (no `set-status`, no hand edit of the
`Status:` line, no `--force`): `ready` is reached only through the gate.

## Ending — hand off, don't build

Print, per member, a **why-first summary**: one or two plain sentences on why
the change exists and what it settles, then its final status and worktree
root. List any epic-wide answers flagged for `/s:epic <epic> amend`, any pairs
sharing a master requirement, and any member that did not reach `ready`.

Close with a `## Summary` heading and **one sentence** saying how many members
are planned and gated and what is left, then the hand-off command alone on its
own line:

```
/s:autopilot <epic>
```

Never build, run `/s:build`, push, or open a PR from this skill. If the grill
is interrupted before the final round, every planned member stays at `draft`;
re-running `/s:epic-grill <epic>` resumes them.
