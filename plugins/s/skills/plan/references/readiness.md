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

## Attestation — evidence, printed, before emission

Meeting the checklist is not enough on its own: before proceeding from
investigation to emission, print a **user-visible readiness attestation** that
discharges each of the four items with concrete evidence. Internal reasoning
does not satisfy this — if it is not printed as response text, it does not
count.

Print it as a **markdown table** with one row per checklist item, so it can be
scanned at a glance — three columns, `#`, `Item`, and `Evidence`:

```
| # | Item | Evidence |
|---|------|----------|
| 1 | Problem and motivation | … |
| 2 | Scope and non-goals | … |
| 3 | Affected capabilities and files | … |
| 4 | No open task-shaping decision | … |
```

Each row's `Evidence` cell carries that item's citation, to these standards:

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
  and the citation must name the invocation and its observed output or exit
  code — a citation of the command's implementation source does not satisfy
  it. Two exemptions: assertions about behavior **this change will create**
  need no run (there is nothing to run yet), and assertions **no task or
  delta requirement depends on** need no run (the premise shapes nothing the
  plan hands the executor).
- **Item 4 (no open task-shaping decision).** Name every task-shaping decision
  and the rung that settled it — investigation, the personal memory store, the
  oracle, or the user — or state explicitly that none remain. Asserting
  "nothing is open" without naming the decisions considered is not sufficient
  once any decision existed to settle.

**An item with no such citation is unmet**, exactly like an item left
unaddressed — go back to investigate, consult the oracle, or ask the user, per
"How to use the gate" above. Print the attestation as a markdown table with one
cited row per checklist item before authoring any artifact.
