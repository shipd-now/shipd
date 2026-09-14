# semantic-review

## ADDED Requirements

### Requirement: Static analysis subcommand
id: review-lint-subcommand

The system SHALL provide `semdiff lint <base> [<head>]`, resolving its
endpoints exactly as `diff` and `files` do, and emitting a single JSON object
carrying the resolved `base`, `head` and `mode`, a `linters` list, and a
`summary`.

The subcommand SHALL detect a linter when its conventional marker file is
present **and** its binary resolves, checking `node_modules/.bin/<tool>` from
the repository root before `PATH`. It SHALL detect `ruff` (`ruff.toml`,
`.ruff.toml`, or a `[tool.ruff]` section in `pyproject.toml`), `flake8`
(`.flake8`, or a `[flake8]` section in `setup.cfg` or `tox.ini`), `pylint`
(`.pylintrc`, or a `[tool.pylint]` section in `pyproject.toml`) and `eslint`
(any `eslint.config.*` or `.eslintrc*`). A marker present with no resolvable
binary SHALL be reported with state `unavailable` rather than omitted.

The subcommand SHALL execute only an argv it constructs itself, requesting each
linter's machine-readable format, and SHALL run each linter over **only** the
changed paths whose extension that linter owns — `.py` for the three Python
linters, and the JavaScript and TypeScript extensions for `eslint`. A detected
linter owning no changed path SHALL be reported with state `skipped` and SHALL
NOT run. No linter SHALL receive a fix or write flag.

The subcommand SHALL NOT execute a repository-defined script by default. A
`lint` script declared in `package.json` SHALL be reported with state
`not-run`, and SHALL be executed only where the resolved configuration's `lint`
key declares `run_scripts` true.

Each `linters` entry SHALL carry the linter's `name`, its `state` (one of
`ran`, `unavailable`, `skipped`, `not-run`, `failed`), the `argv` executed when
one was, and its `findings`, each with `path`, `line`, `rule`, `message` and
`severity`. Each linter SHALL run under a per-linter timeout. A timeout, a
crash, or output that does not parse SHALL set state `failed` with a captured
stderr excerpt, and the subcommand SHALL still exit `0` — a failing linter
never blocks a review.

#### Scenario: A detected linter runs over changed paths only
- **WHEN** `semdiff lint` runs in a repository carrying a `ruff.toml`, with
  `ruff` resolvable and two changed Python files among several unchanged ones
- **THEN** the entry for `ruff` has state `ran`, its `argv` names only the two
  changed paths, and its findings carry `path`, `line`, `rule`, `message` and
  `severity`

#### Scenario: A marker without a binary is reported, not dropped
- **WHEN** a repository carries a `.flake8` file and `flake8` resolves on
  neither `node_modules/.bin` nor `PATH`
- **THEN** the `flake8` entry is present with state `unavailable`, and the exit
  code is `0`

#### Scenario: A detected linter owning no changed path is skipped
- **WHEN** `eslint` is detected and the diff changes only Python files
- **THEN** the `eslint` entry has state `skipped` and no `argv` is executed

#### Scenario: A repo script is not run without the opt-in
- **WHEN** `package.json` declares a `lint` script and the resolved
  configuration does not declare `lint.run_scripts` true
- **THEN** the entry has state `not-run` and no script is executed

#### Scenario: The opt-in permits the script
- **WHEN** the resolved configuration declares `lint.run_scripts` true and
  `package.json` declares a `lint` script
- **THEN** the script is executed and its entry reports the state of that run

#### Scenario: A failing linter degrades rather than blocks
- **WHEN** a detected linter exceeds its timeout or emits output that does not
  parse
- **THEN** its entry has state `failed` carrying a stderr excerpt, and
  `semdiff lint` exits `0`

#### Scenario: The project's own install wins
- **WHEN** both `node_modules/.bin/eslint` and a `PATH` `eslint` resolve
- **THEN** the executed `argv` names the `node_modules/.bin` binary

### Requirement: Linter output in the review
id: review-lint-step

The `/s:review` skill SHALL carry an inline workflow step directing the
reviewer to run `semdiff lint` over the same endpoints as the diff and to read
its output, with the detailed guidance in
`plugins/s/skills/review/references/linters.md` named by its
`${CLAUDE_PLUGIN_ROOT}` path beside its load condition. The inline step SHALL
state that a linter finding is corroboration the reviewer weighs, reported only
where it bears on the change, and never promoted to a review finding
automatically. `SKILL.md` SHALL stay under 300 lines.

#### Scenario: The step is inline and the detail is referenced
- **WHEN** `plugins/s/skills/review/SKILL.md` is inspected
- **THEN** it carries the `semdiff lint` step in the workflow itself and names
  `linters.md` in the References table with its load condition

#### Scenario: A linter hit is not automatically a finding
- **WHEN** the skill's linter step is read
- **THEN** it states that a linter finding is weighed as corroboration and
  reported only where it bears on the change

#### Scenario: The skill body still fits the ceiling
- **WHEN** `plugins/s/skills/review/SKILL.md` is measured
- **THEN** it is under 300 lines
