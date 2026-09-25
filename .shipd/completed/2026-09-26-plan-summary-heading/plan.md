# plan-summary-heading
Status: verified

## Idea

Close every plan hand-off with a `## Summary` heading and one plain sentence saying what the change does and why.

### Motivation

The user asked that every planning session end the way the last one did on request: a heading named "Summary" and a single sentence such as "We're making X, so Y". Today the hand-off runs several paragraphs with no such line, so the user has to ask for the one-sentence form separately.

### Details

- The plan skill's Ending section gains a step between the motivation-led body and the build pointer: print `## Summary`, then one sentence stating what the change does and why, naming no file.
- The enrichment re-gate paragraph points at the same closing, so both hand-offs match.
- The harness plan body's hand-off step says the same, so generated commands for other tools follow it.
- The `standalone-invocation` requirement of `shipd-plan` records the heading, the one-sentence form, and its position before the build pointer.

Affected capabilities: `shipd-plan` (modified). Impact: `plugins/s/skills/plan/SKILL.md`, `plugins/s/harness/bodies/plan.md`, `plugins/s/.claude-plugin/plugin.json`. No engine code, no new dependencies.

### Non-goals

- No change to the build skill's inline planning, which continues into implementation and never hands off.
- No change to the motivation-led body, the build pointer's colon rule, or the `/s:build` line.
- No new eval case: the plan evals grade emitted artifacts, not the closing text.
- No change to the depth path's shared-understanding summary, which is a mid-flow confirmation, not the hand-off.

## Implementation

- **One new step in the Ending section.** In `plugins/s/skills/plan/SKILL.md`, the Ending section's numbered list becomes five steps: 1 promote through the gate, 2 summarize why-first (unchanged), 3 **Close with a Summary heading** (new), 4 point at build (renumbered from 3, its fenced example extended to show the heading and sentence above the colon sentence), 5 stop (renumbered from 4). Step 3 reads: print a level-2 heading `## Summary`, then exactly one plain-language sentence stating what the change does and why, in the shape "We're <doing X>, so <Y is unblocked>", naming no file or artifact. Rejected: folding the sentence into step 2, because the heading must sit last, directly above the build pointer, where a reader scanning the terminal finds it.
- **The enrichment pointer names the closing too.** The enrichment re-gate paragraph that says "hand off with the motivation-led summary" adds "closing with the `## Summary` heading and its one sentence" so an enrichment hand-off matches a fresh one.
- **The harness body mirrors the skill in one sentence.** In `plugins/s/harness/bodies/plan.md`, step 9 adds: "then print a `## Summary` heading with one plain sentence saying what the change does and why" before "and end with `/s:build` alone on its own line". The body stays a router; the long form stays in the skill.
- **Version.** Bump `plugins/s/.claude-plugin/plugin.json` by one patch level over what `main` carries when the task runs, because the plugin cache snapshot is keyed by version.

Risk: a summary sentence that restates the motivation paragraph word for word. Guard: the step names the "We're X, so Y" shape and the no-file rule, which forces a compression rather than a repeat.

## Readiness attestation

### Problem and motivation

The user wants every plan hand-off to close with a "Summary" heading and a one-sentence statement, and the skill requires none today.

Evidence:

- The request: "when we plan, always end with a summary like that, with a heading 'Summary'", where "that" is the one-sentence answer given on request in the same session.
- Capability `shipd-plan`, requirement `standalone-invocation`: the hand-off leads with Motivation and closes with the build pointer, with no compressed summary named.
- `plugins/s/skills/plan/SKILL.md:791-808`: steps 2 and 3 of the Ending section carry no heading and no one-sentence form.

### Scope and non-goals

The change edits the skill's Ending section, its enrichment pointer, the harness body's hand-off step, and one requirement; the build skill, evals, and engine code stay untouched.

Evidence:

- In scope: `plugins/s/skills/plan/SKILL.md:193` (enrichment pointer), `:766-811` (Ending section), `plugins/s/harness/bodies/plan.md:89-91` (step 9).
- Out of scope: `evals/cases/plan-*` hold only `prompt.md` and `fixture/`, grading artifacts; `plugins/s/skills/build/tests/test_harness_generate.py` renders bodies through the same renderer on both sides and asserts no hand-off wording.

### Affected capabilities and files

One capability and three files are affected, because the hand-off is defined in the skill and restated once in the harness body.

Evidence:

- Capability `shipd-plan`: requirement `standalone-invocation` (base f3cf4235738d, from `spec_status.py base-hash`).
- Files: `plugins/s/skills/plan/SKILL.md`, `plugins/s/harness/bodies/plan.md`, `plugins/s/.claude-plugin/plugin.json:4`.
- Runnable premise: `grep -rn -i "motivation-led|hand-off summary" plugins/s README.md docs` excluding the plan skill returned no line, so no other surface restates the hand-off wording.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- Placement after the motivation-led body and before the build pointer: settled by the request, which asks the session to "end with" the summary, and by `standalone-invocation`, which fixes `/s:build` as the last line.
- Heading level `##`: settled by the request naming a heading and by the terminal rendering of the existing hand-off.
- One sentence in the "We're X, so Y" shape, naming no file: settled by the request's "like that", pointing at the one-sentence answer given in this session.
- Applying to enrichment hand-offs too: settled by the request's "always".
