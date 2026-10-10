<!-- doc-type: how-to -->

# Episode 4: Epics and `/s:epic-grill`

## Introduction

An assistant that agrees with every design lets a weak plan through. This episode shows the opposite: an epic decomposes one feature into member changes over shared decisions, and `/s:epic-grill` pressure-tests the plans before you build. It plans every member, asks you one agenda of hard questions, and gates each member. The episode is for developers who plan features that span several changes.

## At a glance

| Item | Detail |
|---|---|
| Roadmap group | Spec authoring and pressure testing |
| Runtime | 5 minutes |
| Prerequisites | A PRD for the feature, and the core loop from episodes 1 and 3 |
| Commands shown | `/s:epic`, `/s:epic-grill`, `/s:autopilot` |

## Script

### 0:00–1:00 The yes-man assistant

**On screen:** A chat shows an assistant answering "Add retries to the payments client" with "Great idea, here is the code." A red banner reads "No question asked."

**Narration:** An assistant that agrees with any design is a yes-man. It never asks about retry logic, a cache race, or a telemetry gap, so those surface in review or in production. Planning a large feature needs something that pushes back before the build. That is what an epic and `/s:epic-grill` add.

### 1:00–2:30 `/s:epic` decomposes the feature

**On screen:** The PRD for the feature sits on the left. On the right the presenter runs `/s:epic payments-retry`. The epic opens with its Decisions, its Design, and a `## Changes` table of three stub rows. Each row has a complexity rating and depends on the one before.

**Narration:** A PRD comes first and states the product need. `/s:epic` investigates your codebase, asks one batched round of questions, and records the shared decisions and the design. It decomposes the one feature into three dependent member changes and lists each as a stub row. It creates no member change itself.

### 2:30–4:00 `/s:epic-grill` asks one agenda

**On screen:** The presenter types `/s:epic-grill payments-retry`. The terminal prints the planning order, then a dialog lists three questions: retry logic, a cache-invalidation race, and a telemetry gap. Each names its member and carries a recommended first option.

**Narration:** The skill orders the unplanned members by dependency. It plans each through `/s:plan` and defers its human questions. It checks the plans against each other and fixes a mismatched flag name silently. A true conflict joins the agenda. Then it asks the whole agenda in one round, with the recommended default first.

### 4:00–5:00 Answers rewrite the plans

**On screen:** The retry answer changes a line in the second member's plan. The terminal marks each member execution-ready. The summary ends with `/s:autopilot payments-retry` on its own line.

**Narration:** Your answers rewrite the affected plans. The skill gates every member only after that round, so an interrupted run leaves every plan at draft. It never builds. It ends with a short summary per member and names `/s:autopilot` as the command that delivers the epic.

## Takeaways

- An epic decomposes one feature into dependent member changes over shared decisions; a PRD precedes it.
- `/s:epic-grill` plans every unplanned member, cross-checks the plans, and asks one agenda instead of agreeing with everything.
- Answers rewrite the affected plans, every member passes the gate, and `/s:autopilot` delivers; the skill never builds.

## Next

Episode 5 covers the answerer that spares you most questions: [The oracle and the supersession gate](05-oracle-and-supersession-gate.md).

## Sources

- [Spec for the epic skill](../../../.shipd/verified/shipd-epic/spec.md)
- [Spec for the epic-grill skill](../../../.shipd/verified/shipd-epic-grill/spec.md)
- [PRDs](../../prd.md)
