# review-output-redesign
Status: verified
Theme: developer-experience

## Idea

Make the gate's pull-request output a scannable review — verdict, severity
table, brief per-finding detail — and let a confident fix be applied in one
click on both the gate and `/s:review`.

### Motivation

The gate posts its reviewer's free markdown as a plain issue comment
(`copilot-review-gate.yml:574`), so a reader gets an unstructured transcript
with no anchoring and no verdict to scan for, while `semantic-review`'s own
`review-skill` requirement already mandates a `## Findings` header and a
severity table for `/s:review`. The gate has never rendered the contract its
sibling surface already meets, and neither surface offers a fix a reviewer can
apply without retyping it.

### Details

- Render the gate's review body to the same shape `review-skill` mandates: the
  verdict header first, then a severity table, then brief per-finding detail.
- Post it as a real pull-request review carrying anchored inline comments,
  replacing the `gh pr comment` issue comment.
- Carry a committable `suggestion` block on findings the reviewer marks
  confident, on both the gate and `/s:review`.
- Treat an applied suggestion as the disposition loop's implement branch.

Affected capabilities: `semantic-review` (modified), `copilot-review-skill`
(modified). Impact: `plugins/s/skills/review/scripts/review_gate.py`,
`plugins/s/integrations/copilot/SKILL.md`,
`plugins/s/integrations/copilot/copilot-review-gate.yml`, and tests under
`plugins/s/skills/build/tests/`.

### Non-goals

- No change to the verdict marker contract. The last-non-empty-line equality
  rule, `SHIPD_GATE_FAIL_OPEN`, and the `semantic-review` commit status keep
  their current behaviour.
- No `REQUEST_CHANGES`. The review stays a `COMMENT`; the required status is
  the merge-blocking signal and a review decision would need human dismissal.
- No relaxation of the emoji rules. The master's three sanctioned sites stand
  and `--json` stays free of emoji and prose.
- No new reviewer credential. The CLI reviewer keeps no repository access.

## Implementation

**The findings cross the trust boundary as data, not prose.** The CLI reviewer
runs `--allow-all-tools` over a diff it cannot be trusted not to be steered by,
and its step binds no repository credential — so it cannot post. It writes a
findings JSON file beside the markdown body, and the posting step, which holds
`github.token` and never the reviewer's, reads that file and builds the review.
This is the existing workspace-file handoff the workflow already documents,
carrying structured data rather than only text.

Rejected: letting the reviewer post its own review. It would need a repository
token in the step the trust boundary exists to keep credential-free.

**Suggestion eligibility.** A finding carries a committable `suggestion` block
only when the reviewer marks its fix confident **and** the replacement covers
one or more contiguous whole lines that already anchor to a RIGHT-side
commentable line of the diff — the same anchoring `gate-poster` enforces for
inline comments. A partial-line edit, a fix spanning a discontiguous range, or
an unanchorable one degrades to prose. Multi-line replacements are expected and
supported; the constraint is whole lines, not one line.

**The posting step validates before it trusts.** Paths and line ranges in the
findings file are checked against the diff the step computed itself; a finding
naming a path or range outside it is folded into the summary as prose rather
than posted as an anchored suggestion. A steered reviewer can then still write
a misleading suggestion, but cannot anchor one onto a file the pull request
never touched.

**Emoji and suggestions are decoupled.** `_inline_body`'s docstring currently
forbids both in one sentence, restating a completed change's non-goal rather
than a verified rule. The suggestion prohibition is lifted under the
eligibility rule above; the emoji rules are untouched, so the master's three
sanctioned sites and the `--json` mode keep their current behaviour.

**An applied suggestion is dispositioned.** The disposition loop demands
implement-or-reply on every finding; clicking Apply is the implement branch,
evidenced by the resulting commit, so such a thread needs no separate reply and
`resolve --check` treats it like any other implemented finding.

**Risk.** A one-click fix moves the correctness judgement onto whoever clicks.
The confidence gate and the whole-line-in-diff constraint keep suggestions to
cases where a wrong patch is visible on sight, and the verified disposition
rule — implement when correct, otherwise reply with the reason — still governs.

## Questions and answers

### Q1: Which review event should a fix-required verdict submit?
- **Question:** When the gate posts a `fix-required` verdict, should the GitHub
  review be submitted as `COMMENT` (as `review_gate.py:402` hardcodes) or
  `REQUEST_CHANGES`? Options: (1) keep `COMMENT`, the required status being the
  merge blocker; (2) `REQUEST_CHANGES`, blocking by status and review decision
  both. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Keep `COMMENT`. The required `semantic-review` status is already
  the merge-blocking signal and `gate-poster` treats the review POST as the
  carrier for inline comments, so a review decision would add a second block
  that a human must dismiss even after the fix lands.
- **Queued:** none

### Q2: Which findings carry a committable suggestion?
- **Question:** Which findings should carry a one-click `suggestion` block,
  given the reviewer runs with all tools over a steerable diff? Options: (1)
  only a fix the reviewer marks confident whose replacement is whole lines
  inside the diff; (2) any mechanically expressible fix; (3) none, keeping the
  prose-only rule. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option (1), with the replacement free to span more than one line:
  the constraint is contiguous **whole** lines anchoring inside the diff, not a
  single line. The oracle established that the prose-only rule is a completed
  change's non-goal rather than a verified ban, so nothing durable is overturned
  by lifting it under that gate.
- **Queued:** none
