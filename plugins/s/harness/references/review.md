# /s:review — posting the verdict as a pull request's merge gate

The long form the router points at. Read it before posting anything; a plain
review stays local and touches no write API.

**Post only on an explicit request** — the user asking for the review to be
posted, or a driving session instructing you to. Posting as a side effect of
an ordinary review is never correct.

## The machine payload

Posting is mechanical: you supply the judgement as one JSON object, and the
poster shapes the GitHub payloads from it. Emit the object to a file, with no
preamble, no fences, no commentary, and no emoji:

```json
{
  "verdict": "pass" | "changes-requested",
  "effort": 3,
  "findings": [
    {
      "id": "f1",
      "severity": "high" | "medium" | "low",
      "cohort": "bug" | "contract" | "edge-case" | "untouched-caller" | "spec-coverage",
      "location": "path/to/file.ext:LINE",
      "what": "one-line statement of the defect",
      "why": "why it matters",
      "fix": "concrete fix",
      "status": "open",
      "note": ""
    }
  ],
  "spec_coverage": [ { "scenario": "WHEN … THEN …", "state": "met" | "unmet" | "cant-tell" } ],
  "could_not_verify": [ "…" ]
}
```

Rules: `verdict` is `changes-requested` **iff** any finding is high or medium,
else `pass` — the same decision the rendered verdict states, and the two must
never diverge. An unmet spec scenario must appear as a `spec-coverage` finding
with severity `high`. `spec_coverage` is present only when a planned change was
in scope. If the analysis could not run at all, still emit a well-formed
object whose `could_not_verify` explains why.

## The posting flow

1. **Resolve the pull request** for the branch under review (usually the
   current `change/<name>`), capturing its number and head SHA.
2. **Review head against base with merge-base semantics**, so the "after" side
   is exactly what the pull request shows. Do the full analysis — posting is
   never a reason to shortcut it.
3. **Write the JSON object to a temp file.**
4. **Run the poster** with that file. It upserts a single marker summary
   comment, posts anchored inline comments for the findings that fall inside
   the diff (folding the rest into the summary), and sets the
   `semantic-review` commit status on the head SHA. It is idempotent:
   re-running after a push edits the same summary in place and re-stamps the
   status on the new head.
5. **Disposition every finding.** A posted finding is advice nobody has to
   read until it is dispositioned, and every gate thread must end up carrying
   disposition evidence. Each finding gets exactly one of two dispositions,
   never neither:
   - **Implement it** when the suggestion is correct — edit, commit, push.
     The push invalidates the status, so re-run the review and the poster
     afterwards against the new head.
   - **Push back** when it is not worth implementing — reply on that finding's
     thread with a concrete, reasoned explanation. A bare "won't fix" is not a
     disposition: name the reason.
6. **Resolve the threads.** The resolve verb closes only the gate-authored
   threads that carry disposition evidence, refuses any that carry neither
   (listing them and exiting non-zero), and never touches human-authored
   threads — humans resolve their own.
7. **Report back** the posted status state, the summary comment's URL, and the
   unresolved count, which is **zero** on a completed disposition. Any
   non-zero count means a finding still has no disposition — go back to
   step 5.

## Disposition scope

A driving session may narrow how much per-finding judgement the review is
worth. The findings and the rendered verdict stay severity-honest in every
scope; only the merge-gating status is policy-aware, and a narrowed scope is
stamped on the summary comment so a green status over visible findings is
explained on the pull request.

| scope | judgement spent | status is green when |
| --- | --- | --- |
| `all` (default) | every finding, low included | the verdict is `pass` |
| `high-only` | the high findings by hand; the rest cleared with the canonical policy reply | no finding is high |
| `none` | none — findings are recorded, not acted on | always |

## After the branch merges

A squash merge deletes the branch, so a finding that surfaces afterwards can no
longer land on that pull request. Either it blocked the merge and went through
the fix loop above, or it becomes a **new change** planned against the current
base branch — never a second pull request on an already-merged branch.
