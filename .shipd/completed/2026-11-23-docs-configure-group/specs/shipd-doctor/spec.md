## ADDED Requirements

### Requirement: Doctor user documentation
id: doctor-user-docs

The repository SHALL provide `docs/doctor.md`, titled "Doctor", as the main
page for the `shipd doctor` verb and `/s:doctor`. The page SHALL conform to
the shipd documentation standard with `<!-- doc-type: how-to -->` as its
first line and a total line count within the how-to cap.

The page SHALL follow the main-page shape: opening paragraphs saying what
the doctor is, then `## When to use it`, `## How to run it`, and a closing
`## Reference`, in that order. It SHALL state:

- that `shipd doctor` preflights the environment and changes nothing;
- the output contract: one `ok`, `warn`, or `fail` line per check, a closing
  `doctor: ok` or `doctor: <n> problem(s)` line, and exit code `1` only when
  a required check failed;
- that `shipd doctor --fix` installs the local tooling (`textual`, `difft`,
  the statusline, then the drive tools `ffmpeg`, `ffprobe`, and `vhs`)
  without asking, and never changes a setting on GitHub;
- the `/s:doctor` run as numbered steps: run the preflight, map each finding
  to a remedy, ask once for consent, run only the approved remedies, re-run
  the preflight, and report the before and after states;
- that `/s:doctor` runs one remedy round per invocation and never retries;
- that `/s:doctor` is the only path to the GitHub-side remedies (branch
  protection and auto-merge), each named in the consent dialog with the
  exact change;
- that `gh auth login` and `gh secret set COPILOT_GITHUB_TOKEN` stay with
  the person, and that a report-only finding has no remedy;
- in one sentence, that the review gate's setup lives on
  `copilot-review.md`, with a link.

The `## Reference` section SHALL hold a table with one row per check that a
`shipd doctor` run reports, each with what it checks, and a table of the
findings `/s:doctor` can remedy on consent with the remedy for each. The
page SHALL link `copilot-review.md`, `statusline-and-telemetry.md`, and
`customise.md`, and SHALL carry no mermaid fence. Every command on the page
SHALL be a `shipd` verb, a `/s:` skill, or a remedy command the doctor runs
on consent or hands to the person; the page SHALL name no engine script path.

#### Scenario: Page follows the main-page shape
- **WHEN** the level-2 headings of `docs/doctor.md` are listed
- **THEN** they are `## When to use it`, `## How to run it`, and
  `## Reference`, in that order

#### Scenario: Page separates the verb, the fix flag, and the skill
- **WHEN** `docs/doctor.md` is inspected
- **THEN** it states that the bare verb changes nothing, that `--fix`
  installs local tooling only, and that only `/s:doctor` offers the
  GitHub-side remedies, on consent

#### Scenario: Check table matches a run
- **WHEN** the check names in the `## Reference` table are compared with the
  lines of a `shipd doctor` run
- **THEN** every check the run reports has a row

#### Scenario: Page passes the lint and its links resolve
- **WHEN** `docs_lint.py` runs over `docs/doctor.md`
- **THEN** it exits 0 with the file marked `how-to` at 150 lines or fewer,
  the file holds no mermaid fence and no `semdiff.py` or `spec_status.py`
  path, and every relative link resolves
