# Depth-path dialogue — the bounded grill loop

Loaded only when the depth gate selects the depth path (see `SKILL.md`). This
reference replaces the fast path's batched question contract with a bounded
grill loop of grouped question rounds that pressure-tests the plan before
emission.
It has a defined start (the gate) and a defined end (no open decision would
change the task list) — it is **not** an open-ended discussion. Thinking time
without a destination is out of scope; every exchange must move a task-shaping
decision toward resolution.

## Build the agenda

From readiness item 4 (`readiness.md` — "no open decision would change the task
list"), derive an **agenda** of the open task-shaping decisions: every choice
whose resolution one way versus another would add, remove, or reshape tasks.
These are the only things worth grilling on. A decision that does not change the
task list is not on the agenda.

Order the agenda so that decisions which unlock or constrain later ones come
first — resolving the architecture usually reshapes the smaller choices beneath
it.

## The fact/decision test (apply to every agenda candidate)

Before putting anything to the user, split it:

- **Fact** — discoverable from the repository or the request (an existing
  pattern, a current interface, a naming convention, what the code does today).
  **Read it. Never ask it.** A question you could have answered by reading is a
  failure of this skill (the codebase-first rule still binds on the depth path).
- **Decision** — a genuine choice that investigation cannot settle, whose answer
  shapes the tasks. Only these belong in the loop.

Then, before any round opens, **route every surviving decision through the
oracle rung** (see `SKILL.md`'s "The oracle rung" section): consult the
oracle on each decision, fold in the ones it answers `ANSWER`, and carry only
the `INSUFFICIENT` decisions into the agenda's grouped rounds below.
Oracle-settled decisions are reported as
`Q<n> — <question summary> → <answer summary>`, with who settled it, their
`Cited:` citations, and `/s:teach <change> Q<n>` as the correction path, in the
next round's context brief — or in the closing shared-understanding summary
when no round remains to open.

## Context brief — open every round with a restatement

Every decision-resolving round opens with a **context brief**, and because the
harness can drop or hide text that shares a turn with an AskUserQuestion call,
the brief and its questions are delivered as **plain text** — no dialog shares
the turn. The brief is a **precondition of the round**: it must be user-visible
response text — internal reasoning does not count — and issuing a round whose
turn did not first present the visible brief is a protocol violation. Do not
put the questions until the brief is printed. The brief's content:

- **What is already known** — restate the accumulated understanding so the user
  sees that nothing already settled will be re-asked. Every decision the oracle
  settled since the last round is listed here as
  `Q<n> — <question summary> → <answer summary>`, with who settled it and its
  `Cited:` source(s), and the list names `/s:teach <change> Q<n>` as the way to
  teach the oracle a different answer.
- **A diagram, only when one carries the decisions** — attach a visual only
  where it actually carries a decision the round is putting to the user (defer
  to `visualization.md`'s bar; never a decorative visual).
- **The open decisions** — the list this round will settle — and then, in the
  same plain-text message, the round's **numbered questions**: each with
  concrete options, the recommended default named first, collected from the
  user's typed reply (e.g. "1a 2c"). No AskUserQuestion is issued in a turn
  that carries a brief.

Two exemptions:

- **The shared-understanding summary needs no preceding brief.** That summary is
  itself a recap; prefacing a recap with another recap is circular. The brief
  contract covers decision-resolving rounds only.
- **Dependent-chain follow-ups take a one-line delta, not a full brief.** Inside
  a dependent chain, each follow-up question is prefaced by a single line
  stating what the previous answer changed rather than a full restatement — the
  follow-up is also plain text, answered by a typed reply.

## Resolve the agenda in grouped rounds

Once the agenda is built and each item has passed the fact/decision test,
**partition the remaining decisions** before asking anything:

- **Independent decisions** — those whose framing does not depend on another
  decision's answer. Group these into a **single plain-text round of up to
  four** numbered questions, each with concrete options and its **recommended
  option named first** so the cheapest answer is to accept it, collected from
  the user's typed reply. A fifth-or-later independent decision waits for the
  next round.
- **Dependent chains** — decisions whose question cannot even be phrased until
  an earlier answer lands. Ask these **one at a time in dependency order**,
  each follow-up prefaced by a one-line delta of what the previous answer
  changed (see the "Context brief" section) and answered by a typed reply.

**When unsure whether a decision is independent, treat it as dependent.** The
conservative failure mode is one extra round, never a question asked before the
context that frames it exists.

Where a diagram or comparison table would carry a decision, attach a visual
(see the visualization load rule below).

Then work each round:

1. Issue the round — the grouped plain-text questions for the independent set,
   or the next single question in a dependent chain.
2. Fold the answers back into the agenda: a resolved decision may close, open,
   or reshape others. Re-derive what remains open.
3. Repeat — re-partition the still-open agenda and issue the next round — with
   the next still-open decisions.

**End condition.** The loop ends when no open decision would change the task
list — i.e. readiness item 4 is satisfied. Stop asking and proceed to the
shared-understanding summary. Do not manufacture further questions once the
agenda is empty; a grounded stop is the goal, not maximal interrogation.

## Soft cap — an oversized agenda is a decomposition signal

If the agenda of open task-shaping decisions grows past **roughly six**, that is
a signal the change is epic-sized, not a signal to keep interviewing. Stop and
suggest decomposing the change via `/s:epic` rather than continuing the loop.
An interview that runs long is hiding a change that should have been split.

## Visualization load rule

Load `visualization.md` **at most once per session**, the first time a visual
would actually carry a decision being put to the user. Do not load it
pre-emptively, and do not emit decorative visuals — see that reference for the
idioms and the prohibition.

## Close with a shared-understanding summary

When the loop ends, do not emit silently. First present a **shared-understanding
summary** so the user confirms you built the right thing:

- **Problem** — the problem this change solves, in one or two sentences.
- **Chosen approach** — the approach settled on, at a glance.
- **Decisions** — each resolved decision with a one-line rationale.
- **Known risks** — what could go wrong and how the plan guards it.

This summary is the **depth-path** confirmation, reached only because the gate
needed more info and the grill loop ran. A gate that opens no interactive
rounds — the fast path, or a depth path whose grill agenda is already empty —
proceeds directly to emission, with no summary and no "emit" step. Only when
the grill loop actually ran one or more rounds does this summary appear. The summary
is itself load-bearing prose, so close it as plain text: end the message by
asking the user to **reply "emit" to proceed or say what to refine**. Do not
issue an AskUserQuestion for this confirmation. Only on a typed "emit" (or
equivalent go-ahead) do you proceed to emission (`emission.md`) — this is the
depth path's "don't act until confirmed" gate. The readiness checklist remains
the formal terminator for both paths; this summary sits in front of emission on
the depth path only. The fast path adds no such step.
