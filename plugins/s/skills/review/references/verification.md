# Verifying candidate findings

The skill reads this file for every review, to run the verify stage between
judging the diff (steps 1–6d) and reporting (step 8). The stage is never
conditional — only its detail defers here; its name and a summary of what it
does stay inline in `SKILL.md` so a reviewer that opens no reference still
knows it exists and runs.

Spawn **one** fresh-context verifier with the `Agent` tool — named exactly
`Agent`, since a restricted headless runner is configured to allow only that
one name. One verifier per review, not one per candidate: the anchoring worth
removing is to the hunt's own reasoning, and a single cold verifier already
escapes that. Isolating candidates from one another too is a refinement worth
measuring later, not one this stage pays for now.

**What the verifier receives.** Every candidate's location, claim (what), and
why it was suspected; the diff; and the ability to read files.

**What the verifier deliberately does not receive.** The reasoning that
produced the candidates — which pass found each one, or why. Cold start is
the property that matters: a verifier briefed on the hunt's own conviction
would only rubber-stamp it. A fresh reviewer meeting each candidate for the
first time is what makes a `confirmed` verdict worth more than the original
guess.

**Per-candidate verdict.** For every candidate the verifier returns exactly
one of:
- `confirmed`, with a severity (`high`/`medium`/`low`) — the verifier's own
  judgement, whether or not it agrees with a severity an earlier pass
  proposed.
- `killed`, with a one-line reason the candidate does not hold up.

Severity belongs to the verifier from this point on. An earlier pass's
proposed severity is a starting point only, and the verifier is free to
override it.

**Where kills go.** A `killed` verdict never becomes a finding, under any
status or flag — it is reported separately, in its own top-level array (see
`${CLAUDE_PLUGIN_ROOT}/skills/review/references/json-output.md`). A kill
placed inside `findings` would erase the precision this stage exists to
produce, since a consumer scoring the payload counts every `findings` entry
as reported.

**Degradation — the spawn is unavailable.** A restricted tool list can deny
the `Agent` spawn, or the spawn itself can fail. Either way, continue the
review rather than aborting it: record the payload's `verifier.state` as
`skipped` with the reason, keep every finding's proposed severity exactly as
an earlier pass left it, and add an entry to the report's explicit list of
what could not be verified. A review whose verifier did not run is never
reported as verified — a silent pass-through would be indistinguishable from
a review that never had this stage at all, which is exactly what must not
happen.
