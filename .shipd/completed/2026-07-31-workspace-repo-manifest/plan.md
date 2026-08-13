# workspace-repo-manifest
Status: verified
Epic: portable-workspaces

## Idea

Widen the workspace registry into the portable-workspace manifest: per-repo
clone metadata, an explicit focus project, and a workspace-init option that
seeds the root as a git repo.

### Motivation

The portable-workspaces epic makes a workspace a clonable git repo whose
manifest tells any machine which member repos to materialize and which
project the job centers on — but today's registry can only name paths, and
workspace-init cannot produce a git-ready root.

### Details

- Registry `repos` entries widen: a path string (today's form, unchanged) or
  an object `{path, url?, branch?}`; validation stays shape-only.
- The workspace object gains optional `focus: <project-slug>`, which must
  name a declared project (same-file consistency; disk never consulted).
- `workspace-init` gains `--git`: git-init the target when needed and seed a
  marked member-repos `.gitignore` block.
- `workspace-show` prints the focus and marks entries carrying a clone URL.

Affected capabilities: `shipd-workspace`, `spec-status` (modified). Impact:
`plugins/s/skills/build/scripts/spec_common.py`, `spec_status.py`, their
tests, plugin version. `spec_lint --workspace` inherits the new validation
for free (it wraps `validate_workspace`).

### Non-goals

- No materialization or drift logic — `workspace-sync-plan` is the next
  member; this change never clones, fetches, or walks the ladder.
- No maintenance of the gitignore member block — the sync member owns it;
  init only seeds an empty marked block.
- No registration verb: the registry remains hand-edited JSON.
- No wiki changes (`wiki_base`, auto-commit are separate members).

## Implementation

- **Entry shape.** A repos entry is either a non-empty string (the path) or
  an object with required non-empty string `path` and optional non-empty
  string `url` and `branch`; anything else is a shape error naming the
  project. A module-level helper `repo_entry_path(entry)` returns the path
  for either shape (or `None` when malformed) and is used by
  `validate_workspace`, `project_of`, and the show verbs — one reader, no
  drift. Duplicate-path detection compares resolved paths across both
  shapes. Rejected: url at the project level — a project may span repos
  with different remotes.
- **Focus.** `validate_workspace` checks `focus` when present: kebab-case
  and naming a declared project slug, else an error. This is same-file
  consistency — the manifest travels as one document — so the
  never-existence-checked rule for disk paths is untouched.
- **Init `--git`.** `init_workspace(path, git=False)`: when `git` is true
  and `git rev-parse --is-inside-work-tree` fails at the target, run
  `git init`; then ensure `.gitignore` contains the marked block
  (`# >>> shipd-workspace members` / `# <<< shipd-workspace members`), appending
  an empty block only when the markers are absent (idempotent). Local git
  only — no network, per the constitution. The CLI verb passes `--git`
  through. Rejected: always git-init — a workspace inside an existing repo
  checkout must not be re-rooted silently.
- **Show.** `workspace-show` prints `focus: <slug>` after the root line when
  declared, and annotates repo lines carrying a URL with `[url]` alongside
  the existing absent-on-disk annotation. `project-show` reads paths via the
  same helper.
- **Risks.** Widened entries reaching old readers — guarded by routing every
  reader through `repo_entry_path` in this change; registries written by
  this version remain readable by older code only if they avoid the new
  shapes, which is acceptable (manifests are forward-looking).
