# low-findings-never-request-changes
Status: verified
Planned-at: 624603afb43981b2335818d34a6a20bb1cd3a644
Gated-hash: 62f5ed415e9a

## Idea

Make the semantic review request changes only for `high` or `medium`
findings in code the pull request touched: lows never block and get no
thread, and a finding in untouched code is reported as "already there,
reached by this change" without counting.

### Motivation

Pull request authors get a change request and a red required check for
reviews whose only findings are `low`, or whose blocking finding sits in code
the pull request never changed, so advice and pre-existing defects block
merges. Both posting paths trust the reviewer's self-reported verdict over
the severities and the diff.

### Details

- `review_gate.py post` classifies each finding against the PR diff as
  counted or already there, derives the verdict from counted findings, folds
  every `low` into the summary instead of posting it inline, and lists
  already-there findings in their own summary section.
- The CI gate workflow classifies the reviewer's findings file the same way
  and turns a `fix-required` marker into `success` and `APPROVE` when nothing
  counted blocks; it never turns `ship-it` into `failure`.
- The disposition loop acts only on threaded findings (see below).
- Contracts, docs, tests, one patch version bump.

Affected capabilities: `semantic-review` (MODIFIED `gate-poster`, ADDED
three), `copilot-review-skill` (ADDED one). Impact: `review_gate.py`,
`copilot-review-gate.yml`, `integrations/copilot/SKILL.md`, review
references and `SKILL.md`, two docs, tests, `plugin.json`.

### Non-goals

- No change to the severity rubric.
- No configurable threshold; it stays at `medium`.
- Low threads posted before this change are not migrated or resolved.
- The CI gate never reads a `ship-it` marker as `failure`.

## Implementation

- **One owner for the threshold.** `BLOCKING_SEVERITIES = ("high",
  "medium")` below `DISPOSITIONS` in `review_gate.py`.
- **Touched vs untouched (the detection rule).** A location is *touched* when
  its path is in the PR's file list and either the file has no readable patch
  (removed, binary, or too large for GitHub to send one) or the line is in
  that file's `commentable_lines(patch)` set: the RIGHT-side added and context
  lines inside a hunk. That is the same set inline anchoring already uses, so
  "already there" can never hold an anchorable finding. Context lines count as
  touched, because a deletion or edit next to them can be what makes them
  wrong. Rejected: added lines only, which would excuse a bug the change
  causes on a neighbouring line.
- **Already there** = the finding has a `category` that is not
  `untouched-caller` or `spec-coverage`, every location parses to path and
  line, and none is touched. Those two categories stay counted, because each
  is a defect the change causes outside its own lines (a caller left broken by
  a changed contract, or an unmet scenario). A missing category, an
  unparsable location, or an unreadable diff all fail closed (counted).
  Example: a docs-only PR documents `source .env.e2e`; the unsafe heredoc in
  the untouched script is reported, not blocking.
- **Poster flow in `post()`.** After `files`/`commentable` are read, mark each
  already-there finding with `dict(f, already_there=True)`. `counted` is the
  rest. `effective_verdict(counted, review.get("spec_coverage"))` decides:
  `changes-requested` iff a counted severity is in `BLOCKING_SEVERITIES` or
  unknown, or a scenario is `unmet`. A missing severity counts as `low`. Print
  `verdict reconciled: ...` on disagreement. Then rebind `review =
  dict(review, verdict=effective, findings=<marked list>)`.
  `status_state(effective, counted, disposition)` keeps `high-only` and `none`
  as they are but reads counted findings only.
  `_split_findings` gets only counted `high`/`medium` findings; every `low` and
  every unanchorable one goes to `unanchored`.
- **Rendering.** `render_summary` skips already-there findings in "Additional
  findings" and renders them under `### Already there, reached by this
  change`. Each one's table row is suffixed `(already there)`.
  `_status_description` counts counted findings plus `, N already there`.
  The re-render after a rejected inline review passes the marked list too.
- **What folding lows means for `all`'s per-finding threads.** A low has no
  thread. So it opens no PR-room task, needs no reply, and `resolve`'s
  unresolved count never includes it. Under `all` the disposition loop still
  covers every *threaded* finding (high or medium on a touched line); a folded
  low or already-there finding may be implemented but needs no disposition.
  `prior` lists threads only, so folded lows re-render in the upserted summary
  on each re-review (no stacking). A pre-existing low thread still flows
  through `reply`/`autoreply`/`resolve` unchanged. A self-authored PR whose
  findings are all folded submits no review: the neutral `COMMENT` posts only
  when something anchors. Its summary comment still carries everything.
- **CI gate.** In the classify step, after the marker scan and directly before
  `if [[ -n "$state" ]]; then`, a `"$py_bin"` heredoc reads the findings file,
  `$files_file` (already read at the top of the step) and the body (written to
  a workspace file, never piped). It applies the same rule (findings-file
  entries carry `path`/`start_line`/`end_line` and an optional `category`) and
  writes `shipd-gate-finding-classes.json` (`already_there` indices,
  `reclassified`). It exits 0 only when the marker was `fix-required`, the
  review was grounded, the file is a non-empty array of entries that are all
  `low` or already there, and the body's `🔴 high`/`🟠 med` line count is at
  most the count of blocking already-there entries. Bash then sets
  `matched_state`/`state` to `success` and the new description. The posting
  heredoc reads the classes file. It puts already-there entries in their own
  prose section, and adds a gate note under the brand line when the verdict
  was reclassified. Downgrade only, because the file is best effort from an
  untrusted reviewer.
- Risk: a reviewer that miscategorises an untouched caller as `bug`. The
  Copilot contract and json-output rules name `untouched-caller` explicitly.

## Questions and answers

### Q1: Does the CI gate also derive its verdict from findings?
- **Question:** Should the CI review-gate workflow override a Copilot
  fix-required marker to success when its findings file shows nothing
  blocking, or keep trusting the marker alone? Options: (1) override,
  downgrade only; (2) trust the marker. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1: the CI gate changes too, downgrade only.
- **Queued:** q-gate-verdict-derived-from-findings-file

### Q2: Does the local poster stop anchoring low findings inline?
- **Question:** Should `review_gate.py post` fold low findings into the
  summary instead of posting them as inline threads, matching the CI gate?
  Options: (1) leave them inline; (2) fold them. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 2: fold lows into the summary and post no inline comment
  for them, matching the CI gate; the plan states the effect on the `all`
  scope's threads.
- **Queued:** q-poster-folds-low-findings

## Readiness attestation

### Problem and motivation

Low-only and untouched-code reviews block merges because both paths trust the
reviewer's verdict over severities and the diff.

Evidence:

- `review_gate.py:280` maps `all` to `success` iff `verdict == "pass"`;
  `:1069` passes the raw verdict; `:78`, `:919-925` map failure to
  `REQUEST_CHANGES`; `:244-260` anchors lows inline.
- `copilot-review-gate.yml:910-913` sets `failure` from the marker alone;
  `:1042-1047` maps it to `REQUEST_CHANGES`.
- Rule that lows never block: `json-output.md:48`, copilot `SKILL.md:218-220`.

### Scope and non-goals

Two posting paths, their contracts and docs change; the rubric does not.

Evidence:

- In scope: `review_gate.py` `post`, `render_summary`, `_status_description`;
  `copilot-review-gate.yml` classify and posting heredoc.
- Out of scope: the reply/autoreply/resolve/prior verbs (legacy low threads
  behave as before).

### Affected capabilities and files

Two capabilities and about eleven files.

Evidence:

- `semantic-review`: MODIFIED `gate-poster` (base 15f9d6c1afc2); ADDED
  `gate-verdict-from-severity`, `folded-findings-disposition`,
  `low-findings-docs-version`.
- `copilot-review-skill`: ADDED `gate-nonblocking-fix-required-greens`.
- Files: `plugins/s/skills/review/scripts/review_gate.py`,
  `plugins/s/integrations/copilot/copilot-review-gate.yml`,
  `plugins/s/integrations/copilot/SKILL.md`, `plugins/s/skills/review/SKILL.md`,
  `plugins/s/skills/review/references/posting.md`,
  `plugins/s/skills/review/references/json-output.md`,
  `docs/semantic-review-reference.md`, `docs/copilot-review-reference.md`,
  `plugins/s/skills/review/tests/test_review_gate.py`,
  `plugins/s/.claude-plugin/plugin.json`.
- Runnable premise: `python3 -B -m unittest
  test_review_gate.PostDispositionTest.test_omitted_scope_defaults_to_all` →
  OK, pinning a low-only `changes-requested` payload to `failure`.
- Runnable premise: the full `test_review_gate` module ran 191 tests, OK.
- Fixture premise: existing test findings carry no `category`
  (`test_review_gate.py:398-405`, `:965-970`), so the fail-closed rule leaves
  them counted.

### No open task-shaping decision

Every task-shaping decision is settled.

Evidence:

- CI gate scope: the user, Q1. Folding lows: the user, Q2.
- Touched-line rule and the two exempt categories: delegated to the planner
  by the user's request and recorded in Implementation.
