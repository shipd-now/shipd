## ADDED Requirements

### Requirement: Declared new paths
id: declared-new-paths

Refining the gate's task-path check, the gate SHALL treat a path-shaped backticked token in `tasks.md` as declared
new when the word `Create` or `Add`, in any letter case, directly precedes it
with only whitespace, including a line break, between them. A declared path
SHALL produce no file-reference finding, and each of its parent directories
SHALL count as an existing directory for every other token in `tasks.md`,
whatever the task order, in place of the check's existing-directory test. One leading `./` SHALL be ignored. An absolute token,
or one holding a `..` segment, SHALL declare nothing.

#### Scenario: A greenfield tree passes
- **GIVEN** a repository with no `packages/` directory
- **WHEN** one task cites `packages/rules/firestore.rules` and a later task
  reads "Create `packages/rules/package.json`"
- **THEN** no file-reference finding is produced for either path

#### Scenario: Root-level and dot directories can be declared
- **GIVEN** neither `functions/` nor `.github/` exists
- **WHEN** tasks read "Create `functions/package.json`" and
  "Add `.github/workflows/ci.yml`"
- **THEN** no file-reference finding is produced for either path

#### Scenario: A line wrap keeps the declaration
- **WHEN** a task ends a line with "create" and the next indented line starts
  with `new/a/b/c.py` in backticks
- **THEN** no file-reference finding is produced for it

#### Scenario: Words between the verb and the path declare nothing
- **WHEN** a task reads "Add a test to `src/ghost/nested/missing.py`" and
  neither `src/ghost/nested/` nor `src/ghost/` exists
- **THEN** the findings name that token

#### Scenario: A mistyped sibling of a declared tree is a finding
- **WHEN** tasks read "Create `new/a/b/c.py`" and "Edit `nwe/a/b/d.py`"
- **THEN** the findings name `nwe/a/b/d.py` and not `new/a/b/c.py`

#### Scenario: A path outside the repository declares nothing
- **WHEN** a task reads "Create `../ghost/a/b.py`" and the path and its parent
  and grandparent directories do not exist
- **THEN** the findings name that token

### Requirement: Slash tokens that are not repository paths
id: non-path-token-skip

Refining the gate's task-path check, the gate SHALL skip a token that the
check would otherwise report when its final segment holds no `.`, its first
segment is neither a directory under the repository root nor implied by a
declared path, and it does not start with `artefacts/`.

#### Scenario: Tokens that are not repository paths are skipped
- **GIVEN** none of `origin/`, `application/`, `firebase/` or `orgs/` exists
- **WHEN** a task names `origin/main`, `application/octet-stream`,
  `firebase/app` and `orgs/x` in backticks
- **THEN** no file-reference finding is produced for any of them

#### Scenario: Extensionless path under an existing directory is checked
- **GIVEN** `src/` exists and `src/ghost/` does not
- **WHEN** a task names `src/ghost/nested/missing` in backticks
- **THEN** the findings name that token

#### Scenario: Extensionless artefact reference is checked
- **GIVEN** the change directory holds no `artefacts/ghost`
- **WHEN** a task names `artefacts/ghost` in backticks
- **THEN** the findings name that token

### Requirement: Task-path root exclusion and remedy
id: task-path-remedy

Within the gate's task-path check, the repository root itself SHALL NOT count
as an existing parent or grandparent directory, except that a token written
with a leading `./` keeps `.` as a directory in its own path. Each file-reference finding
SHALL name the remedy: the full path from the repository root, or a `Create`
declaration.

#### Scenario: The root is not an accepted grandparent
- **GIVEN** no `dist/` directory exists
- **WHEN** a task reads "Edit `dist/index.js`"
- **THEN** the findings name `dist/index.js`

#### Scenario: A dot-relative token keeps its resolution
- **GIVEN** no `src/` directory exists
- **WHEN** a task names `./src/index.ts` in backticks
- **THEN** no file-reference finding is produced for it

#### Scenario: A dangling edit names the remedy
- **WHEN** a task reads "Edit `src/ghost/nested/missing.py`" and neither
  `src/ghost/nested/` nor `src/ghost/` exists
- **THEN** the finding says both levels are missing, asks for the full path
  from the repository root, and names the `Create` declaration
