# content-dir-nested
Status: verified

## Idea

Allow the configured content directory (`dir` in `.shipd-config.json`) to be a
nested relative path such as `.agents/specs/.shipd`, and make the worktree
remove guard honor the configured name.

### Motivation

The `dir` key is validated down to a single path component, so a repository
cannot group its spec library under a subfolder like `.agents/specs/.shipd` —
a layout the user asked for directly. Every engine surface already resolves
through the `specs_dir` funnel, so only the validator and one hardcoded shell
guard stand in the way.

### Details

- Relax `specs_dirname` in `plugins/s/skills/build/scripts/spec_common.py` to
  accept `/`-separated relative paths; keep rejecting absolute values,
  backslashes, and `.`/`..`/empty components.
- Join the nested components portably in `specs_dir`.
- Resolve the configured content directory in `worktree.sh`'s remove guard
  instead of the literal `.shipd/planned`, falling back to `.shipd` when
  resolution fails.
- Tests in `tests/test_spec_common.py` and `tests/test_worktree.py`; plugin
  version bump.

Affected capabilities: `shipd-config` (modified), `build-spec-lifecycle`
(modified). Impact: `spec_common.py`, `worktree.sh`, the two test files,
`plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No change to `statusline.sh`: the constitution pins it POSIX-only with no
  Python spawns, and its header (statusline.sh:16-18) already documents the
  literal-`.shipd` limitation for any renamed content directory.
- No change to `store_root` semantics — a declared store root still supersedes
  `dir` wholesale.
- No configurability of the `.shipd-config.json` filename itself.
- No Windows drive-letter handling beyond rejecting absolute paths.

## Implementation

- **Validation contract** (`specs_dirname`, spec_common.py:435): accept a
  relative `/`-separated path; raise `ConfigError` naming the offending value
  for a non-string or empty value, an absolute path (`os.path.isabs`; `dir`
  never expands `~`), any backslash, or any component that is empty, `.`, or
  `..`. Rejected alternative: permitting `..` or absolute values — they escape
  the repository root and break the worktree/PR model where artifacts must
  travel inside the repo.
- **Portable join** (`specs_dir`, spec_common.py:551): join as
  `os.path.join(root, *name.split("/"))` so the committed config value stays
  `/`-separated while the resolved path is native. The callers that use the
  bare name as a relative fragment — `spec_lint.py:342` (joins onto root),
  `harness_generate.py:296` (`/`-joins the refs label),
  `guardrails.py rules_dirs` (`<ancestor>/<name>/rules`) — all work unchanged
  with a multi-component name; each call site was read to confirm.
- **Worktree remove guard** (`worktree.sh:212`): resolve the content directory
  once per `remove` by running the engine —
  `python3 "<script-dir>/spec_status.py" --root "$WORKTREE" config-show`
  filtered to its `content-dir:` line — and scan
  `$WORKTREE/<content-dir>/planned`. On any failure (python3 absent, malformed
  config, empty output) fall back to the literal `.shipd`, so the guard is
  never weaker than today and the helper still runs in repositories with
  nothing but git. Refusal reason text names the resolved directory. Rejected
  alternative: parsing the layered `.shipd-config.json` merge in shell —
  reimplementing nearest-wins JSON merging in bash 3.2 is exactly the drift
  the single-funnel rule exists to prevent.
- **Verified premises** (run before emission): `spec_status.py config-show`
  prints a machine-greppable `content-dir: .shipd` line (exit 0), and the
  current validator rejects the nested value — `config-show` against a config
  declaring `dir: ".agents/specs/.shipd"` exits 1 with
  "config `dir` must be a single path component".
- `spec-library-path-notation` already reads `.shipd/` literals in master
  requirement text as the configured directory, so `plugin-worktree-helper`'s
  existing text mandates the guard behavior; the added
  `worktree-guard-content-dir` requirement makes the resolution and its
  fallback explicit so the validator exercises it.
- Nested parents at `init` need no extra work: `cmd_init` creates each layout
  directory with `os.makedirs(..., exist_ok=True)` (spec_status.py:469).
- **Version bump**: `plugins/s/.claude-plugin/plugin.json` → `0.6.185`, per
  the cache-snapshot rule in AGENTS.md.
