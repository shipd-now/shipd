# Posting a review to a PR

The skill reads this file only when posting was explicitly requested, by the user or by a driving session.

The review verdict gates a PR only once it reaches GitHub. Posting is a
**mechanical** step handled by a companion script — you supply the judgement
(the `--json` object), it shapes the GitHub payloads:

```
python3 "$CLAUDE_PLUGIN_ROOT/skills/review/scripts/review_gate.py" post <pr> --from <json|->
```

**Post only on an explicit request** — the user asking to "post the review to
the PR", or a driving session (the autopilot's `review` stage) instructing you
to. Never post as a side effect of a plain review; a review with no posting
request stays local and touches no `gh` write.

## Review stage options

The invoker — a driving session or the user — may pass two options with the
posting request. Both default to today's behaviour, so a plain "post the
review" changes nothing:

- `disposition=<all|high-only|none>` (default `all`) — how much per-finding
  judgement this review is worth. It selects the posting flow's step 6 (see
  below) and passes straight through to the poster as `--disposition`, which
  maps the `semantic-review` commit status by scope: `all` → `success` iff the
  verdict is `pass`; `high-only` → `success` iff no finding is high; `none` →
  always `success`. The findings and the rendered verdict stay
  severity-honest in every scope — only the merge-gating status is
  policy-aware, and a non-`all` scope is stamped on the summary comment and in
  the status description so a green status over visible findings is explained
  on the PR.
- `model=<tier>` — the model tier this review was meant to run on, symbolic
  (`session`, `tier-below`, `tier-two-below`) or a concrete id. Pass it
  through to the poster as `--model`; it is recorded verbatim as a `Model:`
  line in the summary. **Applying** the tier is the concern of the driver that
  spawns the reviewing session (the autopilot's `review` stage); this skill
  never spawns itself on another model, and interactively the tier is
  informational provenance only.

Never resolve the pipeline configuration yourself — this skill reads no
`autonomous-pipeline` key and infers no options. Whatever the invoker did not
pass, take as the default.

When posting is requested:

1. **Resolve the PR.** `gh pr view <branch> --json number,headRefOid,url` (or
   pass the PR number/URL directly). The branch is usually the current
   `change/<name>`.
2. **Review head vs base with merge-base semantics.** Run the review as
   `diff <base> <head>` (default base `main`) so the "after" side is the PR's
   head exactly as GitHub shows it — the same three-dot semantics described
   under "Determine what to review". Do the full analysis; do not shortcut it.
3. **Read prior dispositions and drop what was already answered.** Run
   `review_gate.py prior <pr>` and, for every finding this review is about to
   post, compare its `hash` — the same identity `_finding_hash(<path>,
   <normalized what>)` computes and `_inline_body` embeds as the trailing
   `<!-- shipd-finding <hash> -->` marker — against `prior`'s entries. Omit a
   finding whose hash matches an entry classified `replied`: a human already
   gave it a reasoned answer, and reposting it unchanged only repeats the
   finding back at them. Leave every other finding in place — none of the
   other three classes is evidence a human dismissed it:
   - **`commit-only`** — only a commit landed after the thread, which is
     purely time-based and proves nothing about implementation; a recurrence
     after it is a regression, the most valuable finding the gate can produce.
   - **`autoreplied`** — one of the two canonical `autoreply` bodies fired
     mechanically; nobody actually assessed the finding.
   - **`none`** — nobody has dispositioned it at all.

   This step runs only when posting; a review that is not posting makes no
   `prior` call and omits nothing. Carry the omitted count and this PR forward
   to the final report (step 8).
4. **Emit the machine JSON to a temp file.** Produce the `--json` object (same
   shape and rules as Machine output mode) from the findings that survived
   step 3, and write it to a temp path, e.g. `"$TMPDIR/review.json"`.
5. **Run the poster.** `review_gate.py post <pr> --from "$TMPDIR/review.json"`,
   adding `--disposition <scope>` and `--model <tier>` when the invoker passed
   them. It upserts the marker summary comment, posts anchored inline comments
   for in-diff findings (folding the rest into the summary), and sets the
   `semantic-review` commit status on the head SHA by scope — under the default
   `all`, `success` iff the verdict is `pass`, else `failure`.
6. **Disposition the findings — by scope.** A posted finding is advice nobody
   is required to read until it is dispositioned, and every gate thread must
   end up carrying disposition evidence. How much judgement you spend depends
   on the acting scope:
   - **`all` (the default) — every finding, low included.** Walk the findings
     (newest post first) and give each exactly one of two dispositions — never
     leave a finding with neither. A finding that is neither implemented (by
     your edit or by its suggestion having been applied) nor replied to is
     undispositioned, and `resolve` will refuse it:
     - **Implement** it when the suggestion is correct: make the edit, commit,
       and push. The push re-triggers the gate, so re-run the review + poster
       afterwards so the summary and status track the new head SHA.

       A finding whose committable `suggestion` block has already been
       **applied** on the pull request is implemented by that very act — the
       commit GitHub made is the evidence — so it needs no edit and **no
       separate reply**. Do not reply "applied" onto such a thread; `resolve`
       reads the later commit as the disposition, exactly as it does for a fix
       you pushed yourself.
     - **Push back** when you judge it not worth implementing: post a concrete,
       reasoned reply onto the finding's thread with

       ```
       review_gate.py reply <pr> <comment-id> --body "<the reason>"
       ```

       where `<comment-id>` is the inline review comment rooting that finding's
       thread. A bare "won't fix" is not a disposition — name the reason.
   - **`high-only` — judgement on the highs only.** Implement each **high**
     finding (or push back on it with a reasoned `reply`, exactly as under
     `all`), re-reviewing and re-posting after any push. Then cover the rest
     mechanically:

     ```
     review_gate.py autoreply <pr> --disposition high-only
     ```

     It posts the canonical policy reply onto every unreplied gate thread
     rooted at a medium or low finding, prints `replied=<n>`, and leaves the
     highs — and any thread whose severity it cannot parse — untouched, so a
     reported unparsed thread still needs your disposition.
   - **`none` — no per-finding judgement at all.** Do not implement and do not
     author individual replies; run

     ```
     review_gate.py autoreply <pr> --disposition none
     ```

     which replies to every unreplied gate thread regardless of severity. The
     findings stay posted and honest; they are simply recorded rather than
     acted on.

   `autoreply` skips threads that already carry a reply, so re-running it after
   a push is safe.
7. **Resolve the threads.** Once every finding is implemented, answered, or
   auto-replied, run

   ```
   review_gate.py resolve <pr>
   ```

   It resolves only the gate-authored threads that carry disposition evidence
   (a reply, or a commit landed after the thread was created), refuses any that
   carry neither (listing them as undispositioned and exiting non-zero), and
   never touches human-authored threads — humans resolve their own. Use
   `resolve <pr> --check` to read the unresolved count without mutating.
8. **Report back** the posted status state (`success`/`failure`), the summary
   comment URL, the acting disposition scope when it is not `all`, the
   `unresolved=` count from `resolve` — which is **zero** on a completed
   disposition — and, when step 3 omitted any finding, how many and the pull
   request whose threads answered them. Any non-zero `unresolved=` count means
   a finding still has no disposition; go back to step 6.

The poster is idempotent: re-running after a new push edits the same summary
comment in place and re-stamps the status on the new head SHA. It performs no
analysis of its own — all judgement stays in this skill; the engine only
enforces that each finding was implemented or answered before its thread
resolves.
