# project-groups
Status: verified
Epic: workspace-projects
Theme: spec-engine

## Idea

The workspace registry can hold a `projects` map, but it is inert: nothing
validates its shape, nothing answers "which project owns this repo," a
brief's `Project:` line is accepted on key shape alone, and there is no way
to see the workspace you configured. The grouping layer the epic promised —
projects that focus planning — has no semantics.

This change gives projects their semantics, per the epic and the depth-path
decisions confirmed with the user:

- **Registry semantics**: `projects` maps kebab-case project slugs to objects
  whose `repos` are workspace-root-relative path strings — shape-validated,
  never existence-checked (registries travel across machines). An exact
  duplicate repo path across projects is an error (ambiguous ownership).
- **Project resolution**: `project_of(ws_root, path)` resolves ownership by
  path containment, most-specific entry winning; `None` means the implicit
  default project, which is anonymous and unreferenceable.
- **`Project:` validation on briefs**: the value must name a declared project
  slug; with no projects declared, any `Project:` line is an error.
- **`--workspace` lint mode** validating the registry, mirroring
  `--epic`/`--initiative`.
- **Two status verbs**: `workspace-show` (root, projects with repos annotated
  present/absent, `context.md` presence, initiatives with scopes, an
  implicit-default note) and `project-show <slug>` (one project's repos,
  context, scoped initiatives).
- The `projects/<slug>/context.md` convention (optional free prose, never
  linted), README docs, and the plugin bump (0.2.4 → 0.2.5).

### Non-goals

- No planning-stage consumption of projects (focusing `/s:plan` by project
  context is future work beyond this epic's members).
- No repo existence enforcement anywhere — present/absent annotations in the
  verbs are display, not validation.
- No `context.md` linting or required structure.
- No `/s:initiative` skill — that is the `initiative-skill` member.

Affected capabilities: `shipd-workspace` (one MODIFIED, three ADDED),
`shipd-spec-lint` (ADDED), `spec-status` (ADDED). Impact:
`plugins/s/skills/build/scripts/{spec_common,spec_lint,spec_status}.py` and
their tests, `am/README.md`, `plugins/s/.claude-plugin/plugin.json`.

## Implementation

- **Validation returns error strings, it does not raise.**
  `validate_workspace(registry)` in `spec_common.py` returns a list of error
  strings (empty when valid): `projects` must be an object; each slug
  kebab-case; each value an object whose `repos` is a list of non-empty
  strings; exact duplicate repo paths across projects are errors. Returning
  a list lets `spec_lint.py` wrap entries as `LintError`s and the status CLI
  print them — one implementation, two consumers. Rejected: raising
  `ConfigError` — validation findings are plural, and load-vs-validate stays
  the established seam (`load_workspace` remains tolerant).
- **`project_of(ws_root, path)`** normalizes `path` relative to `ws_root`
  and returns the slug of the project whose repo entry equals or contains
  the path, choosing the longest (most specific) matching entry; `None`
  when nothing matches. Nested entries across projects are legal and
  resolved by specificity; only exact duplicates are invalid (caught by
  `validate_workspace`, and `project_of` still picks deterministically —
  first declaration order — so display code never crashes on an invalid
  registry).
- **Brief `Project:` check extends `lint_initiative`** (and stays out of
  change/epic lint — `Project:` exists only on briefs): load the registry;
  no declared projects → error "no projects declared in the workspace
  registry"; a value outside the declared slugs → error listing them. The
  registry itself failing `validate_workspace` surfaces those errors too —
  a broken registry should not silently pass a brief.
- **`--workspace` lint mode** in `spec_lint.py`: resolves the workspace from
  `--root` like `--initiative` (non-zero "no workspace found" when absent),
  then reports `validate_workspace` findings against the registry path.
  Library and change lint remain registry-silent except through the brief
  path above.
- **Verbs in `spec_status.py`**: `workspace-show` prints the workspace root,
  each declared project with its repos (suffix `(absent)` when the path is
  not a directory on this machine) and `context: yes|no` for
  `projects/<slug>/context.md`, each initiative under `initiatives/` with
  its status and `Project:` scope, and — when the current repo resolves to
  no declared project via `project_of` — a closing `implicit default
  project` note. `project-show <slug>` prints that project's repos
  (annotated), its `context.md` presence (and first line when present), and
  the initiatives whose `Project:` equals the slug; an undeclared slug is a
  non-zero error naming the declared slugs. Both resolve the workspace like
  the initiative verbs and error without one.
- **Risk:** a registry invalid under the new rules now affects brief linting
  — accepted and intended (errors name `.shipd/workspace.json`), and
  `--workspace` gives a direct way to lint the registry itself.
