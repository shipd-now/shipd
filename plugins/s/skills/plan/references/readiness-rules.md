<!-- doc-type: reference -->

# Plan readiness rules

This file is the one source of the rules that decide whether a plan is ready to write. It holds the four readiness items with their citation standards, the gate, the attestation a plan carries, the self-review pass, and the stop rule. Engines load it alongside their own mechanics. It carries rules only, with no commands, no paths, and no interaction, so any engine can follow it. Each part below has a stable `##` heading, because external loaders read the file by heading.

## Problem and motivation

Readiness item 1. You can state, in one or two sentences, what problem the change solves. You can also state its motivation, held to the bar in `authoring.md`, `## Motivation`. When you cannot ground the motivation precisely in the request and the repository, treat it as un-inferrable and resolve it before you write the plan. Never invent a reason.

Citation standard. Cite the file and line, the requirement id, or the capability name that grounds the motivation. Do not restate the motivation as its own evidence.

## Scope and non-goals

Readiness item 2. You know what is in scope and what is explicitly out of scope. Draw the edges so the change does not sprawl.

Citation standard. Cite the capability name or the file and line that fixes the boundary you drew.

## Affected capabilities and files

Readiness item 3. You know which capabilities in the master spec library the change adds or modifies. You also know the concrete files or areas of code the tasks will name. "Somewhere in the codebase" is not an answer.

Citation standard. Cite each affected capability by name and each affected file by file and line. A vague area is not a citation and leaves the item unmet.

Runnable premises are evidence under this item, not a fifth item. The rule applies when the plan asserts how an existing command, script, or flag behaves, and a task or requirement depends on that assertion.

Observe the behaviour: run the command and record the invocation and its output or exit code. Citing the implementation never satisfies this on its own.

Only where your engine cannot run commands while planning, cite the implementing lines and state that the premise is unrun. Then make the first task that depends on it run the command.

Two exemptions apply. An assertion about behaviour this change will create needs no run, because there is nothing to run yet. An assertion that no task or requirement depends on needs no run, because it shapes nothing the plan hands the executor.

## No open task-shaping decision

Readiness item 4. Resolve every decision that would alter which tasks you write, by investigation or by a question. The test is whether resolving a decision one way instead of another would add, remove, or reshape a task. If it would, the decision is still open. When you are unsure whether a decision matters, apply that test.

Citation standard. Name each task-shaping decision and what settled it: the code, a recorded preference, the oracle, or a person. Where none remain, say so explicitly. Claiming that nothing is open is not enough once any decision existed to settle. Name the decisions you weighed.

## The gate

The plan is ready only when you meet all four items. When you meet all four, write the plan. When any item stays unmet, investigate first, then ask. Never write a speculative plan to paper over an unmet item.

## Attestation

A ready plan carries a `## Readiness attestation` section. It holds four `###` subsections, in the order of the four items above. Name each exactly as its item: Problem and motivation, Scope and non-goals, Affected capabilities and files, No open task-shaping decision.

Each subsection opens with a plain statement, in one or two sentences, of how you meet the item. Then comes a line reading `Evidence:` and a dash list of citations to the standards above. The statement comes first, so a reader who wants the summary stops there and a reader who wants the proof keeps going.

An item whose subsection carries no evidence is unmet, like an item left unaddressed. Return to investigating, then ask. Do not write the plan until every item carries evidence.

Write the section in settled prose, per `authoring.md`, `## Placeholders`.

## Self-review

Before you hand the plan over, re-read it. Check for placeholder markers, for contradictions between its parts, and for decisions left to the executor. Fix what you find.

Then check the readiness attestation item by item. Each of the four subsections must carry evidence. An item without evidence is unmet: investigate again, then ask. Do not hand the plan over until the item carries evidence. A linter checks structure. This pass checks sense.

## Stop when ready

The moment the checklist holds, stop investigating and write the plan. Open no new threads of exploration once you clear the bar.
