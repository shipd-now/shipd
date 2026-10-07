# PR description check

The skill reads this file when a pull request's title and description are available — stated inline in the invocation, or fetched for a named pull request via `gh pr view --json title,body`.

Treat the title and description as claims, not as ground truth. For each concrete claim about what the PR adds, changes, or fixes, check it against the actual diff: does the diff support it, fall short of it, or exceed it? Report a mismatch as its own finding — category `description-drift`, severity by the normal high/medium/low rubric, judged on what the mismatch actually implies for correctness or completeness. A description that is merely terse or informal is not a finding; only a claim the diff contradicts, undersells, or oversells is.

- **Real finding — the code diverges from the description.** The description says a function returns early on a missing config value; the diff shows it falls through and uses a default instead. Severity follows the actual behavioral risk, not the mismatch itself.
- **Real finding — the description undersells the diff.** The description says "declared the new dependency," but the diff also adds a whole new feature path nobody mentioned — the gap is worth flagging so a reviewer isn't surprised by unreviewed scope.
- **Real finding — the description oversells the diff.** The description says a dependency was added, but the diff's manifest file (`package.json`, `go.mod`, etc.) never declares it — this is usually also a real defect on its own terms (a missing declaration), not only a documentation gap.
- **Not a finding.** The description is short, informal, or omits minor detail the diff itself makes obvious — style, not substance.
