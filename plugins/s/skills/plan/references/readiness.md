# Readiness checklist — the single gate before emission

Emission is gated on this checklist. It is the one bar that decides whether you
keep gathering context or start writing the spec. It exists to stop both
failure modes at once: **under-asking** (emitting a thin, speculative spec) and
**over-asking** (bothering the user with friction you could have resolved
yourself).

## The four items

A plan is ready to emit only when **all four** items hold. The rules, with each
item's citation standard, live in `readiness-rules.md`, one heading per item:

1. **Problem is clear and the motivation is stateable** —
   `readiness-rules.md`, `## Problem and motivation`. A motivation you cannot
   ground precisely is un-inferrable: put it to the user (fast-path question
   round or depth-path grill) before emission.
2. **Scope and non-goals are bounded** — `## Scope and non-goals`.
3. **Affected capabilities and files are identified** —
   `## Affected capabilities and files`, which also holds the runnable-premise
   rule and its exemptions.
4. **No open decision would change the task list** —
   `## No open task-shaping decision`.

## How to use the gate

The gate itself is `readiness-rules.md`, `## The gate`; stop once it is met per
`## Stop when ready`. Once it is met, stop asking as well as investigating. When an item is unmet, climb the ladder in order:
**prefer investigation** — read the repo for anything discoverable, and as part
of that read rung **consult the personal memory store** (per `SKILL.md`'s "The
personal-memory consultation" section) and apply any relevant captured
preference; this read precedes the oracle rung. When a gap is genuinely
un-inferrable, put it to the **oracle** next (per `SKILL.md`'s "The oracle
rung" section), which consults the user's standing answer before any person is
interrupted. Only what the oracle returns `INSUFFICIENT` goes to the **user** —
batched, per the question contract in `SKILL.md`.

## Attestation — plain in the terminal, evidenced in the plan

Meeting the checklist is not enough on its own: before proceeding from
investigation to emission, print a **user-visible readiness attestation**, and
carry the evidence that discharges each of the four items into the emitted
`plan.md`. Internal reasoning does not satisfy either half — if it is not
printed as response text, and if the evidence is not in the staged `plan.md`,
it does not count.

### What you print

Four plain-language statements, one per checklist item, in checklist order —
each the item's name in bold, an em dash, then one or two sentences saying how
the item is met. Print each statement as its own paragraph, separated from the
next and from the closing line by a blank line, so a markdown terminal never
folds the four together. State counts and reasons (how many files are affected
and why, which capabilities and what they cover), not citations. Close with
one line naming the absolute path of the change's `plan.md`:

```
**Problem and motivation** — <one or two sentences>

**Scope and non-goals** — <one or two sentences>

**Affected capabilities and files** — <one or two sentences>

**No open task-shaping decision** — <one or two sentences>

Full evidence: <absolute path to the change's plan.md>
```

No table, no citations, no command output in the terminal — long evidence
cells stack into an unreadable wall and defeat the at-a-glance scan this
attestation exists for. Pick the change name first (`emission.md`'s "Pick the
change name"), so the closing line names the real destination: inside a
worktree, `planned/<change>/plan.md` under the resolved content directory —
by default `<repo-root>/.worktrees/<change>/.shipd/planned/<change>/plan.md`.

Summarize verified runnable premises in plain language here — that they ran
and what they showed — without reproducing the invocations.

### What the plan carries

The emitted `plan.md` carries a `## Readiness attestation` section whose
subsections, statements, and evidence follow `readiness-rules.md`,
`## Attestation`; `emission.md` gives the section's grammar and placement. An
item without evidence is unmet — go back to investigate, consult the oracle, or
ask the user, per "How to use the gate" above.

Print the four plain statements and the path line before authoring any
artifact.
