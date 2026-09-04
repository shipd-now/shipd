## ADDED Requirements

### Requirement: Engine-mediated epic read
id: explain-epic-read

When `/s:explain` is invoked with an epic slug that resolves, the skill SHALL
read the epic exclusively through the engine's mediated verbs —
`spec_status.py cat epic <slug>` for the artifact and
`spec_status.py epic-show <slug>` for live delivery state — and SHALL remain
strictly read-only: it writes no file, emits no artifact, and runs no mutating
engine verb.

#### Scenario: Known epic is read through both verbs
- **WHEN** `/s:explain personal-memory` is invoked in a repo hosting that epic
- **THEN** the skill runs `cat epic personal-memory` and
  `epic-show personal-memory`, and produces its explanation from those two
  outputs, without opening any spec-tree path directly

#### Scenario: The session mutates nothing
- **WHEN** an `/s:explain` invocation completes
- **THEN** no file has been created or edited and no status-changing engine
  verb has run

### Requirement: Bounded response-text explanation
id: explain-output-budget

The skill SHALL print its explanation as response text only, and the prose
SHALL stay under 100 lines, with fenced diagram blocks excluded from that
count. The explanation SHALL cover the epic's intent (introduction and
decisions), how its members compose (design and member table), and its current
delivery state (lanes and shipped progress from `epic-show`).

#### Scenario: Explanation is short and complete
- **WHEN** the skill explains an epic
- **THEN** the response covers intent, member composition, and current
  delivery state in fewer than 100 prose lines, and no explanation file is
  written

#### Scenario: A small epic gets a proportionally short explanation
- **WHEN** the epic has one or two members and a short introduction
- **THEN** the explanation is far shorter than the ceiling — the 100 lines are
  a cap, not a target

### Requirement: Diagrams only where they carry structure
id: explain-diagram-policy

Where the epic's structure — member dependency order, a pipeline, or hand-offs
between actors — is conveyed faster by a picture than by prose, the skill SHALL
include a diagram as either swimlane-style ASCII or a mermaid block; otherwise
it SHALL include no diagram.

#### Scenario: A multi-member dependency chain earns a diagram
- **WHEN** the epic's design orders several members along dependency or
  pipeline seams
- **THEN** the explanation includes one swimlane-style ASCII or mermaid
  diagram of that structure

#### Scenario: A simple epic gets prose only
- **WHEN** the epic's structure is a flat list with no ordering or hand-offs
  worth picturing
- **THEN** the explanation contains no diagram

### Requirement: Missing or unknown epic lists the roster and stops
id: explain-missing-epic

If `/s:explain` is invoked with no slug, or with a slug the engine cannot
resolve (`cat epic` exits non-zero), then the skill SHALL report the engine's
error (when one was produced), list the available epic slugs — the child
directory names of the resolved content directory's `epics/` directory, with
the content directory taken from `spec_status.py config-show` — and stop
without explaining anything.

#### Scenario: Unknown slug reports and lists
- **WHEN** `/s:explain no-such-epic` is invoked
- **THEN** the skill reports the engine's `epic 'no-such-epic' not found`
  error, prints the available epic slugs, and stops

#### Scenario: No argument lists the roster
- **WHEN** `/s:explain` is invoked with no argument
- **THEN** the skill prints the available epic slugs, asks the user to pick
  one, and stops
