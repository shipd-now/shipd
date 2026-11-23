<!-- doc-type: how-to -->

# Drift

Drift is the distance between a gated plan and the code on `main` today. A
gated plan cites files, symbols, and master requirements. `main` keeps moving
between the gate and the build, so some of those citations go stale.

The engine measures which citations moved. `/s:drift` then judges whether
each move breaks the plan, and returns one verdict for each member.

The skill is read-only. It edits no file, re-plans nothing, and sets no
status. It names the next step, and you run that step.

## When to use it

Run `/s:drift` when a plan has waited a while since its gate. Typical cases:

- other pull requests merged into `main` after the gate passed an epic's
  members;
- you want to know whether a member's plan still holds before you build it;
- you want one view of every drifted member across an epic.

You do not need to run it before an autopilot run. Autopilot runs the same
check before each member's build. See [Autopilot](autopilot.md).

`/s:build` runs a separate check at its start, which the
[supersession gate](supersession-gate.md) page owns.

## How to run it

1. Run the skill on one change or on every member of an epic:

   ```
   /s:drift <change>
   /s:drift --epic <slug>
   ```

   Add `--base <ref>` to measure against a ref other than `main`. Add
   `--json` to get one JSON object and no prose.
2. The engine measures each plan. A member with no moved citation is
   `clean`. A member the engine cannot measure is `skipped`.
3. The skill reads the plan and the bounded diff for each member with a
   finding.
4. The skill returns one verdict for each judged member.
5. The report ends on the `## Drift verdicts` block:

   ```
   ## Drift verdicts
   add-cache: holds — only shifted line citations in src/engine.py
   cache-ttl: revise — load_ttl is gone; revise: Implementation, task 2.1
   cache-evict: conflict — the fix contradicts the plan's Q2; contradicts: Q2
   clean: cache-docs
   skipped: cache-ui (unplanned)
   verdicts: 1 holds, 1 revise, 1 conflict; 1 clean, 1 skipped
   ```

6. Act on each verdict:
   - `holds` — build the member as planned.
   - `revise` — revise the plan at the named sections, then gate it again.
   - `conflict` — a human decides on the named `Q<n>` or epic Decision.

Only a plan entry answered by the user, or an epic Decision, raises
`conflict`. An entry that the planner or the oracle answered never raises it.
When the evidence cannot show that the plan still holds, the verdict is
`revise`.

To change an epic Decision after a `conflict`, see [Epics](epics.md).

## Reference

| verdict or state | meaning |
| --- | --- |
| `holds` | The moves break no assumption that the plan makes. |
| `revise` | An assumption broke, and a revision within the settled decisions repairs it. |
| `conflict` | The repair, or the drift itself, contradicts a user answer or an epic Decision. |
| `clean` | The engine found no moved citation, so the skill judges nothing. |
| `skipped` | The engine did not measure the member, for example an `unplanned` one. |

| finding kind | meaning |
| --- | --- |
| `file-drift` | A commit since the plan touched a file the plan cites. |
| `symbol-gone` | A symbol the plan cites existed at the plan and is gone at the base. |
| `stale-base` | A master requirement the plan's delta modifies changed since the plan. |

See also:

- [Autopilot](autopilot.md) — runs this check before each build.
- [Epics](epics.md) — amend the Decisions a `conflict` names.
- [The supersession gate](supersession-gate.md) — the check build runs at
  its start.
