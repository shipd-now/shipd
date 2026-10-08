# review-verifier-handover
Status: verified
Theme: reliability

## Idea

### Motivation

v0.6.269's verify stage ran for real once — the semantic review of its own pull
request — and worked: two candidates, one killed soundly, one confirmed, and it
exposed a contract break nobody else had caught. That run also found three gaps
in the instruction text, each hit in practice rather than in review.

**The verifier's response has no specified shape.** The stage says the verifier
returns `confirmed` with a severity or `killed` with a reason, and never says in
what form. The reviewer had to invent a plain-text convention and parse its own
invention.

**No subagent type is named.** "The `Agent` tool, named exactly" is satisfied by
any type, and nothing says which one reliably gives file access. The reviewer
chose `general-purpose`.

**Nothing says how the diff reaches the verifier.** Inline in the spawn message,
or re-derived by the verifier itself? The reviewer had it re-run `git diff`,
which worked, and which the instructions neither sanction nor forbid.

Left alone, every review invents its own convention. A benchmark measuring this
stage over three rounds would see kill-rate and severity variance produced by
inconsistent parsing rather than by whether verification helps — and the
registered success criterion, precision up with kills on golden findings near
zero, would be measuring an artefact. benchy-cf is holding their rounds for this
change for exactly that reason.

### Details

Specify the handover in all three directions: the subagent type, the response
shape, and how the candidates and the diff get there.

### Non-goals

- No change to what the verifier does, what it is given, or what it is denied.
  Cold start, one verifier per review, and severity ownership all stand.
- No change to the payload. `killed`, `verifier`, `candidate` and `candidates`
  are already specified and already correct; this is the stage's internal
  handover, not its output.
- **`s:validator` is deliberately not the named type**, though it is
  purpose-built for adversarial refutation and semantically the better fit. It
  ships with the plugin, and whether plugin-provided agent definitions resolve
  in a restricted headless session is unconfirmed. A type that fails to resolve
  is indistinguishable from a denied spawn, so the review would degrade to
  `skipped` and a benchmark round would be spent discovering that. The cold-start
  property comes from the spawn not being a fork, not from the agent definition,
  so the boring option loses nothing.

## Implementation

### The named type

The spawn uses `subagent_type: general-purpose` — a built-in, so it resolves in
a headless session regardless of whether the plugin's own agent definitions
load there. The name is stated rather than left to judgement.

### The response shape

The verifier answers with **one line per candidate**, in the order it received
them, and nothing else:

```
<index> confirmed <high|medium|low>
<index> killed <one-line reason>
```

Terse by design. The research behind this stage found that prompts demanding
explanations raise LLM misjudgment rates in code verification, so the verdict
carries a severity or a reason and no argument. Explanation belongs to the
review's own prose, not to the verdict line.

One line per candidate, index-prefixed, also makes the response parseable the
same way by every session — which is the whole point of specifying it.

### The handover

Candidates travel **inline in the spawn message**: index, location, claim, and
why each was suspected. That list is small and it is the thing the verifier must
judge, so it goes in the message rather than being re-derived.

The diff is **re-derived by the verifier**, which runs `semdiff diff` itself
against the review's own base and head. The spawn message names those endpoints
so the verifier resolves the same ones. This keeps the message small, uses the
engine the skill already depends on, and means the verifier reads the diff with
its own eyes rather than through the hunt's summary of it.

### Budget

`SKILL.md` is at 374 of 400 and gains only the subagent type, since the detail
belongs to the reference. The rendered harness body is at 178 of 185 and must
carry the substance inline, so its addition stays compact — the response shape
as a two-line block and the type as a clause. If it will not fit in seven lines,
stop and report rather than compressing: that file has lost content to
compression three times.

### Version

`plugins/s/.claude-plugin/plugin.json` bumps 0.6.269 → 0.6.270.

## Readiness attestation

### Problem and motivation

The verify stage's handover is unspecified in three ways, so each review invents
its own and a benchmark would measure the variance instead of the stage.

Evidence: the semantic review of pull request 278 executed the stage for real
and reported all three gaps — no output schema for the verifier's response, so
it invented and parsed its own convention; no `subagent_type`, so it chose
`general-purpose`; and no guidance on how the diff arrives, so it re-ran `git
diff`. `verification.md` lines 9 to 36 carry the spawn and verdict text and name
none of the three.

### Scope and non-goals

In scope: the named subagent type, the response shape, the handover of
candidates and the diff, on `SKILL.md`, `references/verification.md` and the
harness body; tests; the version bump.

Out of scope: what the verifier is given or denied, cold start, one-per-review,
severity ownership, the payload shape, and `s:validator` as the type.

### Affected capabilities and files

One capability, one requirement.

Evidence: `semantic-review` requirement `review-skill`, base `47bfe3f7133b`,
computed with `spec_status.py base-hash` in this worktree. Files:
`plugins/s/skills/review/SKILL.md`,
`plugins/s/skills/review/references/verification.md`,
`plugins/s/harness/bodies/review.md`,
`plugins/s/skills/review/tests/test_skill_references.py`,
`plugins/s/.claude-plugin/plugin.json`.

Runnable premises measured here: `SKILL.md` is 374 lines against a 400 ceiling;
the rendered review harness body is 178 against 185; `verification.md` names the
`Agent` tool at line 9 and specifies the per-candidate verdict at line 26
without a response shape; the review suite is green at 288 tests.

### No open task-shaping decision

- Which subagent type: `general-purpose`, because it is a built-in that resolves
  headless — settled above, with `s:validator` rejected for resolution risk
  rather than fit.
- What shape the response takes: one index-prefixed line per candidate, terse,
  no justification — settled above, with the misjudgment finding as the reason.
- How candidates and the diff arrive: candidates inline, diff re-derived from
  named endpoints — settled above.
- Whether the payload changes: no — settled in the non-goals.
