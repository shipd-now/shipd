## ADDED Requirements

### Requirement: Gate workflow grounds the CLI review itself
id: gate-review-grounding

Where the CLI reviewer is configured on a `pull_request` event, the review-gate workflow template SHALL run a grounding step before the reviewer step. The grounding step SHALL bind neither the reviewer secret nor `github.token`. It SHALL run the review engine's `files` and `diff` subcommands with the pull request's base SHA first and its head SHA second, and SHALL write each output to a file in the runner temp directory. It SHALL report `outcome` (`ok` or `failed`) and `files` (the files output's summary file count) as step outputs, and SHALL exit zero whatever the engine did. The engine it runs SHALL be the base ref's copy of `.github/skills/code-review/scripts/semdiff.py`, resolved the way the reviewer instructions are pinned, and the reviewed commit's copy only where the base tree has no such file. The reviewer prompt SHALL name both grounding files and SHALL tell the reviewer not to run `files` or `diff` itself. The reviewer step SHALL skip the Copilot CLI when the outcome is not `ok`.

The posting step SHALL read the grounding outcome and count from the step outputs, never from the workspace files. If the outcome is not `ok`, or the count is `0` while the pull request's changed-files read lists at least one file or failed, then the posting step SHALL re-post `semantic-review` as `pending` with a description starting `Review not grounded:` and naming the cause. It SHALL submit no `APPROVE` or `REQUEST_CHANGES` review and SHALL NOT arm fast-pass. Any body it publishes SHALL go out as a `COMMENT` review opening with a "Not a verdict" notice. It SHALL ignore `SHIPD_GATE_FAIL_OPEN` on this path and SHALL exit non-zero.

#### Scenario: The engine runs base first, head second
- **WHEN** the gate script runs on the CLI path with the stub engine
- **THEN** the engine recorded `files <base sha> <head sha>` and `diff <base sha> <head sha>`, and the grounding step wrote `outcome=ok` and the stub's file count to its outputs

#### Scenario: The prompt hands the reviewer the grounding
- **WHEN** the stubbed CLI's prompt is read
- **THEN** it names both grounding files and tells the reviewer not to run `files` or `diff`

#### Scenario: The base ref's engine is the one run
- **WHEN** the base ref carries an engine and the checkout holds a different one
- **THEN** the base copy's output is the grounding, and the checkout's copy runs only when the base carries none

#### Scenario: A zero-file grounding never approves
- **GIVEN** the engine reports 0 files, the changed-files read lists one file, and the reviewer ends with the ship-it marker
- **WHEN** the gate script runs with the fail-open default
- **THEN** the last status posted is `pending` with a `Review not grounded:` description, the one review submitted is a `COMMENT` whose body opens with the notice, no merge is armed, and the run exits non-zero

#### Scenario: A failed engine skips the reviewer
- **WHEN** the engine exits non-zero
- **THEN** the Copilot CLI is never invoked, the status is re-posted `pending` with a `Review not grounded:` description, and the run exits non-zero

#### Scenario: An empty pull request is still grounded
- **WHEN** the engine reports 0 files and the changed-files read lists none
- **THEN** the verdict marker is classified as before

### Requirement: Gate workflow posts only the review report
id: gate-report-extraction

The review-gate workflow template SHALL invoke the Copilot CLI with `-s`. Before classifying, the posting step SHALL reduce the captured text to the report on the CLI path. It SHALL keep from the last line starting with `## Findings` that precedes the last verdict-marker line, through that marker line. With no marker, it SHALL keep from the last `## Findings` line to the end. With no such line, it SHALL keep the text minus every tool-call transcript block: a line starting with `●` and a space, plus the lines right after it whose left-trimmed text starts with `│` or `└`. The verdict SHALL be classified from the reduced text, and the reduced text SHALL be the body that is published.

#### Scenario: The CLI runs silent
- **WHEN** the stubbed CLI's arguments are read
- **THEN** they include `-s`

#### Scenario: Narration and transcript are dropped
- **GIVEN** CLI output carrying narration and tool-call blocks, then a `## Findings: ✅ Ship it` report ending in the ship-it marker, then trailing narration
- **WHEN** the gate script runs
- **THEN** the published body starts at the `## Findings` line, holds no `●` line, keeps the marker as its last line equal to a marker, and the status is `success`

#### Scenario: Header-less output loses only its transcript blocks
- **WHEN** the CLI output has no `## Findings` line
- **THEN** the published body keeps the prose but holds no tool-call block lines

### Requirement: Contract reads supplied grounding
id: skill-supplied-grounding

The Copilot review skill template SHALL tell the reviewer that, when the invoking prompt names files holding the engine's `files` and `diff` output, it reads those as its map and structural diff and does not run those subcommands itself. It SHALL also say that the gate computes that output with the base first and fails closed when it covers no files.

#### Scenario: The template names the supplied grounding
- **WHEN** `plugins/s/integrations/copilot/SKILL.md` is read
- **THEN** it says supplied `files` and `diff` output is read instead of re-running those subcommands, and that the gate fails closed on an empty grounding

### Requirement: Grounded CI review ships tests, docs, and a version bump
id: ci-review-grounded-ships

The change SHALL cover the grounding, the fail-closed path, and the report extraction with offline tests in `plugins/s/skills/build/tests/test_copilot_verb.py` that stub `copilot`, `gh`, `git`, and the engine. It SHALL describe the grounding and the fail-closed rule in `docs/copilot-review-reference.md`, and the `/s:gate update` refresh in `docs/copilot-review.md`, with both passing `docs_lint.py`. It SHALL advance the plugin version in `plugins/s/.claude-plugin/plugin.json` by one patch above the value `main` carries.

#### Scenario: Offline suites pass
- **WHEN** `python3 -m unittest discover -s plugins/s/skills/build/tests` runs with no network
- **THEN** it reports `OK`

#### Scenario: Version guard passes
- **WHEN** `version_guard.py --base main --head HEAD` runs on the change
- **THEN** it exits `0`
