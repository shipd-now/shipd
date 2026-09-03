# shipd-worktree-hooks

### Requirement: Worktree-hooks setup flow
id: worktree-hooks-setup-flow

The `s:worktree-hooks` skill SHALL turn a described setup need into a
registered post-worktree script: author the script file at
`<content-dir>/hooks/<slug>.sh` in the repo checkout (resolving the directory
name from the `dir` config key and never relocating it via `store_root`,
so the script is checked in and travels with every worktree), mark it
executable, register its repo-relative path through the binary's
`worktree hooks add` verb — never by hand-editing `.shipd-config.json` — and
verify the registration by reading `worktree hooks list` back. Where the
requested step is a plain one-line command, the skill MAY register the
command line directly without authoring a script file. The skill SHALL
resolve the binary as `shipd` on `PATH`, falling back to
`${CLAUDE_PLUGIN_ROOT}/bin/shipd`.

#### Scenario: Described step becomes a registered script
- **WHEN** the user asks for a `.env` file copied into each new worktree
- **THEN** the skill writes an executable script under `.shipd/hooks/`,
  registers its repo-relative path via `worktree hooks add`, and reports the
  listing that proves the registration

#### Scenario: One-line command registers directly
- **WHEN** the user asks for `npm install` after each worktree creation
- **THEN** the skill registers that command line via `worktree hooks add`
  without authoring a script file

### Requirement: Worktree-hooks browse and removal
id: worktree-hooks-browse-remove

When invoked to inspect, the skill SHALL report the registered hooks from
`worktree hooks list`, flagging any registered script path that does not
exist in the checkout. When invoked to remove a hook, the skill SHALL name
the matching entry, obtain the user's confirmation first, and only then run
`worktree hooks remove`, deleting the authored script file as well when the
entry pointed at one under `<content-dir>/hooks/` and the user confirmed
that deletion.

#### Scenario: Listing flags a dangling script
- **GIVEN** a registered item `.shipd/hooks/seed.sh` whose file was deleted
- **WHEN** the skill lists the hooks
- **THEN** the report shows the item and flags that its script file is
  missing

#### Scenario: Removal is confirmed first
- **WHEN** the user asks to remove the database-seed hook
- **THEN** the skill names the matching entry and awaits confirmation before
  running `worktree hooks remove`
