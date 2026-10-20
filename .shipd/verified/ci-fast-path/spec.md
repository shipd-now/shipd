# ci-fast-path

### Requirement: Path classifier fails closed
id: ci-scope-classifier

The CI scope classifier SHALL report the `content` scope only when the changed-path list is non-empty and every path lies under `.shipd/epics/`, `.shipd/research/`, or `.shipd/docs/`. If the list is empty, a path lies elsewhere, a path contains a `..` segment or a backslash, the event is not `pull_request`, or git fails, then the classifier SHALL report the `full` scope and exit 0. The classifier SHALL print its result as a `scope=content` or `scope=full` line and SHALL append that same line to the GitHub output file when one is named.

#### Scenario: Epic-only change has content scope
- **WHEN** the changed paths are `.shipd/epics/x/epic.md` and `.shipd/research/y/report.md`
- **THEN** the classifier prints `scope=content`

#### Scenario: Mixed change has full scope
- **WHEN** the changed paths include `.shipd/epics/x/epic.md` and `plugins/s/skills/build/scripts/spec_lint.py`
- **THEN** the classifier prints `scope=full`

#### Scenario: Master specs and top-level docs have full scope
- **WHEN** the only changed path is `.shipd/verified/x/spec.md` or `docs/customise.md`
- **THEN** the classifier prints `scope=full`

#### Scenario: Push and git failure have full scope
- **WHEN** the event is `push`, or `git diff` fails
- **THEN** the classifier prints `scope=full` and exits 0

#### Scenario: The output file carries the scope line
- **WHEN** the classifier runs with a GitHub output file on an epic-only pull request
- **THEN** the file's only line is `scope=content`

### Requirement: CI keeps one required check with a scope-guarded test run
id: ci-scope-workflow

The `ci` workflow SHALL keep a single job named `ci`, SHALL run the CI scope classifier in a step with id `scope`, and SHALL guard every test-suite step, the dependency install, and the difftastic install with `if: steps.scope.outputs.scope != 'content'`, so a missing or failed classifier output runs the full suite. The pull request version guard, the main-branch version check, and every lint step SHALL carry no `scope` guard. The workflow SHALL NOT read a `fast` output from the classifier.

#### Scenario: Every test step is scope-guarded
- **WHEN** `ci.yml` is read
- **THEN** each step running `unittest discover`, `pip install`, or the difftastic download carries `if: steps.scope.outputs.scope != 'content'`

#### Scenario: Lints and version checks always run
- **WHEN** `ci.yml` is read
- **THEN** the spec library lint, in-flight lint, docs lint, shell syntax, pull request version guard, and main version check steps carry no `if:` on `scope`

#### Scenario: No step reads the old output
- **WHEN** `ci.yml` is read
- **THEN** no step contains `outputs.fast`
