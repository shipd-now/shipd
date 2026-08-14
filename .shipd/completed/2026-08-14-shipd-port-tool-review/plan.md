# shipd-port-tool-review
Status: verified
Epic: shipd-port
Theme: spec-engine

## Idea

Correct the `shipd-port` contract to describe what `tools/port.py` actually
guarantees after the semantic review of `shipd-port-tool`.

### Motivation

The `shipd-port-tool` member shipped with six requirements that its
implementation did not honour, and the review of
[PR #199](https://github.com/mikkel-bergmann/shipd/pull/199) found them. The
code fixes landed in `shipd-now/shipd` as commit `9953976`; this change brings
the master library back in step with them. Leaving the library describing the
old behaviour would mislead members 2 and 3, which read the map rather than the
diff.

### Details

- `port-source-ref`: enumeration reads the *tree* at `--ref`, never the index,
  and a failed run leaves the destination untouched.
- `port-apply-scope`: the git-recorded executable bit survives the port.
- `port-verbs`: a `--source` below the repository root and a `verify --dest`
  that does not exist are errors, not empty successes.
- `port-include-filter`: `--include` matches on whole path segments.
- `port-residual-scan`: text files are written as UTF-8, never in the ambient
  locale's encoding.

Affected capabilities: `shipd-port` (modified). Impact: the master library
only; the code the requirements describe already exists in shipd.

### Non-goals

- No further change to `tools/port.py`. Every behaviour written here is already
  implemented and covered by the shipd suite (25 tests); this change records the
  contract, it does not extend it.
- No edit to `.shipd/completed/2026-08-13-shipd-port-tool/`. Completed changes are
  immutable (`.shipd/constitution.md`), so that member's `plan.md` and `tasks.md`
  keep their as-shipped text — including the `ls-files --with-tree` bullet the
  review corrected. The library, not the archive, is the live contract.

## Implementation

- **Five MODIFIED requirements, no ADDED and no REMOVED.** Each keeps its `id`
  and carries the `base:` hash of the text it replaces, so the merge is checked
  against exactly the version reviewed.

- **The requirement bodies gain the constraint the review found missing, and the
  scenarios pin it.** Eight scenarios are added across the five requirements:
  a staged addition is not ported; an earlier ref ports that ref's tree; a
  failed run writes nothing; executable files stay executable; a source below
  the repository root is rejected; verify on a missing destination is an error;
  include matches whole path segments; non-ASCII text ports as UTF-8 under an
  `LC_ALL=C` locale. Each maps to a test that fails against the pre-fix
  implementation.

- **`port-source-ref`'s wording moves off the command name.** It said "enumerate
  source files with `git ls-files` at the supplied `--ref`", which named a
  command that cannot express the requirement — `ls-files` reads the index. The
  new text states the property ("from the tree at the supplied `--ref`, never
  from the index") and leaves the command to the implementation. Rejected:
  naming `ls-tree` instead — the same mistake with a better command.

- **`port-verbs` says which verbs create a missing `--dest` and which reject
  it.** `verify` errors on a `--dest` that does not exist; `plan` and `apply`
  create it (`mkdir(parents=True)`), which is what makes a first port into an
  empty repo work. Stating only the error half would read as forbidding that.

Risk: none to running code. The requirements describe behaviour that already
ships and is under test; this change can only fall out of step if `port.py`
regresses, which its suite guards.
