# Machine output mode

The skill reads this file when the user passes `--json`, or when it is producing the JSON object the poster consumes.

When the user passes `--json`, emit a single JSON object to stdout and nothing
else — no preamble, no walkthrough, no diagrams. All analysis still runs; only
rendering changes. Shape:

```json
{
  "verdict": "pass" | "changes-requested",
  "effort": 3,
  "findings": [
    {
      "id": "f1",
      "severity": "high" | "medium" | "low",
      "cohort": "bug" | "contract" | "edge-case" | "untouched-caller" | "spec-coverage" | "test-coverage",
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
  "spec_coverage": [ { "scenario": "WHEN … THEN …", "state": "met" | "unmet" | "cant-tell" } ],
  "could_not_verify": [ "…" ]
}
```

Rules: `verdict` is `changes-requested` iff any finding is high or medium, else
`pass`. An unmet acceptance criterion MUST also appear as a `spec-coverage`
finding with severity `high`. `spec_coverage` is present only when a change is
in scope. Valid JSON only — no fences, no commentary, **no emoji**. If the
analysis cannot run, still emit a well-formed object with `could_not_verify`
explaining why.

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
