# /s:review — posting the verdict as a pull request's merge gate

The long form the router points at. Read it before posting anything; a plain
review naming no pull request stays local and touches no write API.

**A named pull request is posted to by default** — no ask required. Where
the invocation names a pull request, its verdict is published through the
poster without being asked. Dispositioning the findings — implementing or
resolving them — is a separate, opt-in step: a driving session declaring a
disposition scope, or the user asking for the findings to be implemented or
answered.

## The machine payload

Posting is mechanical: you supply the judgement as one JSON object, and the
poster shapes the GitHub payloads from it. Emit the object to a file, with no
preamble, no fences, no commentary, and no emoji:

```json
{
  "verdict": "pass" | "changes-requested",
  "effort": 3,
  "endpoints": {
    "base_given": "main",
    "base": "main",
    "base_sha": "<40-char commit id>",
    "head": "feature" | null,
    "head_sha": "<40-char commit id>" | null,
    "merge_base": "<40-char commit id>",
    "mode": "working-tree" | "merge-base" | "linear"
  },
  "findings": [
    {
      "id": "f1",
      "severity": "high" | "medium" | "low",
      "category": "bug" | "contract" | "edge-case" | "untouched-caller" | "spec-coverage" | "test-coverage" | "security" | "performance" | "stability" | "data-integrity",
      "locations": ["path/to/file.ext:LINE", "other/file.ext:LINE2"],
      "what": "one-line statement of the defect",
      "why": "why it matters",
      "fix": "concrete fix",
      "status": "open",
      "note": ""
    }
  ],
  "change": { "slug": "…", "location": "planned" | "completed", "dir": "…" },
  "spec_coverage": [ { "scenario": "WHEN … THEN …", "state": "met" | "unmet" | "cant-tell" } ],
  "could_not_verify": [ "…" ]
}
```

Rules: `verdict` is `changes-requested` **iff** any finding is high or medium,
else `pass` — the same decision the rendered verdict states, and the two must
never diverge. An unmet spec scenario must appear as a `spec-coverage` finding
with severity `high`. `change` and `spec_coverage` are present only when a
planned change was in scope. If the analysis could not run at all, still emit
a well-formed object whose `could_not_verify` explains why.

The `locations` array is non-empty; `locations[0]` is the primary site where
the fix would be applied, and any further entries are sites where the same
defect recurs.

`endpoints` carries the engine's resolved endpoint metadata — `base_given`,
`base_sha`, `head_sha`, and `merge_base` straight from `semdiff`'s meta, plus
`base`/`head`/`mode`. `merge_base` is absent under `--linear`; `head`/
`head_sha` are `null` in working-tree mode. The poster rejects a payload
carrying no `endpoints.merge_base` before writing anything to the pull
request. `plugins/s/skills/review/references/json-output.md` specifies this
same object identically, since it is a second machine-payload surface for
the same contract.

## The posting flow

1. **Resolve the pull request** for the branch under review (usually the
   current `change/<name>`), capturing its number, base commit, and head
   commit — never a local branch name, which is how a stale or
   fork-relative base used to leak into the review.
2. **Fetch both resolved commits, then review by commit id**, with
   merge-base semantics, so the "after" side is exactly what the pull
   request shows. Do the full analysis — posting is never a reason to
   shortcut it.
3. **Write the JSON object to a temp file.**
4. **Run the poster** with that file. It upserts a single marker summary
   comment, posts anchored inline comments for the findings that fall inside
   the diff (folding the rest into the summary), and sets the
   `semantic-review` commit status on the head SHA. It is idempotent:
   re-running after a push edits the same summary in place and re-stamps the
   status on the new head.
**The default ending, once posted.** Where nothing beyond the review was
asked for, stop here: implement no finding, author no reply, run neither
step 5 nor step 6, and leave every posted thread open for the pull request's
owner to action and resolve.

5. **Disposition every finding — only where asked.** Run this step only when
   a driving session declared a disposition scope, or the user asked for the
   findings to be implemented or answered. A posted finding is advice nobody
   has to read until it is dispositioned, and every gate thread must end up
   carrying disposition evidence. Each finding gets exactly one of two
   dispositions, never neither:
   - **Implement it** when the suggestion is correct — edit, commit, push.
     The push invalidates the status, so re-run the review and the poster
     afterwards against the new head.
   - **Push back** when it is not worth implementing — reply on that finding's
     thread with a concrete, reasoned explanation. A bare "won't fix" is not a
     disposition: name the reason.
6. **Resolve the threads — only where step 5 ran.** The resolve verb closes
   only the gate-authored threads that carry disposition evidence, refuses
   any that carry neither (listing them and exiting non-zero), and never
   touches human-authored threads — humans resolve their own.
7. **Report back** the posted status state and the summary comment's URL.
   Where steps 5 and 6 ran, additionally report the unresolved count, which
   is **zero** on a completed disposition — any non-zero count means a
   finding still has no disposition, so go back to step 5. Where they did
   not run, report that every posted thread was left open.

## Disposition scope

The scope narrows an opted-in disposition, never the posting itself, which
always happens by default. Once a driving session or the user has opted in,
the scope sets how much per-finding judgement the review is worth. The
findings and the rendered verdict stay severity-honest in every scope; only
the merge-gating status is policy-aware, and a narrowed scope is stamped on
the summary comment so a green status over visible findings is explained on
the pull request.

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
