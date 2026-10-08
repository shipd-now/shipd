<!-- description: Run a semantic review of local changes against a base ref before they are pushed. -->
# /s:review — semantic review of local changes before they ship

You supply the judgement; `git` supplies the mechanics. Reason over the diff,
never over whole files dumped into context. The review is read-only — it never
edits the repository.

<!-- include:preamble -->

1. **Fetch the base's remote, then decide what to compare, and say so.**
   In every mode — working tree, two refs, or a pull request — fetch the
   base's remote first, e.g. `git fetch origin main`. It writes
   remote-tracking refs only, never the working tree, index, or a local
   branch, and never pulls, rebases, or checks anything out. If the fetch
   fails, continue and record a could-not-verify entry naming the unchecked
   base, rather than ending the review. By default compare the working tree
   against `main` (`master` when that's the default), anchored on the fork
   point — `git merge-base <base> HEAD` — not the base's own tip, so an
   advance picked up after you branched is never read as your own edit.
   For two refs, compare `<base>...<head>` so the "after" side is what a
   pull request would show. State the resolved base, head, and mode
   — as commit ids — before the findings.
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
   safety: grep is not a call graph, so name what you could not check. A
   changed limit, bound, timeout, retry count, buffer size, or threshold is a
   contract change too — chase its consumers the same way.
5. **Follow the values the call sites actually pass.** A guard the real call
   can never reach is dead code; a comment promising behaviour the code does
   not produce is wrong even though its line exists. Confirm the path that
   reaches a mechanism really runs before you describe it as if it does. When
   the diff touches two or more parallel implementations of the same thing,
   compare them against each other, not only against the base, and name any
   hardening applied to one and not the other.
6. **Judge new code on its own terms.** For every function, class, guard, or
   helper the diff introduces: does it measure the quantity its limit
   actually governs, does an escape hatch let its guarantee lapse, does it
   terminate cheaply on hostile input, and do its boundaries agree with its
   doc comment?
7. **Apply the risk lenses.** Whatever the cohort, watch for six triggers:
   secret or credential exposure (a key, token, password, or personal data
   in a literal, log line, error message, or fixture); authorization boundary (a
   route, handler, job, or query reached without checking the caller's
   scope, role, or ownership); unbounded work (iteration count or size
   driven by user input with no cap); resource release (a handle, socket,
   lock, connection, or transaction not released on every exit path,
   including errors); migration reversibility (a schema migration or
   destructive operation with no down-path, backfill, or backup); packaging
   and dependency manifests (a manifest or lockfile disagreeing with the
   code or with each other, or omitting a new file from what it publishes).
8. **Breadth sweep.** After the risk lenses, revisit each changed file once
   more, end to end, for a remaining defect the structural and
   signature-chasing steps above would not catch alone: a swallowed or
   silently-dropped error, a resource or file leak on a rare or cleanup path,
   dead or duplicated code, a field or variable declared but never read, an
   unstable or incorrect identity such as a list key derived from an array
   index, or a blocking call in an async context. Send what it finds back to
   step 11's rubric to rate.
9. **Verify the spec when a change is in scope** — the user named one, exactly
   one change sits under `.shipd/planned/`, or the diff adds or edits a change
   directory under `.shipd/planned/` or `.shipd/completed/` (its slug strips
   any leading `YYYY-MM-DD-` date prefix). Read it with `python3
   "$S/spec_status.py" cat change <change>`, then classify every
   `#### Scenario:` against the diff as **met** (citing the file and hunk),
   **unmet**, or **can't-tell** — a real outcome, not a failure to force;
   every unmet scenario is a high-severity finding. Cross-check the `- [x]`
   tasks against the diff, flag any marked done with no change behind it,
   and — while under `.shipd/planned/` — surface `shipd lint <change>`
   findings verbatim; an archived `.shipd/completed/` change has none to
   surface, its deltas already merged.
10. **Check the PR description against the diff when one is available —
    given inline, or via `gh pr view --json title,body`.** Check both
    directions: each title/body claim against the diff, and the diff's
    substantial content against what the description never mentions — an
    unmentioned feature has no claim to check, so only the second direction
    finds it. Either mismatch is its own finding, category
    `description-drift`, severity by the normal rubric. Anchor a
    description-level finding at one location only, unless another site
    independently shows the drift.
11. **Report by cohort, most severe first.** Give each finding a location (fix
    site, not symptom; a further site where the defect is visible — wrong the
    same way, showing the mismatch on its own terms, or the line where it
    surfaces at run time though correct in isolation), what is wrong, why it
    matters, a fix, and severity:
    - **high** — a correctness bug, a contract break with an un-updated
      consumer, or an unmet spec scenario;
    - **medium** — an unhandled edge case, a caller at genuine risk, or a
      likely-wrong behaviour you cannot fully confirm;
    - **low** — a real defect whose impact is contained: nothing lost,
      corrupted, exposed, or promised and unmet. Pure style, naming, and
      formatting are never findings.
    Rate every finding by what the defect does, not by the kind of defect it
    is: data loss, data corruption, a security exposure, or a broken guarantee
    is medium or high however minor the kind looks — a success response that
    hides a failure, returning an empty result as if real while a count or
    flag says otherwise; a cleanup path that drops the record but leaves the
    data, or the reverse; and an error path that loses the only copy. A secret
    or credential exposure finding, or an authorization boundary reached
    without a scope check, is always **high** regardless of your confidence.
    Open with an effort score of 1–5 justified by the counts, then the verdict:
    **Fix required** when any finding is high or medium, **Ship it** otherwise.
    When unsure between two levels, state the doubt, not inflate it; never drop
    a finding for unclear severity — report your best estimate, flagged
    uncertain. Close with an explicit list of what you could not verify.
12. **Check test coverage, rolled up per cohort.** For every finding you
    write, at every severity, ask whether an existing test would fail if
    that defect regressed. Raise one `test-coverage` finding per cohort
    with uncovered findings, naming each defect it would guard and where
    the tests belong — never one per finding, which multiplies with the
    findings and buries them. Anchor it once, where the tests belong.
13. **Hand off.** Fix-required findings go back through `/s:build`'s
    implementation loop while the branch is still open, or — once it has
    merged — become a new change through `/s:plan`. Never open a second pull
    request on an already-merged branch.
<!-- if:file-references -->
   Posting the verdict onto a pull request as its merge gate is a separate
   flow with its own payload and posting verbs: read {refs}/review.md before
   posting anything. A review naming a pull request posts to it by default —
   no ask required. Dispositioning the findings — implementing or resolving
   them — happens only when asked.
<!-- else -->
   Posting the verdict onto a pull request as its merge gate is a separate
   flow whose detail is not available as a file here. A review naming a pull
   request still posts to it by default — no ask required — and
   dispositioning the findings happens only when asked; say so when the user
   asks for the flow's detail, state that you would have read the review
   reference for the gate's payload shape and its posting verbs, and either
   finish the review locally or hand the posting step to a harness that
   carries that reference.
<!-- end -->
