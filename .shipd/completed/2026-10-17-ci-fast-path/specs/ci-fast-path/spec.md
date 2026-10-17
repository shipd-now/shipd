## ADDED Requirements

### Requirement: Path classifier fails closed
id: ci-scope-classifier

The CI scope classifier SHALL report a fast path only when the changed-path list is non-empty and every path lies under `.shipd/epics/`, `.shipd/research/`, or `.shipd/docs/`. If the list is empty, a path lies elsewhere, a path contains a `..` segment, the event is not `pull_request`, or git fails, then the classifier SHALL report the full path and exit 0.

#### Scenario: Epic-only change is fast
- **WHEN** the changed paths are `.shipd/epics/x/epic.md` and `.shipd/research/y/report.md`
- **THEN** the classifier prints `fast=true`

#### Scenario: Mixed change is full
- **WHEN** the changed paths include `.shipd/epics/x/epic.md` and `plugins/s/skills/build/scripts/spec_lint.py`
- **THEN** the classifier prints `fast=false`

#### Scenario: Master specs and top-level docs are full
- **WHEN** the only changed path is `.shipd/verified/x/spec.md` or `docs/customise.md`
- **THEN** the classifier prints `fast=false`

#### Scenario: Push and git failure are full
- **WHEN** the event is `push`, or `git diff` fails
- **THEN** the classifier prints `fast=false` and exits 0

### Requirement: CI keeps one required check with a guarded fast path
id: ci-fast-path-workflow

The `ci` workflow SHALL keep a single job named `ci`, SHALL run the classifier in a step with id `scope`, and SHALL guard every test-suite step, the dependency install, and the difftastic install with `if: steps.scope.outputs.fast != 'true'`. The version guard and every lint step SHALL remain unguarded.

#### Scenario: Every test step is guarded
- **WHEN** `ci.yml` is read
- **THEN** each step running `unittest discover`, `pip install`, or the difftastic download carries the `scope` guard

#### Scenario: Lints always run
- **WHEN** `ci.yml` is read
- **THEN** the spec library lint, in-flight lint, docs lint, and shell syntax steps carry no `if:` on `scope`
