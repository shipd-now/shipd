# review-stage-options
Status: verified
Epic: named-pipelines

## Idea

Teach `/s:review` and `review_gate.py` the pipeline's review-stage options —
a disposition scope (`all` | `high-only` | `none`) with mechanical
auto-replies that keep finding threads resolvable, and a recorded model
tier — so both delivery drivers can invoke a cheapened review.

### Motivation

The pipeline schema already types the review stage's `disposition` and
`model` options and the eco/basic presets declare them, but no consumer
honors them: the `/s:review` posting flow always runs the full per-finding
disposition loop and the gate's commit status always fails on any
high/medium finding. Without a consumer, `{"autonomous-pipeline": "eco"}`
cannot cut review token spend, and a preset review with unimplemented
medium findings would deadlock auto-merge behind a permanently red
`semantic-review` status.

### Details

- `review_gate.py post` gains `--disposition` (default `all`) and
  `--model`: a disposition-aware commit-status mapping, plus policy and
  model provenance lines in the posted summary comment.
- `review_gate.py` gains an `autoreply` verb: canonical policy replies on
  gate-authored, unreplied finding threads selected by scope, giving
  `resolve` its disposition evidence without per-finding judgment.
- `/s:review` (SKILL.md) documents the option surface an invoker passes,
  the scope-aware posting flow, and which driver applies the model tier.

Affected capability: `semantic-review` (modified). Impact:
`plugins/s/skills/review/scripts/review_gate.py`,
`plugins/s/skills/review/SKILL.md`,
`plugins/s/skills/review/tests/test_review_gate.py`,
`plugins/s/.claude-plugin/plugin.json` (version bump). No new
dependencies; the gate script stays stdlib-only.

### Non-goals

- No driver wiring: the autopilot conveying stage options and tiers is
  epic member `autopilot-stage-options`; `/s:build`/`/s:plan` resolving
  the pipeline interactively is member `interactive-pipeline`. Here the
  options arrive as explicit invocation input, defaulting to today's
  behavior.
- No pipeline resolution inside `/s:review` or `review_gate.py` — neither
  reads the `autonomous-pipeline` key; the invoker supplies the options.
- No change to the `--json` verdict contract: `changes-requested` iff any
  high/medium finding, regardless of scope. Only the commit-status
  mapping is policy-aware.
- No in-skill model switching: `/s:review` never spawns itself on another
  model; the tier is recorded provenance, applied by the driver that
  spawns the reviewing session (per the epic's documented-applicability
  decision).
- No thread-listing pagination changes: `autoreply` inherits the existing
  100-thread/100-comment GraphQL cap the resolve verb already documents.

## Implementation

- **Disposition-aware status mapping lives in `post`, not in the verdict.**
  `post --disposition <scope>` maps state as: `all` → `success` iff
  verdict `pass` (unchanged); `high-only` → `success` iff no finding has
  severity `high`; `none` → always `success`. The findings JSON and the
  rendered verdict header stay severity-honest; the status is where merge
  policy acts, and it is the mechanical, fake-`gh`-tested layer. Rejected:
  recomputing the verdict in the skill under the scope — it would fork the
  machine contract (`verdict` iff high/medium) that the human header must
  mirror, and hide policy in prose instead of tested code.
- **Why the mapping must change at all:** the autopilot review grade
  requires a green `semantic-review` status AND `unresolved=0`
  (`autopilot.py:222-256`), and auto-merge waits on the required check.
  Under `high-only`, medium findings are auto-replied, never implemented —
  with the old mapping the status stays `failure` forever. Under `none`
  the status is always `success` — the epic's "the gate stays honest, the
  loop costs nothing": honesty is the posted findings, not a red status
  nobody may act on. Shipped presets never use `none`.
- **Policy provenance in the summary.** When the scope is not `all`, the
  summary comment carries a `Disposition: <scope>` line, and the commit
  status description appends `(disposition <scope>)`, so a green status
  over visible findings is explained on the PR. When `--model <tier>` is
  given, the summary carries a `Model: <tier>` line — symbolic
  (`session`/`tier-below`/`tier-two-below`) or concrete id, printed as
  given, never resolved here.
- **`autoreply <pr> --disposition high-only|none [--body <text>]`.**
  Reuses `_list_review_threads` and the REST `in_reply_to` create through
  the same injectable `gh` seam. Selects gate-authored (root author ==
  viewer), unresolved threads with no reply yet; parses the root
  severity from the gate's own `_inline_body` first-line format
  `**<severity> — <what>**`; replies to `medium`/`low` under `high-only`
  and to every thread under `none`. Default body names the policy, e.g.
  "Auto-dispositioned by review policy (disposition: high-only): below
  the acting threshold; not implemented." Prints `replied=<n>` on stdout
  and exits 0; already-replied threads are skipped, so re-runs are
  idempotent. Under `high-only`, a root whose severity cannot be parsed
  is left untouched and reported (conservative: judgment-worthy); under
  `none`, parsing is not consulted — every gate thread gets the reply.
  Rejected: matching findings to threads via a `--from` JSON by
  path/line — `post` returns no comment ids, and the body prefix is a
  format this same script authors.
- **`/s:review` SKILL.md changes.** A "Review stage options" note in the
  posting section: the invoker (a driving session or the user) may pass
  `disposition=<scope>` and `model=<tier>`; both default to today's
  behavior (`all`, no tier line). The posting flow becomes scope-aware:
  `all` → the existing full loop; `high-only` → implement each high
  finding (or push back with a reasoned `reply` when judged wrong),
  re-review and re-post after any push, then `autoreply`, then `resolve`;
  `none` → post, `autoreply`, `resolve` — no per-finding judgment. Pass
  the scope and tier through to `post`, and include the scope in the
  final report. Applicability is documented per the epic: the tier names
  the model the reviewing session should run on; the autopilot applies it
  when spawning the review stage, and interactively it is informational.
- **Tests** extend `plugins/s/skills/review/tests/test_review_gate.py`
  (fake `gh` seam, no network): status mapping per scope, provenance
  lines, description suffix, autoreply selection by severity, high-only
  leaving high and unparseable roots untouched, idempotent re-run, and
  `none` replying to all. CI already discovers this suite.
- **Risk:** severity parsing couples `autoreply` to `_inline_body`'s
  format. Guard: derive both from one module-level severity-prefix
  regex/constant beside `_inline_body`, and cover the round-trip
  (render → parse) in the tests.
- **Version bump:** `plugins/s/` changes, so
  `plugins/s/.claude-plugin/plugin.json` bumps in the same PR.
