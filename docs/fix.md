<!-- doc-type: how-to -->

# Fix a bug

`/s:fix` debugs a reported problem against the spec library. Before it reads
any code, it finds what the specs say the behaviour should be. It then fixes
the code to match, or hands off when the documented behaviour itself is wrong.
It ends with a report and ships nothing.

## When to use it

- Something behaves wrongly, and you want a fix grounded in the documented
  contract.
- You want a regression test that pins the documented behaviour.
- You suspect the spec itself is wrong, and want a diagnosis before you plan
  a change.

Use [`/s:plan`](plan.md) instead when you already know the documented behaviour must
change. Use [Build a change](build.md) to ship planned work.

## How to run it

1. Run `/s:fix` with the symptom in your own words:

   ```
   /s:fix the report rows print in the wrong order
   ```

2. Check the three to six search terms the skill states. Correct them if they
   miss the area.
3. Read the diagnosis and the outcome in the closing report.
4. Commit, push, and open the pull request yourself, under your repository's
   conventions.

### What the skill does

1. **Retrieve before it dives.** The skill runs the engine's `related` verb
   with your search terms:

   ```
   python3 plugins/s/skills/build/scripts/spec_status.py related <term> [<term>...]
   ```

   The verb ranks verified capabilities, planned and completed changes,
   research reports, epics, and wiki pages by term hits. The skill reads the
   top matches through the engine's `cat` verbs, verified capabilities first.
2. **Reproduce first.** Where a runnable surface exists, the skill reproduces
   the problem before it changes anything. A failing test, a failing command,
   or a minimal script serves as the evidence.
3. **Diagnose and classify.** The skill compares the reproduction against the
   documented behaviour. Exactly one of two outcomes follows.

### Outcome A: the code is wrong

The code drifted from the documented behaviour, or no spec covers the bug.
The skill:

1. fixes the code with the smallest change that makes the documented
   behaviour hold;
2. adds a regression test that follows your repository's test conventions;
3. re-runs the reproduction and the relevant tests.

### Outcome B: the spec is wrong

The code faithfully implements the specs, and the documented behaviour itself
is wrong. The skill changes nothing. It reports the capability, requirement,
and scenario that encode the wrong behaviour, then hands off to `/s:plan`. An
ambiguous spec takes this outcome too.

### Boundaries

- The skill never edits a spec artifact: no plan, no delta spec, no verified
  master, no epic, no wiki page.
- The skill never moves a change's status.
- The skill never commits, branches, pushes, or opens a pull request.
- The skill fixes one problem per run, and names any others as follow-ups.

## Reference

### Report parts

| Part | Contents |
| --- | --- |
| Diagnosis | The root cause, and the capability and requirement it violates, or a note that no spec covers it. |
| Retrieval | The terms searched and the artifacts read. |
| Fix | The files changed and what each change does, or the hand-off to `/s:plan`. |
| Verification evidence | The reproduction before and after, and the test commands with their real results. |
| What it could not verify | Anything not reproduced, not tested, or out of scope. |

A fix without a reproduction appears in the report as unverified, in those
words.

### Related pages

- [Build a change](build.md) — ship a planned change, including one a
  hand-off produced.
