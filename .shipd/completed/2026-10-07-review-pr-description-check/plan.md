# review-pr-description-check
Status: verified
Theme: reliability

## Idea

### Motivation

Item 3 of the benchy-cf ReviewBench handoff: on the benchmark's 5 PRs,
3 golden findings are misses purely because `/s:review` never checks a
pull request's own title and description against the diff. Named examples:
k1LoW `github.go:75` (the code diverges from what the description claims),
apilix `WORKSPACES.md:1` (the description says only dependencies were
declared, but the PR adds a whole feature), and apilix
`server/package.json` (the description says a dependency was added, but
the manifest never declares it). benchy-cf's harness now passes the title
and description inline after the `/s:review` command line
(`run-shipd.sh --pr-context`); a real PR gets them from `gh pr view`. The
skill itself has never had a step that reads either.

### Details

Add a check that, whenever a pull request's title and description are
available, verifies each concrete claim against the actual diff and
reports a mismatch as its own finding — a new `description-drift`
category, severity by the existing high/medium/low rubric. This is a fifth
judgement pass alongside new-code checks, risk lenses, the breadth sweep,
and test-coverage.

Affected capability: `semantic-review` (requirement `review-skill`,
modified). Impact: `plugins/s/skills/review/SKILL.md` (new step 5d, a
References table row), a new reference file
`plugins/s/skills/review/references/pr-description.md`,
`plugins/s/harness/bodies/review.md` (mirrored step, fully inline — it
ships into other repos with no `${CLAUDE_PLUGIN_ROOT}`),
`plugins/s/skills/review/references/json-output.md` and
`plugins/s/harness/references/review.md` (the `category` enum gains
`description-drift`), `plugins/s/skills/review/references/posting.md`
(the named-PR `gh pr view` call gains `title,body`),
`plugins/s/skills/review/tests/test_skill_references.py` (the taxonomy
value set and its "ten values" test), and the plugin version bump.

### Non-goals

- No change to `review_gate.py` — nothing there inspects or validates
  `category` values (confirmed: `grep -n category
  plugins/s/skills/review/scripts/review_gate.py` returns no matches), so
  a new category needs no poster code change.
- No change to the severity rubric, the exposure floor, or any other
  judgement pass's content.
- Not a harness-side change: benchy-cf owns `run-shipd.sh --pr-context`
  and real-PR `gh pr view` resolution already exists in `posting.md` —
  this change only adds `title,body` to that existing call and the
  judgement instruction that uses them.
- Items 4 (new risk lenses) and 5 (missing-test precision, on hold) are
  separate, later changes.

## Implementation

### The check

New SKILL.md step `5d`, positioned after `5c` (breadth sweep) and before
`6` (report) — exact text:

```
### 5d. Check the PR description against the diff
When a pull request's title and description are available, read
`${CLAUDE_PLUGIN_ROOT}/skills/review/references/pr-description.md` and verify
every claim against the diff.
```

New References table row (added after the `new-code-checks.md` row):

```
| `${CLAUDE_PLUGIN_ROOT}/skills/review/references/pr-description.md` | a pull request's title and description are available |
```

New reference file `plugins/s/skills/review/references/pr-description.md`
— full text below, installed verbatim (it satisfies
`test_each_reference_opens_with_title_and_condition`'s "reads this file"
requirement and shares ≥3 content words with the table cell above, per
`test_table_cell_agrees_with_reference_condition`):

```markdown
# PR description check

The skill reads this file when a pull request's title and description are available — stated inline in the invocation, or fetched for a named pull request via `gh pr view --json title,body`.

Treat the title and description as claims, not as ground truth. For each concrete claim about what the PR adds, changes, or fixes, check it against the actual diff: does the diff support it, fall short of it, or exceed it? Report a mismatch as its own finding — category `description-drift`, severity by the normal high/medium/low rubric, judged on what the mismatch actually implies for correctness or completeness. A description that is merely terse or informal is not a finding; only a claim the diff contradicts, undersells, or oversells is.

- **Real finding — the code diverges from the description.** The description says a function returns early on a missing config value; the diff shows it falls through and uses a default instead. Severity follows the actual behavioral risk, not the mismatch itself.
- **Real finding — the description undersells the diff.** The description says "declared the new dependency," but the diff also adds a whole new feature path nobody mentioned — the gap is worth flagging so a reviewer isn't surprised by unreviewed scope.
- **Real finding — the description oversells the diff.** The description says a dependency was added, but the diff's manifest file (`package.json`, `go.mod`, etc.) never declares it — this is usually also a real defect on its own terms (a missing declaration), not only a documentation gap.
- **Not a finding.** The description is short, informal, or omits minor detail the diff itself makes obvious — style, not substance.
```

### The SKILL.md line budget

`plugins/s/skills/review/SKILL.md` is at its 329/330-line ceiling with no
slack (confirmed: `wc -l` reports 329). Step 5d plus the table row costs 6
raw lines. Free this budget through **mechanical reflow, not content
cuts**: several bullet lists in steps 3, 4, 5b, and 6 are wrapped
noticeably narrower than the file's typical width and can be rejoined and
rewrapped at ~88 columns with zero words changed — a pure line-count
reduction, verified word-for-word against the original. The implementer
reflows exactly these four bullet blocks (step 3's five bullets, step 4's
two bullets, step 5b's five risk-lens bullets, step 6's four rubric
bullets) by joining each bullet's wrapped lines into one string and
rewrapping at a wider column, never by rewording or dropping a clause —
this is the proven-safe technique (no content loss, directly measurable)
versus the alternative of shortening prose, which cost two real content
regressions in the two preceding changes. **One hard constraint on the 5b
reflow**: the risk-lens trigger name `secret or credential exposure` must
keep its literal "or" — not become "secret/credential exposure" — because
`test_risk_lens_triggers_stated_inline` and `_missing_triggers` match it as
an exact phrase; reflow changes line breaks only, never the words inside a
trigger name.

### The harness body

`plugins/s/harness/bodies/review.md`'s render-ceiling test
(`test_every_body_stays_lean_at_the_full_vocabulary`, ceiling 120 rendered
lines) is likewise at its edge (confirmed: rendering the full feature
vocabulary over the current file yields 119 lines). The new step costs 4
rendered lines as:

```
10. **Check the PR description against the diff when one is available —
    given inline, or via `gh pr view --json title,body`.** A title/body
    claim the diff contradicts or exceeds is its own finding, category
    `description-drift`, severity by the normal rubric.
```

inserted after the existing step 9 (spec verification) and before the
existing step 10 (report), renumbering every step from the old 10 onward
by one (10→11, 11→12, 12→13) — safe this time because every renumbered
marker stays two digits (no single-to-double-digit transition, which is
what caused the indentation regression in an earlier change). Free the
needed budget the same mechanical-reflow-first way: rejoin and rewrap step
1's prose and step 7's risk-lens paragraph at a wider column (same "or"
constraint on the secret/credential trigger name applies here too), and
tighten step 9's closing sentence only as prose, verified word-for-word.
The implementer measures with:

```
python3 -c "
import sys
sys.path.insert(0, 'plugins/s/skills/build/tests')
sys.path.insert(0, 'plugins/s/skills/build/scripts')
import harness_bodies as hb, harness_registry as hr
print(len(hb.render('review', hr.FEATURES,
                     refs_dir='plugins/s/skills/review/references').splitlines()))
"
```

after every edit, targeting ≤119, and runs
`test_every_body_stays_lean_at_the_full_vocabulary` to confirm before
moving on — never trusting a manual line count.

### The `description-drift` category

Add it as an 11th enum value on both `json-output.md`'s and
`harness/references/review.md`'s `"category":` line, and one explanatory
sentence beside each file's existing `locations` array sentence: "names a
finding where a pull request's title or body makes a claim the diff
contradicts, undersells, or oversells — present only when a pull request's
title and description were available to review." Update
`test_skill_references.py`'s `ALL_TAXONOMY_VALUES` frozenset to add
`"description-drift"` and rename
`test_value_set_contains_all_ten_values` to
`test_value_set_contains_all_eleven_values` (its body is unchanged — it
already reads from the updated frozenset).

### `posting.md`

Change the named-pull-request resolution call from
`gh pr view <target> --json number,baseRefOid,headRefOid,url` to the same
with `,title,body` appended, and add one sentence after it: "`title` and
`body` feed the PR-description check (`references/pr-description.md`) as
claims to verify against the diff, never as resolution metadata."

### Spec

`.shipd/verified/semantic-review/spec.md`'s `review-skill` requirement
gains one paragraph describing the check (mirroring the SKILL.md
wording), the judgement-pass count corrects from four to five, and two
new scenarios (a real description/diff mismatch is reported;
`description-drift` is present only when a description was available).

### Version

`plugins/s/.claude-plugin/plugin.json` bumps 0.6.252 → 0.6.253.

## Readiness attestation

### Problem and motivation

3 of the benchmark's golden findings are misses because `/s:review` never
checks a PR's title/description against its diff; nothing in the skill
reads either field.

Evidence: benchy-cf's original handoff (this conversation) naming
`k1LoW:github.go:75`, `apilix:WORKSPACES.md:1`,
`apilix:server/package.json`; `plugins/s/skills/review/SKILL.md` (no step
reads a title or description anywhere); `plugins/s/skills/review/references/posting.md`
line ~56 (`gh pr view` resolves `number,baseRefOid,headRefOid,url` only,
no `title`/`body`).

### Scope and non-goals

In scope: the new check (SKILL.md, harness body, new reference file), the
category addition (both JSON payload surfaces, the taxonomy test), the
`gh pr view` field addition, the spec delta, the version bump. Out of
scope: `review_gate.py` (confirmed no category-handling code exists to
change), the severity rubric, and items 4/5.

### Affected capabilities and files

One capability, one requirement.

Evidence: capability `semantic-review`, requirement `review-skill` (base
hash `ef0ca408187c`). Runnable premises: `wc -l
plugins/s/skills/review/SKILL.md` reports 329 (ceiling 330); the harness
render script above reports 119 (ceiling 120) — both confirming zero
starting slack, which the mechanical-reflow strategy accounts for.

### No open task-shaping decision

- Where the new step sits in each file's sequence: settled above (SKILL.md
  5d after 5c; harness body step 10 after step 9, renumbering safely since
  no digit-width boundary is crossed).
- How to free line budget without repeating the two prior content-loss
  regressions: mechanical reflow of exact, named bullet blocks, verified
  word-for-word and re-measured after every edit — settled above, not left
  for the implementer to improvise.
- The category name (`description-drift`) and its enum position (appended
  11th, not inserted mid-list, so no existing value's position shifts):
  settled above.
- Whether `review_gate.py` needs a change: no, confirmed by grep — settled
  above.
