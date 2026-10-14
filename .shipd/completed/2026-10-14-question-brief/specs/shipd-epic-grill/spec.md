## MODIFIED Requirements

### Requirement: One final question round
id: epic-grill-final-round
base: 3e15cd8dd303
Dropped: Five decisions take two dialogs

The skill SHALL build its question agenda from the `PLANNER` entries read
from disk across all selected members, merging entries that pose the same
decision. If the agenda is empty, then the skill SHALL ask nothing. Otherwise
the skill SHALL ask the whole agenda only after the consistency pass, as one
numbered typed round. Each question SHALL open with the brief that
`plugins/s/skills/document/references/question-brief.md` defines, SHALL name
its member(s) and `Q<n>` references, and SHALL list the adopted default as
the first option marked recommended. The skill SHALL NOT issue an
AskUserQuestion for the agenda. For each answered entry that carries a
`**Queued:**` slug, the skill SHALL classify the answer against the capture
rubric and answer or discard the queued block, as `/s:plan` does.

#### Scenario: Five decisions take one typed round
- **WHEN** the agenda holds five decisions
- **THEN** the skill asks all five in one numbered typed round, each with
  its brief, and no question round before the consistency pass

#### Scenario: Empty agenda asks nothing
- **WHEN** no member holds a `PLANNER` entry
- **THEN** the skill asks no question round
