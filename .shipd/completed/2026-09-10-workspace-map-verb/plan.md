# workspace-map-verb
Status: verified

## Idea

The member map gets an engine-owned writer — `workspace-map` list/set/remove
verbs on the status CLI — and a guided `/s:workspace map` skill verb that
interviews per member and drives them, so the machine-local map is never
hand-authored.

### Motivation

`load_repo_map` shipped with no writer: mapping a member means hand-editing
`.shipd-workspace.local.json`, against the workspace tooling's own rule that
declarations are written by engine verbs, never by hand (the setup skill's
existing contract). The map is only as usable as the verb that maintains it.

### Details

- New status-CLI verbs: `workspace-map` (list the map with per-entry
  resolution), `workspace-map set <member-path> <local-path>`, and
  `workspace-map remove <member-path>` — validated against the manifest,
  preserving unknown file content, ensuring the map file is gitignored at
  the workspace root on first write.
- New `/s:workspace map` skill verb: reads the sync plan, proposes mapping
  candidates for each member (existing checkouts found via the
  `clone_sources` scan, or a user-supplied path), asks once, and drives
  `workspace-map set` per accepted member. `sync` stays question-free.

Affected capabilities: `shipd-workspace` (one added requirement, one
modified). Impact: `plugins/s/skills/build/scripts/spec_status.py`,
`plugins/s/skills/build/scripts/spec_common.py` (write helper),
`plugins/s/skills/build/tests/test_spec_status.py`,
`plugins/s/skills/workspace/SKILL.md`, `docs/workspaces.md`,
`plugins/s/.claude-plugin/plugin.json` (version bump). Stdlib-only.

### Non-goals

- No reverse lookup — that is the `workspace-reverse-lookup` change; the
  two are independent and either can land first.
- No interview inside `sync` or `clone` — their question-free unattended
  contract stands; the interview is the new `map` verb's alone.
- No writing of the repo-side `workspace_root` pointer key — the verbs
  touch only the workspace root's `repos` map; a `workspace_root` key
  already present in the file is preserved byte-for-byte.
- No map schema change and no doctor check.

## Implementation

- **Verb surface.** `workspace-map` resolves the workspace from the cwd
  (the standard no-workspace error otherwise). Bare form lists each entry
  as `<member-path> -> <value> (<resolved absolute>)` plus the existing
  unknown-key note; `set` requires `<member-path>` to be a declared
  manifest member path (error naming the declared paths otherwise) and
  stores `<local-path>` verbatim (a `~` or relative value is resolved at
  read time by `member_dest`, so what the user typed is what the file
  says); `remove` deletes the entry, erroring when absent. `set` warns —
  never errors — when the target does not exist or is not a git work
  tree, matching the planner's report-don't-repair stance. Rejected:
  blocking `set` on a missing target — pre-declaring a checkout you are
  about to move into place is legitimate.
- **The writer.** A `save_repo_map(ws_root, repos)` helper in
  `spec_common.py` beside `load_repo_map`: reads the existing file
  raw (or `{}`), replaces only the `repos` key, preserves every other
  top-level key (`workspace_root` included), writes pretty-printed JSON
  with a trailing newline. Malformed existing file → the load's own
  `ConfigError` propagates; `set`/`remove` never repair a broken file.
- **Gitignore ensure.** On the first successful `set` (and only `set`),
  ensure `<ws_root>/.gitignore` carries a `.shipd-workspace.local.json`
  line — appended outside the marked member block, idempotent, created
  with the file when absent. Rejected: putting it inside the marked
  member block, which the sync reconciler rewrites to exactly the
  manifest's member paths and would drop it.
- **Skill verb.** `plugins/s/skills/workspace/SKILL.md` gains `map` in
  its dispatch: run `workspace-sync --json` for the member list, propose
  candidates — for each unmapped member, an existing local checkout whose
  origin matches the member url (reusing the planner's `clone_sources`
  candidate scan, surfaced from the plan's `source` field) or a
  user-typed path — in a single question round; drive
  `workspace-map set` for each accepted member and finish by reporting
  the map list. Members already mapped are reported, not re-asked. The
  skill never edits the file itself.
- **Docs.** `docs/workspaces.md`'s member-map section gains the verbs and
  the skill flow.
- **Version bump.** `plugins/s/.claude-plugin/plugin.json` to the next
  patch after what main carries at build time (`0.6.199` observed at
  planning; the supersession gate reconciles if it moved).
- **Risk.** Two sessions writing the map concurrently last-write-wins;
  acceptable for a machine-local convenience file — the list verb makes
  the current state one command away.
