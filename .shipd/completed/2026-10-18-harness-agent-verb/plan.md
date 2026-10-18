# harness-agent-verb
Status: verified
Epic: harness-agents
Theme: developer-experience
Planned-at: 1c2412156039feacdae88e7e9c59004ad2dc67a4
Gated-hash: f593d00961fd

## Idea

Write, remove, and report the generated agent files beside the command files:
`shipd install` and `harness add`/`remove`/`status` gain the agent surface with
the same ownership markers, idempotent refresh, and `--force` semantics.

### Motivation

The agents are renderable but nothing writes them, so a user who runs
`shipd install` or `shipd harness add` on OpenCode, Antigravity CLI, or
oh-my-pi still receives no agents and `/s:build`'s delegation names a file that
was never created. The write surface is the step between the render and a user
actually having the agents.

### Details

- `harness_generate.py`: `agent_paths(entry, mode, root)` and
  `_agent_payloads(entry, mode, root, base_dir)`, wired into `planned` (so
  `add` and `shipd install` write them), into `remove`'s candidate list, and
  into `_entry_state` (so `status` counts them).
- `plugins/s/bin/shipd`: `harness show` prints the entry's `agent` member.
- `test_harness_generate.py`: the agent files are written, refreshed
  idempotently, removed, and reported, and a foreign agent file is refused
  without `--force`.
- `plugins/s/.claude-plugin/plugin.json`: the version bump this change owes.

Affected capabilities: `harness-verb` (modified). Impact: no new dependency;
`shipd install` gains the agent files through its existing `hg.add` call, and a
harness with no agent surface is unchanged.

### Non-goals

- No new render logic: `render_agent` and the agent path helpers already exist.
- No change to the generated bodies or the Claude skills; that is the
  `harness-agent-delegation` member.
- No new registry data and no change to the neutral source.
- No documentation.

## Implementation

- **Agents ride the existing write pipeline, not a parallel one.** The
  command surface already flows through one `planned` → `add` → `remove` →
  `_entry_state` chain, and `shipd install` calls `hg.add` directly, so the
  agent files join that chain as extra payloads rather than as a second writer.
  `_agent_payloads(entry, mode, root, base_dir)` resolves to one
  `(path, render_agent(entry, role))` pair per `AGENT_ROLES` member for a
  harness with an agent surface, and to `[]` otherwise. Rejected: a separate
  agent-only action — two writers would drift on ownership and idempotence.
- **`add` and `remove` inherit the ownership rules for free.** Because the
  agent files become payloads and candidates, the existing marker check, the
  byte-compare-before-write idempotence, the `--force` refusal on a foreign
  file, and the empty-directory pruning all apply without new code. The agent
  files carry the ownership marker by construction (`render_agent` emits it).
- **`status` counts the agent files.** `_entry_state`'s `expected`/`present`
  and its currency check read the same payloads, so a harness is `installed`
  only when its command *and* agent files are byte-current, and `stale` when
  an agent file is missing or edited. A harness with no agent surface is
  unchanged.
- **`shipd install` needs no edit.** `install_tui` writes the confirmed
  selection through `hg.add(generated, hg.USER_MODE)`, so the agent files land
  for every selected harness with an agent surface the moment `planned` emits
  them. The install TUI's own selection logic is untouched.
- **`harness show` prints the agent member.** `HARNESS_FIELDS` gains `agent`,
  and `_harness_field` renders a dict as its `repo_pattern` (or `none`), so a
  `show` line stays one line like every other field.
- **The version bump rides here.** `plugin.json` moves `0.6.322` → `0.6.323`.

Risk: writing a new directory (`.claude/agents/`, `.opencode/agents/`) means
`remove` may prune a directory a user also keeps their own agents in; the
prune stops at the first non-empty directory and at the surface boundaries, so
a shared directory with a user's own file is left alone.

## Readiness attestation

### Problem and motivation

The agents are renderable but never written, so a user on OpenCode,
Antigravity CLI, or oh-my-pi still receives no agents and `/s:build`'s
delegation names a file that does not exist.

Evidence:

- Epic `harness-agents` Introduction: those harnesses "are told to spawn an
  executor that does not exist".
- `harness_generate.py`'s `planned` emits command and reference payloads only;
  no action writes an agent file.

### Scope and non-goals

The write, remove, and report path for agent files, its tests, and the version
bump; rendering, the bodies, and the skills stay out.

Evidence:

- In scope: `harness_generate.py`, `plugins/s/bin/shipd`,
  `test_harness_generate.py`, `plugins/s/.claude-plugin/plugin.json`.
- Out of scope: the epic assigns the bodies and skill naming to
  `harness-agent-delegation`.

### Affected capabilities and files

One capability, `harness-verb`, modified; three edited files plus the version
bump.

Evidence:

- Capability `harness-verb`: `harness-add-remove` (base 4ae6182f05a3) and
  `harness-status` (base 415251f33c08) modified.
- Edited: `harness_generate.py`, `plugins/s/bin/shipd`,
  `test_harness_generate.py`, `plugins/s/.claude-plugin/plugin.json`.
- Runnable premise: `python3 -m unittest discover -s
  plugins/s/skills/build/tests -p 'test_harness_generate.py'` → exit 0, 77
  tests OK; `shipd harness add cursor --root <tmp>` writes only
  `.cursor/commands/` today.

### No open task-shaping decision

Every task-shaping decision is settled by the epic and by the existing write
pipeline; none needed the user.

Evidence:

- The write/remove/status shape, the ownership rules, and the idempotence: all
  settled by `harness_generate.py`'s existing `planned`/`add`/`remove`/
  `_entry_state` chain.
- `shipd install`'s coverage: settled by `install_tui`'s existing `hg.add`
  call.
- The member split and the ids: settled by the epic's Decisions and Changes
  table.
