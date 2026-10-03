# Machine output mode

The skill reads this file when the user passes `--json`, or when it is producing the JSON object the poster consumes.

When the user passes `--json`, emit a single JSON object to stdout and nothing
else — no preamble, no walkthrough, no diagrams. All analysis still runs; only
rendering changes. Shape:

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
      "location": "path/to/file.ext:LINE",
      "what": "one-line statement of the defect",
      "why": "why it matters",
      "fix": "concrete fix",
      "status": "open",
      "note": "",
      "suggestion": {
        "confident": true,
        "start_line": 42,
        "end_line": 44,
        "lines": ["the whole replacement line", "and the next one"]
      }
    }
  ],
  "change": { "slug": "…", "location": "planned" | "completed", "dir": "…" },
  "spec_coverage": [ { "scenario": "WHEN … THEN …", "state": "met" | "unmet" | "cant-tell" } ],
  "could_not_verify": [ "…" ]
}
```

Rules: `verdict` is `changes-requested` iff any finding is high or medium, else
`pass`. An unmet acceptance criterion MUST also appear as a `spec-coverage`
finding with severity `high`. `change` and `spec_coverage` are present only
when a change is in scope. Valid JSON only — no fences, no commentary, **no emoji**.
If the analysis cannot run, still emit a well-formed object with `could_not_verify`
explaining why.

`endpoints` carries the engine's own resolved endpoint metadata verbatim —
`base_given`, `base_sha`, `head_sha`, and `merge_base` straight from
`semdiff`'s meta, plus `base`/`head`/`mode`. `merge_base` is absent under
`--linear`; `head`/`head_sha` are `null` in working-tree mode. The poster
(`review_gate.py post`) rejects a payload carrying no `endpoints.merge_base`
before writing anything to the pull request — an unverified base is not a
verified one. `plugins/s/harness/references/review.md` specifies this same
`endpoints` object identically, since it is a second machine-payload surface
for the same contract.

`change` carries the resolved shipd change's metadata when spec-aware mode
resolved a change. Run `semdiff change <name>` to retrieve the change's
`slug`, `location` (`planned` or `completed`), and `dir` (the change directory
path relative to the repo root), then carry all three into the `change` member.

## The optional `suggestion` object

`suggestion` is **optional** and belongs on a finding only when you would stake
the fix on being applied unread: clicking Apply on a GitHub suggestion commits
your lines verbatim, so the correctness judgement moves to whoever clicks.
Omit it and the finding renders as prose, which is the right answer whenever
you are less than sure.

The poster commits it as a `suggestion` block only when **all** of these hold —
anything else quietly degrades to prose, never an error, so a shape you got
wrong costs a suggestion and not the review:

- `confident` is exactly `true`;
- `start_line` and `end_line` are integers with `start_line <= end_line` — one
  contiguous range, the only shape GitHub can commit;
- `lines` is a non-empty list of the **whole** replacement lines. Its length
  need not match the range: a fix may add or remove lines. Never express an
  edit inside a line — no `start_column`/`end_column`, whose mere presence
  declares a partial-line edit and degrades the finding;
- the finding's `location` anchors to a RIGHT-side line of the PR diff (the
  same rule that decides inline-vs-summary for every finding), and every line
  in `start_line..end_line` is in that diff too — a comment spanning a line the
  diff does not carry is rejected outright.

The range is what the suggestion replaces, and it need not be the `location`
line; the comment anchors on the range. The block changes nothing else about
the finding — same severity marker, same what/why/fix prose — and `--json`
stays emoji- and prose-free.
