<!-- doc-type: reference -->

# Plan authoring rules

This file is the one source of the rules for writing a plan's prose. It says what each part of a change holds and how to phrase it. Engines load it alongside their own emission mechanics. It carries rules only, with no commands, no paths, and no interaction, so any engine can follow it. Each part below has a stable `##` heading, because external loaders read the file by heading.

## Motivation

State the reason for the change in at most two sentences. Name who cannot proceed and what they cannot do.

Ground the reason in the request and the repository context, never in a guess. When you cannot state the reason precisely from what you have, find out before you write it. You may cite repository state as evidence for the reason. It is never the reason itself. A file that is a placeholder, absent, or holding particular content is not a motivation on its own.

## Non-goals

List what is explicitly out of scope, with at least one exclusion. A plan has no Goals section anywhere. The idea already states the goals, and stating them twice invites drift. Put the approaches you considered and dropped with the decision that rejected them. Do not put them in a goals list.

## Implementation decisions

Record the binding decisions an executor must not re-make, one at a time, in the style of an architecture decision record. For each decision, give the choice and a short rationale. Add the rejected alternative where it clarifies why. An executor should never have to reconstruct why you decided.

Name the files and components the change touches. Name the interfaces and data shapes it introduces or alters.

Record the risks and trade-offs: what could go wrong, and how the plan guards against it. A trivial change may keep this part brief. It still records why the approach is sound.

## Requirements

Each requirement states one behaviour with a SHALL or MUST statement. Each carries an id that is unique within the change.

Phrase the statement in one of the five EARS shapes:

- the plain ubiquitous form
- event-driven ("when a trigger occurs")
- state-driven ("while a state holds")
- unwanted-behaviour ("if a condition arises, then")
- optional-feature ("where a feature is present")

EARS is authoring guidance.

A statement needs only the SHALL or MUST token, never a matching template.

## Scenarios

Give every requirement at least one scenario. A scenario holds one concrete WHEN that names the exact trigger. It may add a GIVEN for the starting state. It ends with an observable THEN that a reader could check by running or inspecting the result. Write the trigger as a specific action or input, never a general condition. Write the outcome as something you can see, never an internal intention.

## Tasks

A lower-tier agent executes the tasks and does no architectural thinking. Write each task to that standard.

- Keep each task small and single-purpose. Make one concrete change, and split a task that hides two.
- Make each task independently executable. Order the list so working from top to bottom succeeds.
- Name the concrete file or location each task changes, never a vague area such as somewhere in the command line code.
- Cite each repository path in backticks, as the full path from the repository root. Write the word Create or Add directly before a path the task creates, with nothing between them. Never remove the backticks from a repository path to pass the gate, because later drift and overlap checks read them.
- Leave no decision to the executor. Settle every question of approach, interface, or trade-off in the decisions and requirements first. A task that forces a choice means the plan was not ready. Resolve the choice and rewrite the task as a mechanical instruction.
- Put the failing-test task before the implementation task that makes it pass, wherever the work has a testable surface. Documentation-only work, and other work with nothing to observe, is exempt. Do not invent a test for it.
- Tie each task to the requirement ids it implements or verifies. The ids come only from this change's own requirements. A task that covers the whole change says so instead of naming ids.

## Placeholders

The readiness gate scans the whole plan for placeholder markers, outside its own insufficiency section.

The markers are the words TBD, TODO, FIXME, and XXX. They also include three question marks in a row, `???`, and the two-word phrase the gate matches for an unresolved question. Write every part in settled prose that carries none of them. When you record a consultation, paraphrase it into the decision, the options, and the answer. Never paste a transcript that still carries a marker.

Settle a decision before you write the plan. Do not mark it open.

## Size

Keep each document lean. The plan and every single delta spec should stay under about 2,000 tokens, roughly 8,000 characters. The linter warns above that budget. A document that pushes the limit is a signal to decompose the change. Do not write a monolith.
