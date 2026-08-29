# paginate-review-diff-map
Status: verified
Theme: reliability

## Idea

Fetch every page of a pull request's changed files when the review gate builds
the diff map it anchors findings against, so a large pull request stops
silently losing its inline comments.

### Motivation

The posting step reads the changed files with `per_page=100` and no
`--paginate`, so past 100 files the diff map is short and every finding in the
unfetched files is folded into the review body as prose — indistinguishable
from a finding that named a path the diff genuinely does not carry. The same
step already paginates its other list call, so the two disagree.

### Details

- Add `--paginate` to the changed-files call in the gate workflow template.
- Assert the flag in the gate's test suite, beside the existing assertion that
  the posting step reads that endpoint at all.
- Amend `gate-workflow-template` so the diff it verifies findings against is
  required to be complete, rather than merely computed.

Affected capabilities: `copilot-review-skill` (modified). Impact:
`plugins/s/integrations/copilot/copilot-review-gate.yml`,
`plugins/s/skills/build/tests/test_copilot_verb.py`. No new dependencies; the
engine stays stdlib-only and the workflow gains no new tool.

### Non-goals

- No change to the reviews poll at line 487, which already paginates.
- No change to the `: > "$files_file"` failure path: a call that *fails* is
  already reported, and this change is about a call that succeeds while
  returning less than everything.
- No change to the embedded Python. The loader already accepts what the
  paginated call returns, so nothing downstream of the fetch moves.
- No new warning for a short diff map: with the fetch complete there is no
  longer a truncation to warn about.
- No change to which findings anchor: the severity gate and `placed()` are
  untouched.

## Implementation

- **`--paginate` alone, with no `--slurp` and no loader change.** Verified
  against a real pull request rather than assumed: `gh api
  "repos/shipd-now/cai-api/pulls/27/files?per_page=2" --paginate` returned a
  single JSON array of all 3 files that `json.load` accepts, while the same
  call without the flag returned 2. `gh` merges pages for a REST array endpoint
  on its own, so the multi-document output that would require `--slurp` never
  arises here. `per_page=100` stays: it sets the page size, and paginating
  fetches the rest.
- **The assertion is on the step's source text, not on a stubbed call.** The
  gate tests already assert the posting step's text contains
  `"repos/$REPO/pulls/$PR_NUMBER/files` (`test_copilot_verb.py:1099`), and the
  new assertion sits beside it in the same style. Rejected: extending the
  runnable `gh` stub to record the files call's argv — the stub serves
  `*/files*` from a fixture and records nothing for it (line 1335), so
  asserting the flag behaviourally would mean teaching it a recording channel
  it has for no other read. A flag's presence in the emitted command is exactly
  what a source assertion is good for.
- **The requirement gains completeness, which is what was missing.**
  `gate-workflow-template` requires findings to be verified "against the diff it
  computed" and says nothing about that diff covering every changed file. That
  silence is what let a truncating fetch satisfy the spec, so the delta requires
  the diff map to cover the pull request's changed files in full and pins it
  with a scenario.
- **Every consumer of the map benefits without being touched.** `placed()`
  refuses a finding whose path is absent from the map, so a complete map is
  what makes its refusal mean "not in the diff" rather than "not in the first
  page". No call site changes.

Risk: a pull request near GitHub's 3000-file cap now issues up to thirty list
calls where it issued one, so the step is slower and consumes more API quota on
very large pull requests — accepted, because the alternative is silently
dropping the anchoring those findings were computed for. Risk: `--paginate`'s
single-array merging is `gh` behaviour rather than a documented API guarantee;
the empirical check above is the evidence, and the loader's existing
`json.load` failure path already degrades to an empty map rather than crashing
if that ever changed.
