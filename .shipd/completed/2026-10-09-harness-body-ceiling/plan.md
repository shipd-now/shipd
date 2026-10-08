# harness-body-ceiling
Status: verified
Theme: developer-experience

## Idea

### Motivation

The rendered harness body ceiling stands at 200 and the worst case is 194 — the
`review` body rendered for the `aider` harness, which declares no features and
so receives the longest fallback text. Six lines of headroom.

This is the fourth raise in four versions: 120 to 140, 160, 185, 200. The
docstring that recorded the third raise said a fourth should be a conversation
about decomposing the body rather than another raise. That conversation happened
and the user decided: raise it to 250.

So this change records a deliberate decision rather than drift, which is the
distinction worth preserving in the docstring. Four raises that each looked
locally reasonable is how a guardrail stops meaning anything; four raises where
the fourth was argued and chosen is a different thing.

### Details

The ceiling test asserts 250 instead of 200, in both loops it already runs. No
body's content changes, and the figure moves only in the requirement that owns
it.

### Why the file keeps growing

`plugins/s/harness/bodies/review.md` ships standalone into other repositories
and can read no reference file. Every rule the review skill gains has to be
repeated there in full, because a harness-installed review has no `SKILL.md` and
no `references/` directory to defer to. The skill surface can extract detail
behind a load condition; the harness body has no such mechanism.

That is why its options are to grow, to split into multiple installed files, or
to accept that harness-installed reviews run a reduced skill. Raising the
ceiling postpones that choice. 250 against today's 194 buys roughly four more
changes at recent sizes, which is enough that the question will not resurface
immediately.

### Non-goals

- No change to any body's content. This is the ceiling only.
- No decomposition of the harness bodies. That is the alternative the raise
  postpones, and it is a design question rather than a line-count one.
- No change to the `SKILL.md` ceiling, which sits at 400 against 377.

## Implementation

`test_every_body_stays_lean_at_the_full_vocabulary` in
`plugins/s/skills/build/tests/test_harness_bodies.py` asserts `lines < 250`
instead of `< 200`, across both loops it already runs: every command body at the
full feature vocabulary, and every command body against every registered
harness's own declared features.

The docstring records three things. That the fourth raise was asked for and
chosen rather than reached by drift. The structural reason the file grows —
no reference mechanism, so every rule repeats in full. And the measured worst
case at the time of the raise, 194 for `review` on `aider`, so a later reader
can see how fast it moved rather than only where it ended.

The figure lives in the `body-content` requirement, which states that a surface
naming a rendered-body budget references that requirement rather than restating
the number. It changes there and nowhere else.

### Version

`plugins/s/.claude-plugin/plugin.json` bumps 0.6.271 → 0.6.272.

## Readiness attestation

### Problem and motivation

The ceiling leaves six lines of headroom, and the user has decided to raise it
to 250 rather than decompose the bodies.

Evidence: rendering every command body against every registered harness's own
declared features in this worktree gives a worst case of 194 lines, for
`review` on `aider`, against the 200 the test asserts. The `body-content`
requirement states the figure and owns it.

### Scope and non-goals

In scope: the asserted figure in the ceiling test, its docstring, the
`body-content` requirement, the version bump. Out of scope: every body's
content, harness-body decomposition, and the `SKILL.md` ceiling.

### Affected capabilities and files

One capability, one requirement.

Evidence: `harness-command-bodies` requirement `body-content`, base
`c0bd96acd83d`, computed with `spec_status.py base-hash` in this worktree.
Files: `plugins/s/skills/build/tests/test_harness_bodies.py`,
`plugins/s/.claude-plugin/plugin.json`.

Runnable premises measured here: the worst rendered body across all 26 commands
and all 15 registered harnesses is 194 lines; the test asserts `lines < 200` in
two loops, one at the full vocabulary and one per registered harness.

### No open task-shaping decision

- Raise or decompose: raise to 250, decided by the user after the third raise's
  docstring flagged the question — settled above.
- Where the figure changes: in `body-content` alone, which owns it — settled
  above.
- Whether any body's content changes: no — settled in the non-goals.
