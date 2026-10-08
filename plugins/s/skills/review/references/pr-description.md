# PR description check

The skill reads this file when a pull request's title and description are available — stated inline in the invocation, or fetched for a named pull request via `gh pr view --json title,body`.

Treat the title and description as claims, not as ground truth, and check them against the diff in **both directions**. Neither direction alone finds what the other does.

**Direction 1 — each claim against the diff.** For every concrete claim about what the PR adds, changes, or fixes, ask whether the diff supports it, contradicts it, or falls short of it.

**Direction 2 — the diff against the claims.** Walk the diff's substantial content and ask what the description never mentions. This is a separate pass, not a by-product of direction 1: an unmentioned feature has no claim to check, so iterating claims can never surface it. Scope the pass to substance — a new feature path, a new dependency, a new migration, a new public surface, a behavioral change to an existing one — not to every file the diff touches.

Report a mismatch from either direction as its own finding: category `description-drift`, severity by the normal high/medium/low rubric and its impact rule, judged on what the mismatch implies for correctness or completeness. A description that is merely terse or informal is not a finding.

**Anchor a description-level finding at one location only.** Where the drift is a property of the description rather than of any particular line, give the finding its primary anchor and stop. A second location follows the review skill's general further-location permission, never a separate rule granted here — a claim contradicted at three call sites is three sites; a description that undersells the PR's scope is one finding about the description, however many files the unmentioned scope spans.

- **Real finding — the code diverges from the description.** The description says a function returns early on a missing config value; the diff shows it falls through and uses a default instead. Severity follows the actual behavioral risk, not the mismatch itself.
- **Real finding — the description undersells the diff.** The description says "declared the new dependency," and the diff does that, but also adds a whole feature path the description never mentions. Nothing in the description is false, which is exactly why direction 1 misses it — the finding is the silence, and it matters because unmentioned scope goes unreviewed.
- **Real finding — the description oversells the diff.** The description says a dependency was added, but the diff's manifest file (`package.json`, `go.mod`, etc.) never declares it — this is usually also a real defect on its own terms (a missing declaration), not only a documentation gap.
- **Not a finding.** The description is short, informal, or omits minor detail the diff itself makes obvious — style, not substance.
