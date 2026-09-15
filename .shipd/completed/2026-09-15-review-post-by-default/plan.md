# review-post-by-default
Status: verified

## Idea

Make `/s:review <pr>` post its review to that pull request by default, and make
implementing and resolving the findings an opt-in the invoker must ask for.

### Motivation

`posting.md` forbids posting without an explicit request, then makes every
posting flow finish by implementing findings and resolving the threads, so a
review of someone else's pull request either never reaches it or arrives
auto-dispositioned. The reviewer's findings should land on the pull request and
stay open for whoever owns it.

### Details

- Invert the posting default: a review whose target is a named pull request
  posts its verdict; a bare `/s:review` stays local and posts nothing.
- Make the disposition loop and the thread resolution opt-in, so the default
  posted review implements nothing and resolves nothing.
- Carry the same inversion through the harness review body, the harness review
  reference, and the concept guide.
- Prefix every posted finding's severity with its 🔴/🟠/🟡 dot, on both posting
  surfaces, so a finding on the pull request reads like a row of the summary
  table.

Affected capabilities: `semantic-review` (modified) and `project-readme`
(modified). Impact: `plugins/s/skills/review/references/posting.md`,
`plugins/s/skills/review/SKILL.md`, `plugins/s/harness/bodies/review.md`,
`plugins/s/harness/references/review.md`, `docs/semantic-review.md`,
`plugins/s/skills/review/scripts/review_gate.py`,
`plugins/s/integrations/copilot/copilot-review-gate.yml`,
`plugins/s/integrations/copilot/SKILL.md`, and the review test suites. No new
dependencies.

### Non-goals

- No behavioural change to `autoreply`, `resolve`, `prior` or `protect` beyond
  the severity marker they read through `parse_severity`.
- No severity dot in the `--json` payload — the dot is a rendering concern.
- No ownership guard refusing `resolve` or `autoreply` on a pull request the
  authenticated viewer does not own, and no new `unresolve` verb.
- No change to the `semantic-review` commit status mapping, and none to the
  autopilot's review stage, which drives the poster through its own prompt.
- No posting from a bare `/s:review` that names no pull request.

## Implementation

- **The trigger is a named pull request, nothing else.** Posting fires when the
  invocation names one — a pull request URL, `#<number>`, a bare number, or a
  branch the user points at a pull request. A bare `/s:review` reviews the
  working tree and posts nothing, because the working tree may hold commits and
  edits that the pull request's head does not carry. Rejected: posting whenever
  the current branch happens to have an open pull request — it posts a review of
  code the pull request does not contain.
- **The commit status is unchanged.** The flow runs `review_gate.py post <pr>
  --from <file>` with no `--disposition` flag. `post --help` reports
  `--disposition {all,high-only,none} … (default: all)`, so the status stays
  severity-honest: `success` iff the verdict is `pass`. Rejected: always-green
  and no-status — both would need a poster change, and both hide a real verdict
  from the pull request's own gate.
- **Disposition becomes opt-in, and posting no longer implies it.** `posting.md`
  keeps steps 6 and 7 verbatim, but gates them on the invoker asking for the
  findings to be dispositioned — a driving session passing `disposition=<scope>`
  (which the autopilot already does at
  `plugins/s/skills/build/scripts/autopilot.py:422-470`), or the user asking for
  the findings to be fixed. Absent that ask, the flow stops after posting and
  reports, leaving every thread open for the pull request's owner. Rejected:
  deleting the disposition loop — the autopilot grades its review stage on
  `resolve --check` reporting `unresolved=0` (`autopilot.py:268`), so the loop
  must stay reachable.
- **The pull-request resolution lives in `posting.md`, not `SKILL.md`.**
  `wc -l plugins/s/skills/review/SKILL.md` reports `299` against the ceiling of
  300 asserted at `plugins/s/skills/review/tests/test_skill_references.py:218`,
  so `SKILL.md` gains only a pointer bullet and must be compressed to absorb it.
  The `posting.md` load condition in the References table changes from "posting
  to a PR was explicitly requested" to a pull request being in scope; the
  condition sentence under that file's title changes with it, since
  `test_skill_references.py` pins at least three shared content words between
  the two.
- **Both reference-free surfaces carry the inversion inline.**
  `plugins/s/harness/bodies/review.md:84` and
  `plugins/s/harness/references/review.md:6` each state the old rule in their own
  body, and neither can read a file under `skills/review/references/`.

- **The severity dot is rendered, never stored.** `_sev_marker` gains the
  finding's `_SEV_DOT` entry directly before the severity word, and the folded
  findings section gains the same dot. The `--json` object is untouched, so the
  machine payload stays emoji-free and no `--json` consumer changes.
- **The marker's literal stays in one place.** `_SEV_MARKER_RE` is derived from
  the renderer's format through a sentinel today, and that derivation must
  survive: keep a single format string carrying a dot placeholder and a severity
  placeholder, and build both the renderer and the regex from it. Rejected:
  writing the regex out by hand — it is exactly the drift the current sentinel
  exists to prevent, and `auto-disposition-verb` requires the two to share one
  constant.
- **The parser accepts the dot as optional.** Threads already posted on open
  pull requests carry the dotless marker. A parser that rejected them would make
  `prior` report their severity as null and make
  `autoreply --disposition high-only` treat them as unparseable, so the dot
  group is optional in the regex. Rejected: a one-off migration of existing
  comment bodies — it rewrites other people's pull requests to no benefit.
- **The vendored workflow renders the dot in its own Python.**
  `plugins/s/integrations/copilot/copilot-review-gate.yml` carries its own
  `inline_body` and folded-finding renderer, independent of `review_gate.py`, so
  the same dot is applied there. That file is a managed file keyed to the plugin
  version, refreshed in gated repositories by `/s:gate update`.

Risk: a user reviewing a colleague's pull request in a repository that requires
the `semantic-review` check now turns that check red on a high or medium
finding. That is the gate behaving as specified, and the pull request's owner
clears it by addressing the findings.

Risk: `SKILL.md` overflows its 300-line ceiling. Guard: the compression task
runs `wc -l` and the existing ceiling test covers it in CI.

## Questions and answers

### Q1: What does the commit status do on a default posted review?
- **Question:** When a review posts by default without dispositioning its
  findings, should the `semantic-review` commit status stay severity-honest,
  always report success, or not be written at all? Recommendation: stay
  severity-honest.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Keep it severity-honest, exactly as today — `success` iff the
  verdict is `pass`, `failure` on any high or medium. The review stays a real
  gate the pull request's owner must clear, and the poster needs no change.
- **Queued:** none

### Q2: When does posting fire by default?
- **Question:** Should posting fire only when the invocation names a pull
  request, also when a bare `/s:review` runs on a branch carrying an open pull
  request, or also for a working-tree review posted onto that pull request?
  Recommendation: only a named pull request.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Only when the invocation names a pull request. A bare `/s:review`
  stays local, because a working-tree review can describe code the pull
  request's head does not carry.
- **Queued:** none

### Q3: How far past the prose flip does the change go?
- **Question:** Should the change stay prose-only, add an ownership guard to
  `resolve` and `autoreply`, or add that guard plus a new `unresolve` verb?
  Recommendation: prose only.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Prose only. Flip the default across the skill, both harness
  surfaces, the guide and the specs, and change no Python. The ownership guard
  and an `unresolve` verb are separate work.
- **Queued:** none
