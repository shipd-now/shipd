<!-- description: Execute a planned change task by task, verify it, and ship it as a pull request. -->
# /s:build — execute a planned change and ship it

You own the contract, the verification, and the ship. Code is written only
against a lint-clean change, and only inside that change's own branch.

<!-- include:preamble -->

1. **Work in the change's worktree.** `bash "$S/worktree.sh" <change>`, then
   work in `.worktrees/<change>` on branch `change/<change>`. Never author
   artifacts or edit code in the main checkout. Read `.shipd/constitution.md`
   when it is present and treat every rule in it as binding on what follows.
2. **Get a lint-clean change first.** When `.shipd/planned/<change>/` already
   holds artifacts and `shipd lint <change>` exits 0, adopt them as they are —
   do not re-plan and do not re-ask what planning already settled. Otherwise
   run the `/s:plan` flow and continue from what it emits. No code is written
   against an unlinted contract, however small the change looks.
3. **Bring the branch current, then check for supersession.** Run
   `git fetch origin main && git merge origin/main` — a conflict here is
   itself a signal, so surface it rather than resolving it blindly — then
   `python3 "$S/spec_status.py" check-base <change>`. Exit 0 proceeds
   silently. Exit 4 prints `<capability>/<id>: <kind>` findings: read the
   named masters and the base branch's recent history to classify them.
   Masters that merely moved for unrelated reasons → reconcile the deltas'
   `base:` hashes and proceed. An already-merged change that did this plan's
   substance → stop, report the superseding merge, and ask the user whether to
   abandon the change or re-scope it to what remains.
4. **Open the work.** `python3 "$S/spec_status.py" use <change>`, then
   `python3 "$S/spec_status.py" set-status active <change>`.
5. **Implement every task in `tasks.md`, in order.** The delta specs and
   `plan.md`'s `## Implementation` are the contract; a task that needs a
   decision they do not fix is a question, not a judgement call.
<!-- if:subagents -->
   Delegate the implementation: spawn one executor per currently-claimable
   task on the model tier one step below your own, and keep the architectural
   work yourself. Each spawn message carries only the change name, the
   absolute path to `"$S/claim_task.sh"`, and any build-specific addenda — the
   artifacts on disk are its whole context, so paste no conversation into it.
   Each executor loops `claim` → implement → `complete` → re-`claim`. When one
   returns a message beginning `QUESTION:`, answer it yourself and
   definitively, updating the artifacts first when the answer exposes a gap in
   the spec, then resume that executor where it paused.
<!-- else -->
   Do the work yourself, one task at a time.
   `bash "$S/claim_task.sh" claim <change>` atomically takes the next ready
   task and prints `ID<TAB>TEXT` (the first line only — read the task's full
   text in `tasks.md`). Implement exactly that task, then
   `bash "$S/claim_task.sh" complete <change> <ID>` and claim again. Empty
   output can mean a barrier has not cleared yet, so stop only once
   `bash "$S/claim_task.sh" status <change>` reports `pending=0`.
<!-- end -->
<!-- if:background-tasks -->
   Tasks sharing a `[P<n>]` tag are mutually independent: run a ready group's
   tasks together in the background rather than one after another, and keep
   the foreground free to answer questions while they run. `claim` is atomic
   and group-aware, so it never hands out a task whose barrier is unfinished.
<!-- else -->
   Treat the `[P<n>]` tags as documentation only and run every task
   sequentially in the foreground. `claim` hands out one ready task at a time
   and withholds any whose barrier is unfinished, so a strictly sequential
   pass is always correct — only slower.
<!-- end -->
6. **Verify — a clean lint is not a working change.** Confirm
   `bash "$S/claim_task.sh" status <change>` reports `pending=0
   in_progress=0`, re-derive the change's status with
   `python3 "$S/spec_status.py" sync <change>`, then run the project's build,
   typecheck, linter, and tests, and drive the real behaviour each
   `#### Scenario:` describes rather than trusting the suite alone. Re-run
   `shipd lint <change>` — it must still exit 0. Fix whatever fails and
   re-verify before going on; a scenario you cannot exercise is a finding, not
   a pass.
7. **Stamp and apply.** `python3 "$S/spec_status.py" set-status verified
   <change>`, then `python3 "$S/spec_merge.py" <change>`, which merges the
   deltas into `.shipd/verified/` and archives the change under
   `.shipd/completed/`. Merge warnings never fail the merge — carry them into
   the report.
8. **Ship as a pull request; never push to `main`.** Read the mode first with
   `python3 "$S/spec_status.py" config-show`: no `pr-mode` line or
   `pr-mode = "auto"` ships an auto-merging pull request, `pr-mode = "draft"`
   opens a draft and stops there, and any other value stops before pushing
   and reports that `auto` and `draft` are the accepted values.
   ```sh
   git add -A && git commit -m "<what shipped>"
   git push -u origin change/<change>
   gh pr create --fill                            # add --draft in draft mode
   gh pr merge --auto --squash --delete-branch    # auto mode only
   ```
   Then post the semantic review onto the pull request with `/s:review` and
   disposition every finding it posts — implement the correct ones, reply to
   the rest with a concrete reason — since the merge waits on that gate.
9. **Report** in a few sentences: what shipped, the task counts, the commit
   hash, and the pull request's full URL rather than its number.
<!-- if:background-tasks -->
   Then watch the pull request to a terminal state in the background, polling
   `gh pr view "$PR_URL" --json state,mergeStateStatus`. `MERGED` ends the
   watch; `DIRTY`, `BEHIND`, or `BLOCKED` means it cannot merge as armed, so
   reconcile against `origin/main`, push, and re-post the review on the new
   head within that same cycle.
<!-- else -->
   Then read the pull request's state once with
   `gh pr view "$PR_URL" --json state,mergeStateStatus` and report it. Nothing
   here polls the pull request to its terminal state, so say so and tell the
   user to re-run that check — or re-invoke this command — once the required
   checks have finished.
<!-- end -->
<!-- if:file-references -->
The long form — the merge-warning rendering, the telemetry report, and the
post-merge close-out — lives in {refs}/build.md; read it before step 7.
<!-- else -->
The long form of the merge-warning rendering and the post-merge close-out is
not available as a separate file here. Say so if a step needs it, state that
you would have read the build reference for that detail, and finish the build
from the rules above, leaving the worktree in place for the user to clean up.
<!-- end -->
