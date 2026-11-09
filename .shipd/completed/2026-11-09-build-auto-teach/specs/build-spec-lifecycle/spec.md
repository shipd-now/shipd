## ADDED Requirements

### Requirement: Post-verify teacher
id: post-verify-teach

When a build stamps a change `verified`, the resolved pipeline's `build` entry
does not declare `teach` false, and `spec_status.py wiki-show --json` run from
the change's worktree reports `present` true and `fallback` false, build SHALL
spawn one `s:teacher` sub-agent on the execution tier with description
`teacher · <change>` and a spawn message carrying only the change name and the
absolute path of the plugin's `skills/build/scripts/` directory, and SHALL
continue into the merge phase without waiting on it. Before printing the
end-of-build report, build SHALL collect the teacher's report and render it as
the first Observations line, prefixed `wiki:`. Where the store is absent or the
repo-local fallback, or the entry declares `teach` false, build SHALL spawn no
teacher and SHALL render `wiki: skipped — <reason>`. If the teacher fails or
returns no report, then build SHALL say so on that line and SHALL neither fail
the build nor delay the merge. A driven build SHALL await the teacher before
its final report text, and the autopilot's build addenda SHALL instruct the
driven build to skip the teacher when the entry declares `teach` false.

#### Scenario: Teacher spawns after verified
- **GIVEN** a worktree whose `wiki-show --json` reports a present workspace
  store that is not the fallback, and a bare `build` entry
- **WHEN** the build stamps the change `verified`
- **THEN** an `s:teacher` sub-agent is spawned with description
  `teacher · <change>` and a spawn message naming only the change and the
  scripts directory, and the merge phase proceeds without waiting

#### Scenario: Fallback store spawns no teacher
- **GIVEN** `wiki-show --json` reporting `fallback` true
- **WHEN** the build stamps the change `verified`
- **THEN** no teacher is spawned and the report's Observations open with
  `wiki: skipped — no workspace store`

#### Scenario: Pipeline opt-out spawns no teacher
- **GIVEN** a resolved `build` entry declaring `teach` false
- **WHEN** the build stamps the change `verified`
- **THEN** no teacher is spawned and the report's Observations open with
  `wiki: skipped — teach disabled by pipeline`

#### Scenario: Teacher outcome is an observation
- **WHEN** the teacher reports `taught — [[slug]] (new): …` and
  `drained — q-foo`
- **THEN** the report's first Observations line reads
  `wiki: taught [[slug]]; drained q-foo`, and the report structure is
  otherwise unchanged

#### Scenario: Teacher failure never blocks the build
- **WHEN** the teacher reports `failed — <reason>` or returns nothing
- **THEN** the PR ships as usual and the Observations line names the failure

#### Scenario: Driven build awaits the teacher
- **WHEN** an autopilot drive runs the build as a stage sub-agent
- **THEN** the build collects the teacher's report before ending its turn
  with the report text
