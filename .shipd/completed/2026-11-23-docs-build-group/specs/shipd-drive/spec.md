## ADDED Requirements

### Requirement: Drive and demo user documentation
id: drive-demo-user-docs

The repository SHALL provide `docs/drive-and-demo.md`, a how-to page titled
"Drive a browser and record a demo" that is the main page for `/s:drive` and
`/s:demo`. The page SHALL follow the main-page shape: the opening under the title saying what the feature is, then the exact
level-2 headings `## When to use it`, `## How to run it`, and `## Reference`,
in that order. For `/s:drive`
it SHALL cover target resolution, the `doctor` preflight, login with the
`--manual` path, probing the live DOM before authoring a selector, waiting on
named completion signals, the `PASS`/`FAIL` verdict, and `handoff` with
`resume`. For `/s:demo` it SHALL cover the choice between a browser and a
terminal subject, capture with `record` or `tape`, and post-processing with
`post`. Its Reference section SHALL hold a table of `drive.py` verbs that
names no verb absent from `drive.py --help`. The page SHALL carry no diagram,
and every relative link in it SHALL resolve. The page SHALL conform to the
shipd documentation standard: `<!-- doc-type: how-to -->` as its first line
and a total line count within the how-to cap.

#### Scenario: Page follows the main-page shape
- **WHEN** `docs/drive-and-demo.md` is inspected
- **THEN** its level-2 headings are exactly `## When to use it`,
  `## How to run it`, and `## Reference`, in that order

#### Scenario: Page covers driving and the verdict
- **WHEN** `docs/drive-and-demo.md` is inspected
- **THEN** it names targets, `doctor`, `login --manual`, `probe`, the
  `PASS`/`FAIL` verdict, `handoff`, and `resume`

#### Scenario: Page covers both demo mediums
- **WHEN** `docs/drive-and-demo.md` is inspected
- **THEN** it names the browser path through `record`, the terminal path
  through `tape`, and `post` as the shared last step

#### Scenario: Verb table matches the CLI
- **WHEN** each verb in the page's Reference table is compared with the
  output of `drive.py --help`
- **THEN** every verb in the table appears in that output

#### Scenario: Page carries its marker and fits its cap
- **WHEN** `docs_lint.py` runs over `docs/drive-and-demo.md`
- **THEN** it exits 0 with the file marked `how-to` at 150 lines or fewer
