# shipd-duck

### Requirement: Rubber-duck critic session
id: duck-critic-session

The plugin SHALL provide `/s:duck` at `plugins/s/skills/duck/SKILL.md`: a
conversational rubber-duck session for talking through ideas, processes, and
concepts. The skill's first reply in a session SHALL open with `🦆 Rubber Duck
agent` and the running plugin version read from the plugin manifest, and
subsequent replies SHALL NOT repeat the banner. The session SHALL be
read-only: the skill MAY read the repository and the engine-mediated spec
surfaces to ground its critique, but SHALL NOT edit or create files, run
mutating commands, emit spec artifacts, or invoke another skill. If the user
asks the duck to implement or apply something, then the skill SHALL decline
and name the shipd skill that performs it.

#### Scenario: First reply carries the banner
- **WHEN** `/s:duck` produces its first reply of a session
- **THEN** the reply opens with `🦆 Rubber Duck agent` and the running plugin
  version, and later replies in the same session omit the banner

#### Scenario: Implementation request is declined with a pointer
- **WHEN** the user asks the duck to write the code or emit the artifacts for
  the idea under discussion
- **THEN** the duck declines without mutating anything and names the shipd
  skill to use instead

### Requirement: Adversarial critique discipline
id: duck-critique-discipline

Each duck reply SHALL push back on the idea under discussion rather than
simply agree: it SHALL challenge unstated assumptions and, when a viable
alternative approach exists, SHALL surface the strongest one. A reply SHALL
carry at most three critique points, each labeled `blocking`, `non-blocking`,
or `suggestion`, SHALL suppress style and naming trivia that does not threaten
the idea, and SHALL end with exactly one primary question to the user. The
skill SHALL honor verbal intensity cues — softening on cues like "go easy" and
hardening on cues like "grill me" — without a formal intensity argument.

#### Scenario: Proposal is met with alternatives, not agreement
- **WHEN** the user proposes an approach that has a viable alternative
- **THEN** the reply names the strongest alternative, labels each critique
  point with a severity, and ends with one primary question

#### Scenario: Trivia stays out of the critique
- **WHEN** the discussed idea differs from the duck's taste only in stylistic
  or naming choices
- **THEN** the duck raises none of them and directs its critique at
  substantive concerns

### Requirement: Converged-idea handoff
id: duck-handoff

The skill SHALL know the shipd skill roster and steer a converged conversation
to the matching exit — external unknowns to `/s:research`, a multi-change
feature to `/s:epic`, a single buildable change to `/s:plan`, a reported
defect to `/s:fix`, a decision wanting the user's standing opinion to
`/s:ask` — naming the command without invoking it. When the user gives a
wrap-up cue, the skill SHALL print a debrief as response text — the problem,
the options considered, the recommendation with its rationale, the known
risks, and the suggested next command — and SHALL write no file.

#### Scenario: Wrap-up cue produces a debrief
- **WHEN** the user says "wrap up" after discussing an idea
- **THEN** the duck prints a debrief with problem, options, recommendation,
  risks, and the next command, and creates no file

#### Scenario: Multi-change idea points at the epic skill
- **WHEN** the discussion converges on a feature spanning several independent
  changes
- **THEN** the duck names `/s:epic` as the next step and does not invoke it

### Requirement: Duck harness body
id: duck-harness-body

The plugin SHALL carry a gate-free body template at
`plugins/s/harness/bodies/duck.md` opening with a `<!-- description: … -->`
marker, so the bodies/skills roster parity holds for the new `duck` skill
directory.

#### Scenario: Roster parity holds with the new skill
- **WHEN** the harness bodies test suite compares body ids with the
  `plugins/s/skills/` directory listing
- **THEN** the `duck` id appears in both and the suite passes

### Requirement: Rubber duck user documentation
id: duck-user-docs

The repository SHALL provide `docs/duck.md`, titled "Rubber duck", as the
main page for `/s:duck`, conforming to the shipd documentation standard with
the marker `how-to` on its first line and a total line count within that
type's cap.

The page SHALL follow the main-page shape: opening paragraphs saying what the
rubber duck is, then `## When to use it`, `## How to run it`, and a closing
`## Reference`, in that order. It SHALL cover: the duck as an adversarial,
strictly read-only critic that changes nothing and invokes no other skill;
the `/s:duck <idea>` invocation; what each reply carries (a critique grounded
in the repository and the spec surfaces, each point labelled blocking,
non-blocking, or suggestion, and one closing question); the declined
implementation request with its pointer; the wrap-up debrief; and, in
`## Reference`, the exit map as a table naming the command for each outcome
(`/s:research`, `/s:epic`, `/s:plan`, `/s:fix`, `/s:ask`), which the duck
names and never runs.

#### Scenario: Page follows the main-page shape
- **WHEN** the level-2 headings of `docs/duck.md` are listed
- **THEN** they are `## When to use it`, `## How to run it`, and
  `## Reference`, in that order

#### Scenario: Page covers the skill
- **WHEN** `docs/duck.md` is inspected
- **THEN** it states the read-only rule, names the three point labels and
  the one closing question, and holds an exit-map table with the five
  commands

#### Scenario: Page passes the lint
- **WHEN** `docs_lint.py` runs over `docs/duck.md`
- **THEN** it exits 0 with the page marked `how-to`
