<!-- description: Judge whether an epic's gated plans still hold against main — holds, revise, or conflict per drifted member. -->
# /s:drift — judge whether gated plans still hold against main

Your job is thin: run `spec_status.py drift`, then judge only the members the
verb flagged, from a bounded evidence set. You are read-only — write no file,
run no mutating verb, re-plan nothing, open no question, and delegate to no
other agent.

<!-- include:preamble -->

1. **Resolve the invocation.** It is `<change> | --epic <slug> [--base <ref>]
   [--json]`. Pass the change, `--epic`, and `--base` to the verb unchanged;
   strip your own `--json` first and remember whether it was present.
2. **Run the verb.** Without `--json`, run
   `python3 "$S/spec_status.py" drift <args>` and relay its text verbatim as
   the report's first section, then run it again with `--json` for the member
   list. With `--json`, run only the JSON form. Branch on the exit code alone:
   - `0` — every member is clean or skipped. Print `clean:` and `skipped:`
     lines; read no plan and no diff.
   - `4` — judge every member whose `findings` array is non-empty.
   - `1` or `2` — relay the `Error:` or usage text and stop. Under `--json`,
     emit the object in step 6 with `error` set and empty arrays.
   The verb's `root` names each member's hosting root for every later read.
3. **Gather the evidence — only this.** Per flagged member:
   `python3 "$S/spec_status.py" --root <root> cat change <member>`; once per
   run, `python3 "$S/spec_status.py" cat epic <slug>` for the plan's `Epic:`
   header (skipped when the plan has none). Per finding: for `file-drift`, `git -C <root> diff
   <planned_at>..<base.sha> -- <path>` (over 400 lines, read `git log
   --format='%h %s'` for the path plus the hunks naming an identifier the plan
   cites); for `symbol-gone`, `git -C <root> grep -l -w -F
   <symbol> <planned_at>` (strip the `<sha>:` prefix), `git -C <root> diff
   <planned_at>..<base.sha> -- <those paths>`, and `git -C <root> log
   --format='%h %s' -S<symbol> <planned_at>..<base.sha>`; for
   `stale-base`, `python3 "$S/spec_status.py" --root <root> cat verified
   <capability>` against the delta's MODIFIED entry. Read nothing else and take
   no whole-tree diff.
4. **Judge.** One verdict per flagged member. `holds`: no assumption the plan's
   Implementation, tasks, or delta scenarios make about the drifted paths,
   symbols, or master changed. `revise`: an assumption broke and a revision
   inside the plan's `**Answered by:** USER` entries and the epic's Decisions
   repairs it. `conflict`: the repair or the drift contradicts a `USER` entry
   or an epic Decision; name the `Q<n>` or the Decision. `PLANNER` and `ORACLE`
   entries never raise `conflict`. If the evidence cannot show an assumption
   holds, the verdict is `revise`, never `holds`.
5. **End the report with the block**, in the verb's member order:
   `## Drift verdicts`, then `<member>: holds — <reason>`,
   `<member>: revise — <reason>; revise: <sections or tasks>`,
   `<member>: conflict — <reason>; contradicts: Q<n> | Decision "<name>"`, then
   `clean: a, b`, `skipped: c (<reason>)`, and last
   `verdicts: <n> holds, <n> revise, <n> conflict; <n> clean, <n> skipped`.
6. **`--json` mode.** The whole response is one JSON object, no fence, no
   prose: `mode` (`epic` or `change`), `epic`, `change`, `base` (`ref`, `sha`),
   `verdicts` (per member: `member`, `root`, `planned_at`, `verdict`, `reason`,
   `contradicts`, `revise`, and the verb's `findings` verbatim), `clean`,
   `skipped` (`member`, `reason`), and `error` (`null`, or the engine's line).
7. **Name the next step, then stop.** `revise`: revise the plan and re-gate
   with `spec_gate.py <change>`. `conflict`: a human decision on the named
   `Q<n>` or Decision. You perform neither.
