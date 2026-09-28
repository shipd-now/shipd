# review-summary-footer
Status: verified

## Idea

Make a clean semantic-review comment say "No problems found." and close every posted summary with one stat line counted from the pull request's own file list.

### Motivation

A reviewer reading a clean gate comment sees "No findings.", which reads as "nothing was looked at" rather than "it looked and found no problems", and nothing on the comment says how much of the pull request the review covered. The user asked for the plainer sentence and for a coverage stat drawn from data the gate already holds.

### Details

- Replace "No findings." with "No problems found." wherever a clean review renders it: the poster's `render_summary`, the copilot reviewer's body instructions, and the review skill's report rules.
- Close the posted summary with `Reviewed N files, +A -D lines.` on every verdict, counted from GitHub's per-file `additions` and `deletions` in the PR file list the poster already fetches.
- Add the same footer to the copilot gate workflow's posting step, folded above the verdict marker so the marker stays the last line, and pin the two renderings together with a parity test.

Affected capabilities: `semantic-review` (modified), `copilot-review-skill` (modified). Impact: `plugins/s/skills/review/scripts/review_gate.py`, `plugins/s/integrations/copilot/copilot-review-gate.yml`, `plugins/s/integrations/copilot/SKILL.md`, `plugins/s/skills/review/SKILL.md`, the two review test modules, and the plugin manifest version. No new dependencies.

### Non-goals

- No change to the `--json` review object: the footer is computed by the poster, never emitted by the reviewer.
- No stat from `semdiff` (hunks, signature changes): GitHub's own line counts are the source.
- No change to the file-list reads' pagination on either surface.
- No change to inline comment bodies, severity dots, or the verdict header.

## Implementation

- **Stat source: the PR file list, not the reviewer.** `review_gate.post` already calls `_pr_files` to anchor inline comments, and each entry carries `additions` and `deletions`. The footer reads those, so it costs no extra API call and stays honest even when the reviewer misreports itself. Rejected: carrying counts in the review JSON — a second source that a steered reviewer could inflate.
- **Format.** `Reviewed N files, +A -D lines.` with an ASCII hyphen, singular `file` when N is 1. Files whose entries carry no integer counts still count as files; when no entry carries counts at all, the line is `Reviewed N files.` with no zeros invented. An empty or non-list file list renders no footer. Bool values are not counts (the same guard `_line_number` applies to line numbers).
- **Placement.** The footer is the last line of the summary body, after any "Additional findings" section, on both `pass` and `changes-requested` verdicts, and on the folded re-post after an inline review is rejected.
- **`render_summary` signature.** A new trailing keyword `files=None`; `post` passes the fetched file list on both of its calls. Existing callers and tests that omit it render exactly as before, minus the wording change.
- **Constant.** `NO_PROBLEMS = "No problems found."` in `review_gate.py` is the one rendered sentence; the two skill bodies quote the same words, and a test in `test_skill_references.py` pins all three.
- **Workflow parity.** The posting step's embedded Python gains `footer(files)` returning `["", "<line>"]` or `[]`, appended to the `prose` block that `fold` inserts above the verdict marker, so the backwards marker scan is unchanged. It mirrors `review_footer` line for line and `FooterParityTest` executes the real workflow source against the real module.
- **Docs.** The copilot skill body tells the reviewer the posting step adds the line and not to write it; the review skill body says the same of `review_gate.py post`.
- **Version.** `plugins/s/.claude-plugin/plugin.json` moves to 0.6.239, the repo's per-change convention.

Risk: a file list read that fails leaves no footer rather than a wrong one; the anchoring logic already degrades the same way. Risk: a PR over one page of files gets partial counts on the session path; that read's pagination is a non-goal here and unchanged.

## Readiness attestation

### Problem and motivation

Reviewers reading a clean gate comment see "No findings.", which reads as "nothing was looked at" rather than "it looked and found no problems", and nothing tells them how much was reviewed. The user asked for "No problems found." and a coverage stat from data the gate already has.

Evidence:

- `plugins/s/skills/review/scripts/review_gate.py:266` renders `No findings.` in place of the table.
- `plugins/s/integrations/copilot/SKILL.md:116` instructs the copilot reviewer to write the same sentence.
- Capability `semantic-review`, requirement `gate-poster`, defines the summary comment the poster upserts; requirement `summary-brand-mark` is the precedent for a small additive rendering rule.

### Scope and non-goals

The change touches the poster's renderer, the workflow's posting step, both skill bodies, and their tests; the review JSON, semdiff counts, inline comment bodies, and file-list pagination stay out.

Evidence:

- In scope: `review_gate.py:235-283` (`render_summary`), `review_gate.py:571-611` (`post`), `copilot-review-gate.yml:782-858` (`prose`, `fold`, the payload body), `SKILL.md:116` (copilot), `SKILL.md:215-216` (review).
- Out of scope: `plugins/s/skills/review/references/json-output.md` is not edited; `semdiff.py`'s `summary` object is not consumed.

### Affected capabilities and files

Two capabilities and seven files are affected, because the sentence and the footer render on two posting surfaces, each with its own body rules and tests.

Evidence:

- Capability `semantic-review`: ADDED requirements `summary-clean-wording`, `summary-review-footer`.
- Capability `copilot-review-skill`: ADDED requirements `copilot-clean-wording`, `gate-body-footer`.
- Files: `plugins/s/skills/review/scripts/review_gate.py`, `plugins/s/integrations/copilot/copilot-review-gate.yml`, `plugins/s/integrations/copilot/SKILL.md`, `plugins/s/skills/review/SKILL.md`, `plugins/s/skills/review/tests/test_review_gate.py`, `plugins/s/skills/review/tests/test_skill_references.py`, `plugins/s/.claude-plugin/plugin.json`.
- Runnable premise: `python3 -m unittest discover -s plugins/s/skills/review/tests -p 'test_*.py'` on the unedited tree → exit 0, `Ran 178 tests ... OK`; on the edited tree → exit 0, `Ran 192 tests ... OK`.
- Runnable premise: `python3 -c "import yaml; yaml.safe_load(open('plugins/s/integrations/copilot/copilot-review-gate.yml'))"` on the edited tree → exit 0.
- Runnable premise: rendering `render_summary({'verdict':'pass','effort':2,'findings':[]}, [], files=[...two entries with 12/3 and 100/0...])` → body ends `No problems found.` then `Reviewed 2 files, +112 -3 lines.`.

### No open task-shaping decision

Every task-shaping decision is settled by investigation; none remain.

Evidence:

- Stat source (GitHub per-file counts over semdiff hunks): settled by investigation, since `post` already holds the file list (`review_gate.py:579`) and the workflow's posting step reads the same endpoint (`copilot-review-gate.yml:661-668`).
- Footer placement (last line, every verdict): settled by investigation, since `fold` inserts blocks above the verdict marker so the marker scan stays valid.
- Wording ("No problems found."): given verbatim by the request.
