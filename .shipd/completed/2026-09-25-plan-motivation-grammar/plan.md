# plan-motivation-grammar
Status: verified

## Idea

Require a plan's `### Motivation` to name who is blocked and from what, so the
rule stops rewarding a restatement of a file's current state.

### Motivation

Every surface that governs `### Motivation` states only a prohibition — "never
a guess", "never invent or hand-wave" — and the newest one asks outright for
"the repository's terms", so the cheapest way for an author to comply is to
quote a file's literal contents; across 21 epics in this workspace the result
is measurable, with `shipd-now-site` carrying 2.3 plumbing markers per
motivation against 0.3 outcome markers and four of its seven motivations
sharing a 52–66% verbatim template. A reader of those plans learns which file
held an `h1`, never why anyone wanted the change.

### Details

- Bump the plugin version, which AGENTS.md requires in the same PR for any
  change under `plugins/s/`.
- Amend `plan-document-sections` in the `shipd-spec-format` capability so the
  motivation must name the affected party and what they cannot do, with
  repository state admissible as evidence for that claim but never as the
  claim itself.
- Rewrite the rule on all four prose surfaces that state it:
  `plugins/s/harness/references/plan.md`,
  `plugins/s/skills/plan/references/emission.md`,
  `plugins/s/skills/plan/references/readiness.md`, and `.shipd/README.md`.
- Keep the anti-invention rule intact on every surface — it is doing necessary
  work, it is simply incomplete.

Affected capabilities: `shipd-spec-format` (modified). Impact:
`plugins/s/harness/references/plan.md`,
`plugins/s/skills/plan/references/emission.md`,
`plugins/s/skills/plan/references/readiness.md`, `.shipd/README.md`, and the
version bump in `plugins/s/.claude-plugin/plugin.json`. No code and no new
dependencies.

### Non-goals

- No lint rule. `spec_lint.py` checks the Idea subsections for presence only
  and says so in its own comment; plumbing-only prose is not mechanically
  separable from a change whose why genuinely is a file state.
- No change to the shipped example motivations in
  `plugins/s/skills/build/tests/fixtures/sample` or
  `plugins/s/skills/onboard/assets/sandbox` — both already model outcome
  language.
- No rewriting of motivations in already-archived changes; those are a record.
- No change to the two-sentence length limit, to `### Details`, to
  `### Non-goals`, or to any other part of the plan grammar.

## Implementation

- **The contract carries the rule; the prose surfaces restate it.** The
  binding edit is to `plan-document-sections`, whose motivation clause becomes:
  at most two sentences naming who is blocked and what they cannot do,
  grounded in the planning context and never a guess, with repository state
  admissible as evidence for that claim but not as the claim itself. The four
  prose surfaces then say the same thing in their own register. Rejected:
  changing only the prose — the capability is the format authority the linter
  and every authoring skill resolve against, so a prose-only change would drift
  from it at the next review.
- **`harness/references/plan.md` needs the largest rewrite, because it is the
  most causal.** Its entire current rule is one line — "Why this is being done,
  in the repository's terms" — which actively instructs the failure mode. It
  becomes a short block naming the affected party and what they cannot do, with
  file state as evidence. That file is the source copied to
  `~/.shipd/harness/references/` by `harness_generate.py` (`REFS_SUBDIR`,
  `USER_REFS`), so editing the repo copy is the whole fix; the installed copy
  differs only by the content-directory path substitution the generator applies.
- **`readiness.md` keeps its escalation rule and gains the content bar.** Item
  1 already tells the planner to escalate an un-inferrable motivation to the
  user rather than invent one. That stays exactly as it is; what is added is
  what a *sufficient* motivation contains, so the item tests both that the
  motivation is grounded and that it names a blocked party.
- **The two shipped examples become the canonical illustrations.** Both already
  read correctly — the sample fixture's "leave the sample auth capability open
  to hijacking and brute-force attempts" and the onboard sandbox's "no way to
  see its cards yet" — so `emission.md`'s worked example needs no edit and the
  new rule cites the shape those already demonstrate.

Risk: a change whose why genuinely is a repository state — a format bump, a
migration, a lint-rule fix — could read as non-compliant under a rule phrased
too absolutely. Guarded by admitting repository state as evidence and by
phrasing the requirement around naming the affected party rather than banning
file references.

Risk: the four prose surfaces drift apart again as they did here. Guarded by
making the capability requirement the single normative statement the other
three defer to, rather than four independent phrasings.
