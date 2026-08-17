# gate-verdict-anchor
Status: verified

## Idea

Anchor the Copilot review-gate's verdict parse to the review body's last
non-empty line, so a review that merely quotes the verdict markers can never
be classified as a verdict.

### Motivation

Dogfooding v0.6.127 on shipd-now-website#18 — a pull request that itself
ships the SKILL.md — produced a Copilot review whose body quotes both
verdict markers verbatim while describing the diff, and the shipped
anywhere-in-body substring match classifies such a body as `fix-required`
(the blocking marker is tested first), posting `failure` on a passing pull
request. The skill already mandates the marker as the body's last line, so
the workflow must enforce that anchoring rather than match anywhere.

### Details

- `integrations/copilot/copilot-review-gate.yml`: the bridge job extracts
  the body's last non-empty line (carriage returns and surrounding
  whitespace tolerated) and compares it for equality against the two
  markers; anything else takes the existing fail-open branch.
- `docs/copilot-review.md`: document the bootstrap limit — GitHub runs
  `pull_request_review` workflows from the default branch's workflow file,
  so the bridge never fires on the pull request that first installs the
  gate; that one PR needs its `semantic-review` status posted by the
  session flow (`review_gate.py post`) or an admin bypass, once.
- Version bump `0.6.127` -> the next free patch version (`0.6.130` — main took
  `0.6.128` and `0.6.129` in flight) so v0.6.127 installs report `stale`
  and refresh on re-`add`.

Affected capabilities: `copilot-review-skill` (modified), `project-readme`
(modified). Impact: `plugins/s/integrations/copilot/copilot-review-gate.yml`,
`plugins/s/skills/build/tests/test_copilot_verb.py`,
`docs/copilot-review.md`, `plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No change to `SKILL.md` — its last-line marker mandate is already what
  the anchor enforces.
- No change to the fail-open rule, the reviewer/head-SHA guards, the
  `pending` job, or the `shipd copilot` verb's four-file management.
- No workaround for the default-branch trigger limit (it is GitHub
  behavior); it is documented, not engineered around.

## Implementation

- **Last-line extraction stays pure bash.** The existing regression test
  forbids piping `$REVIEW_BODY` into any matcher (the SIGPIPE/`pipefail`
  hazard recorded in the template), so the extraction uses parameter
  expansion only: strip carriage returns, trim trailing
  whitespace/newlines, take the substring after the last newline, then
  trim surrounding whitespace from that line. Rejected: `tail`/`awk`/
  `grep` extraction — it reintroduces the pipe the regression test exists
  to forbid.
- **Equality, not containment, against each marker.** The extracted line
  must equal `<!-- shipd-verdict: fix-required -->` (state `failure`) or
  `<!-- shipd-verdict: ship-it -->` (state `success`); any other line —
  including a body whose markers appear only mid-text, and an empty body —
  takes the fail-open `success` branch with the existing no-verdict
  description. With equality on a single line, at most one marker can
  match, but the `fix-required` test stays first so the template still
  reads blocking-first.
- **The observed failure is the fixture.** shipd-now-website#18's Copilot
  review (quotes both markers mid-body, ends with neither) is the repro:
  under the old logic it classifies `failure`; under the anchor it takes
  the fail-open branch. Test the three contract cases: markers quoted
  mid-text with a `ship-it` last line -> `success`; a `fix-required` last
  line -> `failure`; markers quoted only mid-text -> fail-open `success`.
- **Bootstrap note lands in the guide's merge-gate section.** GitHub runs
  `pull_request_review`-triggered workflows from the workflow file on the
  default branch (observed live: the bridge job never fired on
  shipd-now-website#18, while the `pending` job did fire via
  `pull_request` from the merge ref), so the installing pull request sits
  at `pending` unless its status is posted another way. The guide's
  merge-gate section gains a short bootstrap subsection naming the two
  outs: the session flow's `review_gate.py post`, or a one-time admin
  bypass; every pull request after the install merges is unaffected.
- **Version bump** `plugins/s/.claude-plugin/plugin.json` `0.6.127` ->
  the next free patch version (`0.6.130` — main took `0.6.128` and
  `0.6.129` in flight), per the cache-snapshot rule in `AGENTS.md` — and it is what
  makes existing v0.6.127 installs report `stale` so re-`add` refreshes
  the buggy workflow.
