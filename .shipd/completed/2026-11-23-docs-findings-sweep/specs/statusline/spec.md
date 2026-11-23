## MODIFIED Requirements

### Requirement: Statusline and telemetry user documentation
id: statusline-telemetry-user-docs
base: aa94c163fc10

The repository SHALL provide `docs/statusline-and-telemetry.md`, titled
"Statusline and telemetry", as the main page for the `shipd statusline` verb,
the build report, and the `shipd metrics` verb. The page SHALL conform to the
shipd documentation standard with `<!-- doc-type: how-to -->` as its first
line and a total line count within the how-to cap.

The page SHALL follow the main-page shape: opening paragraphs saying what
the three surfaces show, then `## When to use it`, `## How to run it`, and a
closing `## Reference`, in that order. `## How to run it` SHALL hold the
level-3 headings `### Register the statusline`, `### Read the build report`,
and `### Read the delivery metrics`.

For the statusline the page SHALL state: the rendered line
`☕ <name> · <status> · <done>/<total> tasks`; that it reads the root's planned
changes plus one level of worktrees; that an `active` change owns the line;
the position bracket when more than one change is live; the
`☕ no active specs` line; that `shipd statusline install` writes the
`statusLine` entry into `~/.claude/settings.json`, keeps every other
setting, and takes effect in the next session; that bare `shipd statusline`
reports and changes nothing; and that `shipd statusline layout` shows or
sets the segments on each line.

For the build report the page SHALL state: that `/s:build` prints the report
at the end of a build; what the report holds (a summary line, the change and
its task counts, any merge warnings, and a table of per-model and total
elapsed time); and that each build writes one file under the configured `log_dir` and
appends one record to `builds.jsonl` in that same directory.

For the delivery metrics the page SHALL state what `shipd metrics` prints and
SHALL name the four subverbs `summary`, `record-flow`, `forecast`, and
`rollup` with one line each.

The `## Reference` section SHALL hold: a table of the statusline segments
`spec`, `directory`, and `context`; a table of the `shipd statusline` flags
`--settings`, `--config`, `--force`, `--show`, and `--hide`; and a table of
the report settings `logging_enabled`, `log_dir`, `number_format`, and
`parallelism` with the defaults `true`, `~/.shipd/builds`, `short`, and `3`.
The page SHALL link `customise.md` as the owner of the `statusline` and
`build` config keys and SHALL link `doctor.md`. It SHALL carry no mermaid
fence. Every command on the page SHALL be a `shipd` verb or a `/s:` skill;
the page SHALL name no engine script path.

#### Scenario: Page follows the main-page shape
- **WHEN** the level-2 headings of `docs/statusline-and-telemetry.md` are
  listed
- **THEN** they are `## When to use it`, `## How to run it`, and
  `## Reference`, in that order

#### Scenario: Page covers the statusline
- **WHEN** `docs/statusline-and-telemetry.md` is inspected
- **THEN** it shows the rendered line ending in `tasks`, names `shipd statusline install` and
  `shipd statusline layout`, and states that the bare verb changes nothing

#### Scenario: Page covers the build report and the metrics
- **WHEN** `docs/statusline-and-telemetry.md` is inspected
- **THEN** it names the parts of the build report, states that
  `builds.jsonl` sits in the configured `log_dir`, and names the four
  `shipd metrics` subverbs

#### Scenario: Reference tables carry the segments and the defaults
- **WHEN** the `## Reference` section is read
- **THEN** it names the three segments, the five flags, and the four report
  settings with the defaults `true`, `~/.shipd/builds`, `short`, and `3`

#### Scenario: Page passes the lint and its links resolve
- **WHEN** `docs_lint.py` runs over `docs/statusline-and-telemetry.md`
- **THEN** it exits 0 with the file marked `how-to` at 150 lines or fewer,
  the file names no `statusline.sh`, `build_report.py`, `metrics.py`, or
  `spec_status.py` path, and every relative link resolves
