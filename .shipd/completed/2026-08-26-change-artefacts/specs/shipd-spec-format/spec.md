## MODIFIED Requirements

### Requirement: Per-change artifact layout
id: per-change-artifact-layout
base: c67c8ef6749e

A change SHALL live at `<content-dir>/planned/<change>/` (default
`.shipd/planned/<change>/`) and SHALL always contain the lean artifact set: a
single `plan.md` holding the change's idea and implementation decisions, a
delta spec at `specs/<capability>/spec.md` for each affected capability, and
`tasks.md` as a separate executor-owned checklist. This artifact set SHALL
be produced for every change regardless of size.

A change MAY additionally carry an optional `artefacts/` directory holding the
standalone outputs of planning — a policy document, a block of verbatim text,
any content that must be preserved exactly rather than paraphrased into the
lean artifact set. Where the directory is present, every file inside it SHALL
be referenced by at least one of `plan.md`, `tasks.md`, or a delta spec, and
references SHALL use the change-relative path `artefacts/<file>` so they stay
correct after the change is archived. The directory SHALL travel with the
change through installation and through the merge's archive to
`<content-dir>/completed/<date>-<change>/artefacts/`.

#### Scenario: A change carries the lean artifact set
- **WHEN** a change `dark-mode-toggle` is authored under the default
  configuration
- **THEN** `.shipd/planned/dark-mode-toggle/` contains `plan.md`, at least one
  `specs/<capability>/spec.md`, and `tasks.md`

#### Scenario: Tasks stay out of the plan document
- **WHEN** an executor marks tasks done during a build
- **THEN** only `tasks.md` checkboxes change and `plan.md` is not rewritten

#### Scenario: A staged artefacts directory installs with the change
- **WHEN** a staging directory carrying `artefacts/policy.md`, referenced from
  `plan.md`, is installed with `spec_emit.py change`
- **THEN** the install succeeds and
  `.shipd/planned/<change>/artefacts/policy.md` holds the staged content

#### Scenario: Artefacts survive the archive
- **WHEN** a change carrying an `artefacts/` directory is merged and archived
- **THEN** `.shipd/completed/<date>-<change>/artefacts/` holds the same files
