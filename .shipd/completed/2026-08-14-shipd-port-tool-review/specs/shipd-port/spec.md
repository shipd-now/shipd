## MODIFIED Requirements

### Requirement: Port tool verbs and exit codes
id: port-verbs
base: 4cf997a62f37

The port tool SHALL expose three verbs — `plan`, `apply`, and `verify` — where
`plan` reports the operations it would perform and writes nothing, `apply`
performs them, and `verify` scans an existing destination. The tool SHALL exit
`0` when clean, `2` when it reports findings, and `1` on a general error printed
as `Error: <message>` on stderr. A `--source` that is not a repository root, and
a `verify --dest` that does not exist, SHALL be general errors rather than empty
successes. `plan` and `apply` SHALL create a missing `--dest`.

#### Scenario: Plan writes nothing
- **WHEN** `port.py plan --source <src> --ref <ref> --dest <dst>` runs against an
  empty destination
- **THEN** the planned operations are printed and the destination contains no new
  file

#### Scenario: General error exits 1
- **WHEN** `port.py plan` is given a `--source` that is not a git repository
- **THEN** the command prints `Error: ` on stderr and exits `1`

#### Scenario: A source below the repository root is rejected
- **WHEN** `port.py plan` is given a `--source` that is a subdirectory of a git
  repository rather than its root
- **THEN** the command prints `Error: ` on stderr and exits `1` rather than
  reporting an empty plan

#### Scenario: Verify on a missing destination is an error
- **WHEN** `port.py verify` is given a `--dest` that does not exist
- **THEN** the command prints `Error: ` on stderr and exits `1` rather than
  reporting a clean scan

### Requirement: Source is read from a git ref
id: port-source-ref
base: aab14e821927

The port tool SHALL enumerate source files from the tree at the supplied
`--ref`, never from the index, and read their content at that same ref, so that
a run is reproducible and unaffected by working-tree and index state.
Untracked, ignored, and staged-but-uncommitted files SHALL NOT be ported. A run
that fails SHALL leave the destination untouched.

#### Scenario: Dirty working tree does not affect the port
- **WHEN** the source repository has an uncommitted modification to a tracked
  file and `port.py apply --ref HEAD` runs
- **THEN** the ported copy carries the committed content, not the modification

#### Scenario: Untracked files are not ported
- **WHEN** the source repository contains an untracked file and `port.py apply`
  runs
- **THEN** no counterpart to that file exists in the destination

#### Scenario: A staged addition is not ported
- **WHEN** the source repository has a `git add`-ed but uncommitted new file and
  `port.py apply --ref HEAD` runs
- **THEN** the run succeeds and no counterpart to that file exists in the
  destination

#### Scenario: An earlier ref ports that ref's tree
- **WHEN** the source repository has two commits and `port.py apply --ref` names
  the first
- **THEN** the run succeeds, the first commit's file is ported, and the second
  commit's file has no destination counterpart

#### Scenario: A failed run writes nothing
- **WHEN** `port.py apply` is given a `--ref` that does not resolve
- **THEN** the command exits `1` and the destination contains no new file

### Requirement: Apply writes only mapped paths and excludes dropped trees
id: port-apply-scope
base: 8312cc707c1a

When applying, the port tool SHALL create or overwrite only the destination
paths its path map produced, SHALL preserve each file's git-recorded executable
bit, and SHALL leave every other file in the destination untouched. Paths under
`openspec/` and `.shipd/` SHALL be excluded from the port entirely.

#### Scenario: Executable files stay executable
- **WHEN** the source has a file recorded in git with mode `100755` alongside
  one recorded `100644`, and `port.py apply` runs
- **THEN** the ported counterpart of the first is executable and the ported
  counterpart of the second is not

#### Scenario: Pre-existing destination files survive
- **WHEN** the destination already contains `LICENSE` and `port.py apply` runs
- **THEN** `LICENSE` is unchanged after the run

#### Scenario: Dropped trees are not ported
- **WHEN** the source contains `openspec/specs/x/spec.md` and `.shipd/state.json`
- **THEN** the destination contains no counterpart to either path

### Requirement: Port can be restricted to a source subtree
id: port-include-filter
base: 7f8ce66a0521

The port tool SHALL accept a repeatable `--include <prefix>` option on `plan`
and `apply` that restricts the run to source paths equal to, or lying under, one
of the given prefixes, matched on whole path segments. When no `--include` is
given, the whole tree SHALL be ported. The residual scan SHALL cover only the
files the run actually wrote.

#### Scenario: Include restricts what is written
- **WHEN** `port.py apply --include plugins/s/` runs against a source that also
  contains `.shipd/verified/shipd-plan/spec.md`
- **THEN** the destination has `plugins/s/…` and no `.shipd/verified/` path

#### Scenario: Include matches whole path segments
- **WHEN** `port.py apply --include plugins/am` runs against a source that also
  contains `plugins/amx/y.py`
- **THEN** the destination carries the ported `plugins/s/` tree and no
  counterpart to `plugins/amx/y.py`

#### Scenario: Repeated include unions the prefixes
- **WHEN** `port.py apply --include plugins/s/ --include requirements.txt` runs
- **THEN** the destination carries both the ported plugin tree and
  `requirements.txt`, and nothing else

#### Scenario: No include ports everything
- **WHEN** `port.py apply` runs with no `--include`
- **THEN** every non-excluded source path has a destination counterpart

### Requirement: Residual match scan reports rather than passes silently
id: port-residual-scan
base: b28b555f8a8e

After writing, the port tool SHALL scan every written text file for a residual
`shipd` or an anchored `am` form its map should have rewritten, SHALL report
each as `<path>:<line>: <match>`, and SHALL exit `2` when any is found. Binary or
non-UTF-8 files SHALL be copied byte-for-byte, never substituted, and SHALL be
excluded from the scan. Text files SHALL be written as UTF-8, never in the
ambient locale's encoding.

#### Scenario: An unmapped anchored form is reported
- **WHEN** a source file contains an anchored form the map does not cover, such
  as `~/.am-designs/`
- **THEN** `apply` reports that file and line and exits `2`

#### Scenario: A clean port exits zero
- **WHEN** every source token is covered by the map
- **THEN** `apply` reports no findings and exits `0`

#### Scenario: Binary files pass through unchanged
- **WHEN** the source contains a binary file whose bytes are not valid UTF-8
- **THEN** the destination copy is byte-identical and the file produces no scan
  finding

#### Scenario: Non-ASCII text ports as UTF-8 regardless of locale
- **WHEN** a source file contains non-ASCII text and `port.py apply` runs under a
  non-UTF-8 locale such as `LC_ALL=C`
- **THEN** the run succeeds and the ported file's bytes are valid UTF-8
