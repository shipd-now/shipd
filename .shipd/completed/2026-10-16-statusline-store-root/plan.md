# statusline-store-root
Status: verified
Planned-at: 3337c893ff72d30c2bde67eb045230c3c8c6e121
Gated-hash: 9c34e97fe3b8

## Idea

Make the statusline find specs wherever the engine finds them — an external
`store_root` store, a renamed content directory, a linked worktree — and show
`no specs` instead of nothing when it finds none.

### Motivation

In a workspace that keeps its specs in a `store_root` store, the statusline
prints nothing: it only ever looks at `<current_dir>/.shipd/`, while the
engine reads `<store>/<repo folder>`. A stale in-repo `.shipd/` left over
from before the move is worse — the statusline renders it, and its status
disagrees with the engine's. `shipd doctor` reports `ok statusline` through
all of this because it checks only the registration.

### Details

The script walks `.shipd-config.json` files upward from the session
directory (plus `~/.shipd-config.json`), takes `store_root` and `dir` from
the nearest declaring file, finds the main checkout from `.git`, and probes
`<store>/<registry path>` then `<store>/<checkout name>`. In a workspace root
it shows that root's own folder — the same folder `spec_status.py` reads.
When nothing resolves it prints `☕ no specs` (plus any context/directory
segments and chained statusline) instead of staying silent. The doctor runs
the script's new `--print-content-dir` and warns when it differs from the
engine's folder.

### Non-goals

- No aggregation across store folders; a workspace root shows its own folder.
- A member relocated through the machine-local member map is not matched;
  it degrades to `no specs`.
- The worktree guard's own store blind spot is unchanged.
- No Python, Node, or `git` process per render.

## Implementation

- **Config walk.** In `plugins/s/integrations/statusline.sh`, a function
  `read_key <file> <key>` returns a top-level-looking JSON string value via
  `sed -n 's/.*"<key>"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1`.
  Walk `d` from W up to `/` (`d=$(dirname "$d")` until it stops changing),
  collecting, for the first file declaring each, `store_root` + its file's
  directory, `dir`, and the directory of the first config matching
  `"workspace"[[:space:]]*:[[:space:]]*{` (the registry root). Then consult
  `$HOME/.shipd-config.json` for any key still unset when `$HOME` was not on
  the walk. `dirname` is a builtin-equivalent utility already acceptable;
  prefer `${d%/*}` parameter expansion to avoid a process.
- **Store path.** Expand a leading `~` with `$HOME`; a value not starting
  with `/` joins onto the declaring file's directory. Strip a trailing `/`.
- **Main checkout.** Walk up from W for `.git`: a directory → that dir; a
  file → read its first line, strip `gitdir: `, and when it matches
  `*/.git/worktrees/*` take everything before `/.git/worktrees/`; otherwise
  that dir. None found → W.
- **Content directory.** With a store: candidates `<store>/<main relative to
  registry root>` (only when the main checkout lies under the registry root)
  then `<store>/<basename of main>`; the first existing directory wins. With
  no store: `W/<dir or .shipd>` when it exists, and keep the `.worktrees/*`
  scan using `<dir>`. Every later path (`planned/`, `state.json`,
  `autopilot/`, epic files via each candidate's own content dir) keys off the
  resolved content directory `C` instead of `$workspace/.shipd`.
- **No content directory.** Set `spec_seg="no specs"`, call `render_lines`,
  exit 0 — the chain trap still runs. All resolution steps silence stderr.
- **`--print-content-dir`.** Parsed in the existing argument loop; after
  resolution, `printf '%s\n' "$C"` (or nothing) and exit 0 before rendering.
- **Doctor.** In `plugins/s/bin/shipd` `check_statusline`, after confirming
  a shipd registration, run `bash <PLUGIN_ROOT>/integrations/statusline.sh
  --print-content-dir` with stdin `{"workspace":{"current_dir":"<cwd>"}}`
  (5 s timeout). Compare `os.path.realpath` of its output with
  `sc.specs_dir(cwd)` when the latter exists; on mismatch warn
  `the statusline reads <script dir or "nothing"> but the engine reads
  <engine dir> — …`. Any probe failure (timeout, OSError, ConfigError) keeps
  the plain registration verdict. `check_statusline` gains an optional
  `root` parameter (default `os.getcwd()`); `check_steps` passes the root.
- **Docs.** Revise the first "Known limitations" bullet in
  `docs/workspaces/nesting-and-stores.md`: the statusline now resolves the
  store (registry path, then checkout name; member-map relocations excepted);
  the worktree guard still does not. Run
  `plugins/s/skills/document/scripts/docs_lint.py` on the file until clean.
- **Version.** Bump `plugins/s/.claude-plugin/plugin.json` one patch above
  the version the main branch carries at build time.

## Readiness attestation

### Problem and motivation

The statusline cannot see a `store_root` store and stays silent.

Evidence:

- `plugins/s/integrations/statusline.sh` exits 0 silently when
  `$workspace/.shipd` is not a directory, and scans only
  `$workspace/.shipd/planned` and `.worktrees/*/.shipd/planned`.
- `spec_common.specs_dir` returns `<store>/<repo_store_folder(root)>` when
  `store_root` is declared.
- The user's session in `~/projects/workspaces/understand` rendered nothing
  while the engine read `~/projects/workspaces/.shipd/workspaces/`.

### Scope and non-goals

Resolution, `no specs`, the doctor comparison, and one docs bullet.

Evidence:

- In scope: `statusline.sh` resolution and rendering paths,
  `check_statusline`, `docs/workspaces/nesting-and-stores.md` "Known
  limitations".
- Out of scope: `repo_store_folder`'s member-map branch, `worktree.sh`'s
  guard, cross-folder aggregation.

### Affected capabilities and files

Two capabilities; one added and four modified requirements.

Evidence:

- `statusline`: added `statusline-content-resolution`; modified
  `statusline-rendering` (base 7cd1a7dade20), `statusline-integration`
  (8e92d2ca7b4a), `statusline-chain` (5e08f0b14075).
- `shipd-cli`: `doctor-verb` (e78ea2750ed0).
- `spec_common.py` `_resolve_store_root` (relative to declaring file),
  `repo_store_folder` (registry manifest path, else main-checkout basename),
  `local_state_rules` (state.json and autopilot/ inside the content dir).

### No open task-shaping decision

Every task-shaping decision is settled.

Evidence:

- Bash resolution (approach 1), `no specs` fallback: stated by the user.
- Workspace root shows its own folder: settled by the user (Q1).
- Registry matching by probing candidate store folders rather than parsing
  the registry JSON: chosen so no JSON parser is needed per render.

## Questions and answers

### Q1: Which store folders does a workspace-root statusline show?
- **Question:** In a workspace root whose specs live in a `store_root` store
  with several per-repo folders, which changes should the statusline show?
  Options: (a) only the folder the engine resolves for that root; (b) every
  folder in the store. Recommendation: (a).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (a) — only the root's own folder, the same one `spec_status.py`
  reads.
- **Queued:** q-statusline-store-root-folder-scope
