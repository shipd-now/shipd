## ADDED Requirements

### Requirement: Demo skill flow
id: demo-skill-flow

A `/s:demo` skill SHALL produce a branded demo video, selecting its capture
medium from the request: a browser demo through the drive CLI's `record` verb
(drive-recording), a terminal demo through its `tape` verb (drive-tape).
Both media SHALL converge on the same `post` verb (drive-postprocess,
drive-brand-frames), so every demo carries the same title card, fast-forward
treatment, and badge whatever captured it.

The skill SHALL announce the running plugin version in its first
user-visible status sentence. The skill SHALL run the drive CLI's `doctor`
preflight before capturing and, where the tool its chosen medium needs is
missing, SHALL report the remedy and stop rather than attempting the
capture. Where the request names no medium and the subject is ambiguous, the
skill SHALL end its turn as plain text — a numbered list and a typed reply —
and SHALL NOT issue an interactive question tool, matching the drive skill's
own dialog-free contract.

The skill SHALL keep `record a demo` among its trigger phrases, the phrase
the drive skill surrenders to it, so the existing vocabulary still resolves.
The skill SHALL NOT itself drive a browser, resolve a target, or write an
action module's selectors without probing — it delegates capture to the drive
CLI and owns only the routing, the medium choice, and the report.

#### Scenario: A browser subject routes to record
- **WHEN** the request asks for a demo of a web application
- **THEN** the skill captures through the drive CLI's `record` verb and
  post-processes the result through `post`

#### Scenario: A terminal subject routes to tape
- **WHEN** the request asks for a demo of a command-line tool
- **THEN** the skill captures through the drive CLI's `tape` verb and
  post-processes the result through `post`

#### Scenario: A missing medium tool stops before capture
- **GIVEN** a terminal demo request on a machine without `vhs`
- **WHEN** the skill runs its preflight
- **THEN** it reports the `brew install vhs` remedy and stops, capturing
  nothing

#### Scenario: An ambiguous medium is asked as plain text
- **WHEN** the request names no medium and the subject could be either
- **THEN** the skill ends its turn with a numbered plain-text list and no
  interactive question tool

#### Scenario: The surrendered trigger resolves here
- **WHEN** the skill's declared trigger phrases are inspected
- **THEN** they carry `record a demo`

### Requirement: Demo skill registration
id: demo-skill-registration

The repository SHALL ship the skill as `plugins/s/skills/demo/SKILL.md` with
a matching command body at `plugins/s/harness/bodies/demo.md`, preserving the
one-to-one mapping between skill directories and command bodies that the
engine test suite enforces. The drive skill's own declared trigger phrases
SHALL NOT carry `record a demo`, so exactly one skill claims it.

#### Scenario: The skill and its body stay paired
- **WHEN** the harness bodies guard runs over the repository
- **THEN** `plugins/s/skills/demo/` and `plugins/s/harness/bodies/demo.md`
  are both present and the guard exits clean

#### Scenario: Only one skill claims the demo trigger
- **WHEN** every skill's declared trigger phrases are inspected
- **THEN** `record a demo` appears in the demo skill's and in no other's
