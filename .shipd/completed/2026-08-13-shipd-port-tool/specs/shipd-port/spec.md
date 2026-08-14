## ADDED Requirements

### Requirement: Port tool verbs and exit codes
id: port-verbs

The port tool SHALL expose three verbs — `plan`, `apply`, and `verify` — where
`plan` reports the operations it would perform and writes nothing, `apply`
performs them, and `verify` scans an existing destination. The tool SHALL exit
`0` when clean, `2` when it reports findings, and `1` on a general error printed
as `Error: <message>` on stderr.

#### Scenario: Plan writes nothing
- **WHEN** `port.py plan --source <src> --ref <ref> --dest <dst>` runs against an
  empty destination
- **THEN** the planned operations are printed and the destination contains no new
  file

#### Scenario: General error exits 1
- **WHEN** `port.py plan` is given a `--source` that is not a git repository
- **THEN** the command prints `Error: ` on stderr and exits `1`

### Requirement: Source is read from a git ref
id: port-source-ref

The port tool SHALL enumerate source files with `git ls-files` at the supplied
`--ref` and read their content at that same ref, so that a run is reproducible
and unaffected by uncommitted working-tree state. Untracked and ignored files
SHALL NOT be ported.

#### Scenario: Dirty working tree does not affect the port
- **WHEN** the source repository has an uncommitted modification to a tracked
  file and `port.py apply --ref HEAD` runs
- **THEN** the ported copy carries the committed content, not the modification

#### Scenario: Untracked files are not ported
- **WHEN** the source repository contains an untracked file and `port.py apply`
  runs
- **THEN** no counterpart to that file exists in the destination

### Requirement: Ordered longest-first anchored substitution
id: port-token-map

The port tool SHALL apply its token substitutions in a fixed order, longest and
most specific token first, and SHALL NOT substitute a bare `am`. Where a token is
a substring of an earlier-ordered token, the earlier rule SHALL consume it first.

#### Scenario: Config filename is not corrupted by the capability rule
- **WHEN** a source file contains the text `.shipd-config.json` and `shipd-config` is
  an enumerated capability slug
- **THEN** the ported file contains `.shipd-config.json` and does not contain
  `.shipd-shipd-config.json` or `.am-shipd-config.json`

#### Scenario: Ordinary English containing "am" is untouched
- **WHEN** a source file contains the words `ambiguous`, `stream`, and `param`
- **THEN** those words are unchanged in the ported file

#### Scenario: A bare quoted content-directory segment is rewritten
- **WHEN** a source file contains `DEFAULT_DIR = ".shipd"` and
  `os.path.join(root, ".shipd", "planned", slug)`
- **THEN** the ported file contains `".shipd"` in both places

#### Scenario: A quoted segment rule does not match longer strings
- **WHEN** a source file contains `".shipd-config.json"` and the word `".among"`
- **THEN** neither is rewritten by the quoted-segment rule

#### Scenario: Anchored forms are rewritten
- **WHEN** a source file contains `/s:plan`, `s:oracle`, `plugins/s/x.py`,
  `s@shipd`, and `~/.shipd-memory`
- **THEN** the ported file contains `/s:plan`, `s:oracle`, `plugins/s/x.py`,
  `s@shipd`, and `~/.shipd-memory`

### Requirement: Capability slugs are enumerated, not guessed
id: port-capability-enum

The port tool SHALL derive its capability-rename rules by listing the source's
`.shipd/verified/` directory at the ref and taking the directories whose names match
`am-<name>`, and SHALL rename each to `shipd-<name>` in both paths and content.
It SHALL NOT apply a general `am-<word>` pattern to text.

#### Scenario: Only enumerated slugs are renamed
- **WHEN** the source has `.shipd/verified/shipd-plan/` but no `am-widget` capability,
  and a file contains both `shipd-plan` and `am-widget`
- **THEN** the ported file contains `shipd-plan` and still contains `am-widget`

#### Scenario: Capability directories are renamed on disk
- **WHEN** the source has `.shipd/verified/shipd-plan/spec.md` and
  `.shipd/completed/x/specs/shipd-plan/spec.md`
- **THEN** the destination has `.shipd/verified/shipd-plan/spec.md` and
  `.shipd/completed/x/specs/shipd-plan/spec.md`

### Requirement: Apply writes only mapped paths and excludes dropped trees
id: port-apply-scope

When applying, the port tool SHALL create or overwrite only the destination paths
its path map produced, and SHALL leave every other file in the destination
untouched. Paths under `openspec/` and `.shipd/` SHALL be excluded from the
port entirely.

#### Scenario: Pre-existing destination files survive
- **WHEN** the destination already contains `LICENSE` and `port.py apply` runs
- **THEN** `LICENSE` is unchanged after the run

#### Scenario: Dropped trees are not ported
- **WHEN** the source contains `openspec/specs/x/spec.md` and `.shipd/state.json`
- **THEN** the destination contains no counterpart to either path

### Requirement: Port can be restricted to a source subtree
id: port-include-filter

The port tool SHALL accept a repeatable `--include <prefix>` option on `plan` and
`apply` that restricts the run to source paths beginning with one of the given
prefixes. When no `--include` is given, the whole tree SHALL be ported. The
residual scan SHALL cover only the files the run actually wrote.

#### Scenario: Include restricts what is written
- **WHEN** `port.py apply --include plugins/s/` runs against a source that also
  contains `.shipd/verified/shipd-plan/spec.md`
- **THEN** the destination has `plugins/s/…` and no `.shipd/verified/` path

#### Scenario: Repeated include unions the prefixes
- **WHEN** `port.py apply --include plugins/s/ --include requirements.txt` runs
- **THEN** the destination carries both the ported plugin tree and
  `requirements.txt`, and nothing else

#### Scenario: No include ports everything
- **WHEN** `port.py apply` runs with no `--include`
- **THEN** every non-excluded source path has a destination counterpart

### Requirement: Residual match scan reports rather than passes silently
id: port-residual-scan

After writing, the port tool SHALL scan every written text file for a residual
`shipd` or an anchored `am` form its map should have rewritten, SHALL report
each as `<path>:<line>: <match>`, and SHALL exit `2` when any is found. Binary or
non-UTF-8 files SHALL be copied byte-for-byte, never substituted, and SHALL be
excluded from the scan.

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
