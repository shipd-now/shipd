## MODIFIED Requirements

### Requirement: Brand a subject once
id: brand-subject-helper
base: b3dc3575e7d0

The engine SHALL define the constant `BRAND_PREFIX = "☕ "` in `spec_common` as the only place the prefix is spelled, and SHALL provide a stdlib-only `brand_subject(subject)` beside it. `brand_subject` SHALL return `subject` unchanged when it is empty or whitespace only, when it already starts with `☕` (which covers `☕ `, `☕` with no space, and the earlier `☕ Shipd: ` prefix), or when it starts with `fixup!`, `squash!`, or `amend!`. Otherwise it SHALL return `BRAND_PREFIX + subject`, so no subject is ever branded twice. The brand SHALL NOT be configurable.

#### Scenario: A bare subject gets the prefix
- **WHEN** `brand_subject("room: fix x")` runs
- **THEN** it returns `☕ room: fix x`

#### Scenario: Branding is idempotent
- **WHEN** `brand_subject` runs on `☕ room: fix x`, `☕room: fix x`, or `☕ Shipd: room: fix x`
- **THEN** it returns its input unchanged

#### Scenario: Autosquash subjects are left alone
- **WHEN** `brand_subject` runs on `fixup! room: fix x`
- **THEN** it returns its input unchanged

### Requirement: Brand script verbs
id: brand-script-verbs
base: c5af0b66114a

The engine SHALL ship a stdlib-only `plugins/s/skills/build/scripts/brand.py` with three verbs. `subject <text>` SHALL print `brand_subject(text)` and exit 0. `commit-msg <file>` SHALL read `git rev-parse --show-toplevel` from the working directory; while that directory's parent is not named `.worktrees`, it SHALL leave the file unchanged. Otherwise it SHALL rewrite the first line of the file that does not start with `#` through `brand_subject`. `commit-msg` SHALL always exit 0. `install-hook [--root DIR]` SHALL install the hook described in `commit-brand-hook-install` and SHALL always exit 0.

#### Scenario: Subject verb prints the branded subject
- **WHEN** `brand.py subject "Install the gate"` runs
- **THEN** it prints `☕ Install the gate` and exits 0

#### Scenario: Commit message in a shipd worktree is branded
- **GIVEN** a message file holding `hello` then a `#` comment line
- **WHEN** `brand.py commit-msg <file>` runs inside a linked worktree whose directory sits in the repository's `.worktrees` folder
- **THEN** the file's first line is `☕ hello` and the comment line is unchanged

#### Scenario: Commit message in the root checkout is untouched
- **WHEN** `brand.py commit-msg <file>` runs in the repository's root checkout
- **THEN** the file is unchanged and the exit code is 0

### Requirement: Commit hook install
id: commit-brand-hook-install
base: 4b3d514361ef

The `install-hook` verb SHALL write a POSIX `sh` file named `commit-msg` into `<git-common-dir>/hooks`, creating that directory when absent, with mode 0755. Its second line SHALL be `# shipd-managed commit-msg hook`. The file SHALL name `brand.py` by the absolute path of the installing plugin, SHALL exit 0 when that file or `python3` is missing, and otherwise SHALL run `python3 <brand.py> commit-msg "$1"` and exit 0, so a commit is never blocked. If `git config core.hooksPath` is non-empty, or a `commit-msg` file exists without the marker line, then the verb SHALL write nothing and SHALL print one line starting `note: commit branding skipped — ` naming the reason. A `commit-msg` file carrying the marker SHALL be overwritten. When the worktree create path in `worktree.py` succeeds, the engine SHALL run this install for fresh, attached, and reused worktrees alike, before the post-worktree scripts, and its outcome SHALL NOT change the create path's exit code.

#### Scenario: Create installs the hook and a worktree commit is branded
- **GIVEN** a repository with no `commit-msg` hook
- **WHEN** `worktree.py my-change` runs and a commit with message `add x` is made in the new worktree
- **THEN** `<git-common-dir>/hooks/commit-msg` carries the marker and the commit's subject is `☕ add x`

#### Scenario: A foreign hook is never clobbered
- **GIVEN** a `commit-msg` hook without the marker
- **WHEN** `worktree.py my-change` runs
- **THEN** the hook's bytes are unchanged, a `note: commit branding skipped — ` line is printed, and the exit code is 0

#### Scenario: A hooks path is never written
- **GIVEN** `core.hooksPath` set to a directory
- **WHEN** `brand.py install-hook` runs
- **THEN** nothing is written there and a `note: commit branding skipped — ` line is printed

#### Scenario: A missing engine never blocks a commit
- **GIVEN** an installed hook whose named `brand.py` path does not exist
- **WHEN** a commit is made in a shipd worktree
- **THEN** the commit succeeds with its subject unchanged

### Requirement: Engine and skill commits are branded
id: brand-engine-commits
base: e3b6d8074f8d

`spec_common.wiki_autocommit` SHALL commit with `brand_subject(subject)`. The `/s:gate` install and refresh commit lines and the `/s:epic` store amend commit line SHALL render their subject through `brand.py subject`.

#### Scenario: A store auto-commit is branded
- **WHEN** an engine wiki write auto-commits with subject `shipd-wiki: queue-add q-x`
- **THEN** the commit's subject is `☕ shipd-wiki: queue-add q-x`

#### Scenario: Skill commit lines use the helper
- **WHEN** the test reads `plugins/s/skills/gate/SKILL.md` and `plugins/s/skills/epic/SKILL.md`
- **THEN** every `commit -m` line in them contains `brand.py" subject`
