<!-- doc-type: reference -->

# Plan authoring rules

This file is the one source of the rules for writing a plan's prose: what each
part of a change holds and how to phrase it. Engines load it alongside their own
emission mechanics. It carries rules only,
with no commands, no paths, and no interaction, so any engine can follow it.
Each part below has a stable `##` heading, because external loaders read the
file by heading.

## Motivation

State why the change is being made in at most two sentences, naming who is
blocked and what they cannot do. Ground it in the request and the repository
context, never a guess. When you cannot state the reason precisely from what you
have, find out before you write it. Repository state may be cited as evidence
for the reason, but it is never the reason itself: a file being a placeholder,
absent, or holding particular content is not on its own a motivation.

## Non-goals

List what is explicitly out of scope, with at least one exclusion. A plan has no
Goals section anywhere, because the idea already states the goals and stating
them twice invites drift. The approaches you considered and dropped belong with
the decision that rejected them, not in a goals list.

## Implementation decisions

Record the binding decisions an executor must not re-make, one at a time, in the
style of an architecture decision record. For each decision give the choice
made, a short rationale, and the rejected alternative where it clarifies why, so
an executor never has to reconstruct why a decision was made. Name the files and
components touched, and the interfaces and data shapes the change introduces or
alters. Record the risks and trade-offs, what could go wrong and how the plan
guards against it. A trivial change may keep this part brief, but it still
records why the approach is sound.

## Requirements

Each requirement states one behaviour with a SHALL or MUST statement and carries
a kebab-case id that is unique within the change. Phrase the statement in one of
the five EARS shapes: the plain ubiquitous form, event-driven ("when a
trigger occurs"), state-driven ("while a state holds"), unwanted-behaviour ("if
a condition arises, then"), or optional-feature ("where a feature is present").
EARS is authoring guidance, so a statement needs only the SHALL or MUST token,
never a matching template. A requirement that bundles two behaviours is split
into two.

## Scenarios

Give every requirement at least one scenario. A scenario holds one concrete WHEN
that names the exact trigger, with an optional GIVEN for the starting state, and
an observable THEN that a reader could check by running or inspecting the result.
Write the trigger as a specific action or input, never as a general condition,
and write the outcome as something seen, never as an internal intention.

## Tasks

Tasks are executed by a lower-tier agent that does no architectural thinking, so
write each to that standard.

- Keep each task small and single-purpose: one concrete change, and split a
  task that hides two.
- Make each task independently executable, and order the list so working from
  top to bottom succeeds.
- Name the concrete file or location each task changes, never an area such as
  somewhere in the command line code.
- Leave no decision to the executor. Every question of approach, interface, or
  trade-off is resolved in the implementation decisions and the requirements
  before the tasks are written. A task that would force a choice means the plan
  was not ready, so resolve the choice and rewrite the task as a mechanical
  instruction.
- Put the failing-test task before the implementation task that makes it pass,
  wherever the work has a testable surface. Documentation-only work and other
  work with nothing to observe at run time is exempt, and no test is invented
  for it.
- Tie each task to the requirement ids it implements or verifies. The ids come
  from the requirements declared in this change alone, and a task covering the
  whole change, such as a final verification step, says so instead of naming
  ids.

## Placeholders

The readiness gate scans the whole plan, outside its own insufficiency section,
for placeholder markers: the words TBD, TODO, FIXME, and XXX, the two-word
phrase the gate matches for an unresolved question, and a bare run of question
marks. Write every part in settled prose that carries none of them. When
recording a consultation, paraphrase it into the decision, the options, and the
answer, and never paste a transcript that still carries a marker. A decision
that cannot yet be settled is resolved before the plan is written, not marked
open.

## Size

Keep each document lean. The plan and every single delta spec should stay under
about 2,000 tokens, roughly 8,000 characters, and the linter warns above that
budget. A document that pushes the limit is a signal to decompose the change,
not to write a monolith.
