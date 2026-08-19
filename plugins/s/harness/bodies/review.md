<!-- description: Run a semantic review of local changes against a base ref before they are pushed. -->
# /s:review — semantic review of local changes before they ship

You supply the judgement; `git` supplies the mechanics. Reason over the diff,
never over whole files dumped into context. The review is read-only — it never
edits the repository.

<!-- include:preamble -->

1. **Decide what to compare, and say so.** By default compare the working tree
   against `main` (`master` where that is the default branch). When the user
   names two refs, compare `<base>...<head>` so the "after" side is what a
   pull request would show; fetch first, since both refs must exist locally.
   State the resolved base, head, and mode before the findings.
2. **Map the change into cohorts.** `git diff --name-status <base>` gives the
   changed files; group them into architectural cohorts — contracts, database,
   api, frontend, tests, and this repo's own spec artifacts. Review cohort by
   cohort with the foundational layers first (contracts and database before
   api before frontend), never alphabetically and never file by file.
3. **Read the diff structurally.** `git diff <base> -- <cohort paths>`, and
   reason about what changed *structurally*: signatures added, removed, or
   altered; control flow rerouted; contracts broken. Open a whole file only
   when a hunk is genuinely ambiguous, or when a file is new and matters.
4. **Chase every changed signature to its call sites.** For each changed
   function, type, or message shape, `git grep -n "<symbol>"` across the repo.
   Call sites the search finds but the diff does not touch are your
   highest-value findings — a contract the change moved and a consumer nobody
   updated. Treat every match as a candidate to verify, never as proof of
   safety: grep is not a call graph, so name what you could not check.
5. **Follow the values the call sites actually pass.** A guard the real call
   can never reach is dead code; a comment promising behaviour the code does
   not produce is wrong even though its line exists. Confirm the path that
   reaches a mechanism really runs before you describe it as if it does.
6. **Verify the spec when a planned change is in scope** — the user named one,
   or exactly one change sits under `.shipd/planned/`. Read it with
   `python3 "$S/spec_status.py" cat change <change>`, then classify every
   `#### Scenario:` against the diff as **met** (citing the file and hunk),
   **unmet**, or **can't-tell** — the last is a real outcome, not a failure to
   force. Every unmet scenario is a high-severity finding. Cross-check the
   `- [x]` tasks against the diff and flag any marked done with no change
   behind it, and surface `shipd lint <change>` findings verbatim.
7. **Report by cohort, most severe first.** Give each finding a location, what
   is wrong, why it matters, a concrete fix, and an explicit severity:
   - **high** — a correctness bug, a contract break with an un-updated
     consumer, or an unmet spec scenario;
   - **medium** — an unhandled edge case, a caller at genuine risk, or a
     likely-wrong behaviour you cannot fully confirm;
   - **low** — style, naming, minor redundancy, defensive nits.
   Open with an effort score of 1–5 justified by the counts, then the verdict:
   **Fix required** when any finding is high or medium, **Ship it** otherwise.
   When you are unsure between two levels, state the doubt rather than
   inflating it. Close with an explicit list of what you could not verify.
8. **Hand off.** Fix-required findings go back through `/s:build`'s
   implementation loop while the branch is still open, or — once it has
   merged — become a new change through `/s:plan`. Never open a second pull
   request on an already-merged branch.
<!-- if:file-references -->
   Posting the verdict onto a pull request as its merge gate is a separate
   flow with its own payload and posting verbs: read {refs}/review.md before
   posting anything, and post only when the user explicitly asks.
<!-- else -->
   Posting the verdict onto a pull request as its merge gate is a separate
   flow whose detail is not available as a file here. Say so when the user
   asks for it, state that you would have read the review reference for the
   gate's payload shape and its posting verbs, and either finish the review
   locally or hand the posting step to a harness that carries that reference.
<!-- end -->
