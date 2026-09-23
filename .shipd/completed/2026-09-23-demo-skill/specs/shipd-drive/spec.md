## MODIFIED Requirements

### Requirement: Drive preflight
id: drive-doctor
base: 675c1d55ea61

The CLI SHALL expose a `doctor` verb reporting each prerequisite's state:
`uv` and a Playwright browser binary are required for every verb, and
`ffmpeg` and `ffprobe` are required only for recording and post-processing,
and `vhs` is required only for terminal recording. The verb SHALL fail on a
missing recording-only tool solely when the invocation declares it needs
that tier, so driving and browser recording stay unaffected by an absent
`vhs`.
The verb SHALL exit non-zero when a required tool is missing and zero
otherwise, and SHALL name a remedy for each missing tool. Where `doctor` is
invoked with `--fix`, it SHALL install the missing browser binary through the
Playwright worker and re-report, SHALL NOT install any other tool, and
SHALL name `brew install vhs` as the manual remedy for a missing `vhs`, and SHALL state the network access it
performs before performing it.

#### Scenario: A missing required tool fails the preflight
- **WHEN** `doctor` runs with `uv` absent from PATH
- **THEN** the report marks `uv` missing with a remedy and the exit code is
  non-zero

#### Scenario: Video tools are optional for driving
- **WHEN** `doctor` runs with `ffmpeg` absent but `uv` and the browser present
- **THEN** the report marks `ffmpeg` as required for recording only and the
  exit code is zero

#### Scenario: An absent terminal recorder never blocks driving
- **WHEN** `doctor` runs with `vhs` absent but `uv` and the browser present
- **THEN** the report marks `vhs` as required for terminal recording only,
  names `brew install vhs` as its remedy, and the exit code is zero

#### Scenario: The fix flag never installs the terminal recorder
- **WHEN** `doctor --fix` runs with `vhs` absent
- **THEN** no installation of `vhs` is attempted and the report still names
  its manual remedy
