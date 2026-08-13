# workspace-init
Status: verified

## Idea

Every workspace-dependent verb dead-ends on "no workspace found" with no
remedy: `/s:initiative` reports the CLI's no-workspace error verbatim and
stops, and creation is an unowned capability — no CLI verb writes the
`.shipd/workspace.json` marker and no skill guides setup, so a user who
wants initiatives must hand-author the marker from folklore.

This change makes workspace creation owned and guided:

- An engine helper plus a `workspace-init <path>` verb on the status CLI that
  writes the minimal marker (`{}`) and refuses when a workspace is already
  discoverable from the target.
- A new `/s:workspace` skill with `init` (guided setup driving the verb) and
  `show` (roster via `workspace-show`) verbs.
- `/s:initiative`'s no-workspace stop now points the user at
  `/s:workspace init` instead of leaving them stranded.
- AGENTS.md skill roster and onboarding mention; plugin version 0.2.9.

### Non-goals

- No registry seeding: init writes `{}` — no `projects` map, no `initiatives/`
  scaffold; both appear lazily, as today.
- No nested-workspace support: init refuses when any root is already
  discoverable; deliberate nesting stays a hand edit.
- No change to CI-safe lint behavior: linting with no workspace still skips
  initiative-reference checks silently.
- `/s:initiative` does not run setup inline — it names `/s:workspace init`
  and stops, writing nothing.

Affected capabilities: `shipd-workspace` (modified — engine initialization and
the new setup skill), `spec-status` (modified — new verb), `shipd-initiative`
(modified — no-workspace pointer). Impact:
`plugins/s/skills/build/scripts/spec_common.py`,
`plugins/s/skills/build/scripts/spec_status.py`, their tests under
`plugins/s/skills/build/tests/`, new `plugins/s/skills/workspace/SKILL.md`,
`plugins/s/skills/initiative/SKILL.md`, `AGENTS.md`,
`docs/onboarding/05-scaling.md`, `plugins/s/.claude-plugin/plugin.json`.

## Implementation

- **Creation lives in the engine, the skill drives it.** `init_workspace(path)`
  in `spec_common.py` (stdlib only, per the constitution), exposed as the
  `workspace-init` verb in `spec_status.py`. Rejected: the skill hand-writing
  the JSON — it breaks the skills-wrap-CLIs rule and leaves creation unspecced
  in the engine.
- **Explicit target path, not `--root` resolution.** `workspace-init` takes a
  positional `<path>` (absolute, or relative to the cwd): init's whole premise
  is that no workspace resolves, so the target must be stated. The target must
  be an existing directory; init creates only the `.shipd/` subdirectory and
  the marker file, guarding against typo-created directory trees. Marker
  content is exactly `{}` plus a trailing newline.
- **Refusal guard.** If `find_workspace_root(target)` returns a root, error
  naming that existing root and exit non-zero, writing nothing. Rationale:
  nearest-ancestor discovery means a nested marker silently re-roots every
  directory beneath it — shadowing must be a deliberate hand edit.
- **Skill requirements join the existing `shipd-workspace` capability** rather
  than a new `shipd-workspace-skill` capability: the skill's name matches the
  capability, and a `-skill` suffix would be a naming wart. (Acknowledged
  precedent tension: other skills own their `am-<name>` capability outright;
  here engine and skill workspace concerns share one.)
- **`/s:workspace init` flow.** When a workspace is already discoverable,
  report its root and stop — nothing to create. Otherwise ask one
  AskUserQuestion for the target root, offering the repository's parent
  directory first (recommended — a workspace groups repos) and the repository
  root itself as the alternative, then run `workspace-init` and report the
  created root. `show` wraps `workspace-show` and reads only.
- **`/s:initiative` keeps stop semantics.** The no-workspace path still
  reports the CLI error verbatim and writes nothing; it now additionally names
  `/s:workspace init` as the setup path. Rejected: inline setup from the
  initiative skill — dedicated ownership was chosen explicitly.
- **Version bump to 0.2.9** in `plugins/s/.claude-plugin/plugin.json`, same
  PR, per the cache-snapshot rule in AGENTS.md.

Risks: a stale plugin snapshot keeps sessions on the old skills — guarded by
the version bump plus the `claude plugin update` convention. A created marker
later hand-corrupted is already handled: `load_workspace` errors clearly,
naming the file. The refusal guard inherits `find_workspace_root`'s
no-git-assumptions contract, so running init inside any parent workspace
(related or not) correctly refuses.
