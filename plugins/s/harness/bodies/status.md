<!-- description: Report a change's lifecycle status, or run a guarded transition. -->
# /s:status — report a spec's status, or run a guarded transition

Your job is thin: run one status command, relay what it printed, and never
re-implement a check the engine already owns.

<!-- include:preamble -->

1. **Resolve the invocation to exactly one command.** Where a change name is
   omitted, the engine falls back to the currently selected change, so never
   resolve that selection yourself:
   - **no argument, or a change name** → `shipd status [<change>]`, which
     prints the change's status and progress. With no argument and no
     selection it prints the whole delivery board instead — the totals line,
     the `shipped <n>/<m>` line, and the `UNPLANNED`, `READY`, `BUILDING`,
     and `SHIPPED` lanes. Relay either report as printed: do not re-summarize,
     re-order, or re-count it.
   - **validate** → `python3 "$S/spec_status.py" validate <change>`. Report
     `OK` on exit 0, otherwise print the errors it reported.
   - **set-status `<status>`** → the guarded transition in step 2.
   - **pipeline** → `python3 "$S/spec_status.py" pipeline-show`, adding
     `--expand <preset>` when a preset is named. Relay the output verbatim and
     never parse it; an unknown preset exits non-zero listing the known ones,
     and that listing is the answer, not a failure.
   A name that matches no change but does match an epic prints that epic's
   board-shaped report. Epic transitions never go through `set-status`, which
   is change-only — use `epic-set-status <status> <slug>` or `epic-sync
   <slug>` instead.
2. **Run the transition without `--force` first**, then branch on the exit
   code alone. `<status>` is one of `draft`, `ready`, `active`, `complete`,
   `verified`, or `rejected`:
   ```sh
   python3 "$S/spec_status.py" set-status <status> <change>
   ```
   - **0** — it succeeded; report the new status.
   - **1** — a real error: an unknown change or status, a missing proposal, no
     selection. Show the `Error:` line, ask nothing, and do not force —
     `--force` cannot fix an error.
   - **3** — a guard refused it. The first stderr line begins `Refused: ` and
     carries the concrete reason (task counts, or the validation errors).
     Surface that reason and put the choice to the user.
3. **Only an explicit override forces.** Offer exactly two options — override
   anyway, or leave the status unchanged (the default).
<!-- if:question-dialogs -->
   Ask it as a single AskUserQuestion dialog: the turn carries nothing but the
   refusal reason and the two options, which is exactly the shape a dialog is
   for. Never treat a rejected or interrupted dialog as a decline — re-offer
   the same two options as a numbered list and wait for a typed reply.
<!-- else -->
   Ask it as a plain-text numbered list of the two options and read the
   answer from the user's typed reply.
<!-- end -->
   Re-run the same command with `--force` appended only on an explicit
   override. On a decline, change nothing and repeat the refusal reason.
4. **Report the outcome in one or two lines** — the command you ran, the
   change it acted on, and the result — then stop. This command does no other
   work: point at `/s:build` when the answer is a `ready` change waiting to be
   implemented.
<!-- if:file-references -->
   The full status vocabulary and the guard each transition trips is written
   out in {refs}/status.md.
<!-- else -->
   The full status vocabulary and the guard each transition trips is not
   available as a separate file here. Say so if the user asks for it, state
   that you would have read the status reference for that detail, and answer
   from the refusal text the engine printed — it names the guard that fired.
<!-- end -->
