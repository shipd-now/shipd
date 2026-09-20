# Readiness checklist — the single gate before emission

Emission is gated on this checklist. It is the one bar that decides whether you
keep gathering context or start writing the spec. It exists to stop both
failure modes at once: **under-asking** (emitting a thin, speculative spec) and
**over-asking** (bothering the user with friction you could have resolved
yourself).

## The four items

A plan is ready to emit only when **all four** of these hold:

1. **Problem is clear and the motivation is stateable.** You can state, in one
   or two sentences, what problem this change solves. Crucially, you can also
   state its **motivation** — *why* the change is being made — in at most two
   precise sentences grounded in the request and repository context, not in
   guesswork. This is the `### Motivation` the plan will carry, so the bar is
   exacting: if you cannot ground the motivation precisely in what the request
   said and what you found in the repo, treat it as **un-inferrable** and put
   it to the user (fast-path question round or depth-path grill) before
   emission — never invent or hand-wave a reason.
2. **Scope and non-goals are bounded.** You know what is in scope and, just as
   important, what is explicitly out of scope. The edges are drawn; the change
   won't sprawl.
3. **Affected capabilities and files are identified.** You know which
   `verified/` capabilities (under the resolved content directory) the change
   touches (added or modified) and the
   concrete files/areas of code the tasks will name. No hand-waving about
   "somewhere in the codebase."
4. **No open decision would change the task list.** Every decision that would
   alter *what tasks get written* is resolved — by investigation or by a batched
   question. If answering a question would add, remove, or reshape tasks, it is
   still open.

## How to use the gate

- **All four met → emit.** Stop investigating, stop asking, and proceed to
  emission (`emission.md`). Do not open new threads of exploration once the bar
  is cleared.
- **Any item unmet → investigate, then the oracle, then ask the user.** The three
  rungs in order: **prefer investigation** — read the repo for anything
  discoverable, and as part of that read rung **consult the personal memory
  store** (per `SKILL.md`'s "The personal-memory consultation" section) and apply
  any relevant captured preference; this read precedes the oracle rung.
  When a gap is genuinely un-inferrable, put it to the **oracle** next
  (per `SKILL.md`'s "The oracle rung" section), which consults the user's standing
  answer before any person is interrupted. Only what the oracle returns
  `INSUFFICIENT` goes to the **user** — batched, per the question contract in
  `SKILL.md`. Never emit a speculative spec to paper over an unmet item.

Item 4 is the sharpest test: if you find yourself unsure whether a decision
matters, ask whether resolving it one way versus another would change the tasks
you write. If yes, it blocks emission until resolved.

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
the item is met. State counts and reasons (how many files are affected and
why, which capabilities and what they cover), not citations. Close with one
line naming the absolute path of the change's `plan.md`:

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

The emitted `plan.md` carries a `## Readiness attestation` section holding one
level-3 subsection per checklist item — `### Problem and motivation`,
`### Scope and non-goals`, `### Affected capabilities and files`,
`### No open task-shaping decision` — each opening with that item's plain
statement and then an `Evidence:` dot-point list. `emission.md` gives the
section's grammar and placement; the citation standards below are unchanged.

Each item's evidence dot-points carry that item's citation, to these standards:

- **Item 1 (problem and motivation).** Cite the `file:line`, requirement id, or
  capability name grounding the motivation — not a restatement of the
  motivation itself.
- **Item 2 (scope and non-goals).** Cite the capability name or `file:line`
  that fixes the boundary you drew.
- **Item 3 (affected capabilities and files).** Cite each affected capability
  by name and each affected file by `file:line`. A vague "somewhere in the
  codebase" is not a citation and leaves the item unmet. **Runnable premises
  are evidence here, not a fifth item:** where the plan asserts how an
  existing command, script, or flag behaves and a task or delta requirement
  depends on that assertion, the command must have been run before emission,
  and this subsection's evidence must name the invocation and its observed
  output or exit code — a citation of the command's implementation source does
  not satisfy it. Two exemptions: assertions about behavior **this change will
  create** need no run (there is nothing to run yet), and assertions **no task
  or delta requirement depends on** need no run (the premise shapes nothing the
  plan hands the executor).
- **Item 4 (no open task-shaping decision).** Name every task-shaping decision
  and the rung that settled it — investigation, the personal memory store, the
  oracle, or the user — or state explicitly that none remain. Asserting
  "nothing is open" without naming the decisions considered is not sufficient
  once any decision existed to settle.

**An item whose subsection carries no such evidence dot-point is unmet**,
exactly like an item left unaddressed — go back to investigate, consult the
oracle, or ask the user, per "How to use the gate" above, and do not install
the change until every item is discharged.

**Phrasing rule.** The context-sufficiency gate scans all of `plan.md` outside
its own `## Context insufficient` section, so write the section in settled
prose that carries none of the gate's placeholder markers — the same caution
the oracle ledger already carries (`emission.md`, "the oracle ledger").

Print the four plain statements and the path line before authoring any
artifact.
