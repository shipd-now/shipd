<!-- doc-type: reference -->

# Harness agents reference

A harness's **agent surface** is the agent definitions shipd writes beside its
command files. Only a harness whose registry entry declares the `subagents`
feature has one. [Customising shipd](customise.md) covers the registry and the
command surface.

## What ships

`shipd install` and `shipd harness add <name>` write one agent file per shipd
role into the harness's own agent location. Each file carries the same
ownership marker, idempotent refresh, and `--force` refusal on a foreign file
as its command files. A harness that declares no `subagents` receives none.

| Harness | Repository location | User-global location | Frontmatter |
| --- | --- | --- | --- |
| Claude Code | `.claude/agents/shipd-<role>.md` | `~/.claude/agents/` | `name`, `description` |
| OpenCode | `.opencode/agents/shipd-<role>.md` | `~/.config/opencode/agents/` | `description`, `mode: subagent` |
| Antigravity CLI | `.agents/agents/shipd-<role>.md` | `~/.gemini/config/agents/` | `name`, `description`, `subagent: true` |
| oh-my-pi | `.omp/agents/shipd-<role>.md` | `~/.omp/agent/agents/` | `name`, `description` |

`<role>` is one of the three ids below. Every agent file opens with the
harness's frontmatter block, then shipd's ownership marker, then the role's
system prompt.

## The roles

| Id | Role |
| --- | --- |
| `shipd-sub-agent` | The execution worker a `/s:build` delegates its tasks to. |
| `shipd-validator` | The adversarial validator a build spawns to refute each scenario. |

## The verbs

```bash
shipd harness add claude-code --root .    # the repository-level agent files
shipd harness add claude-code --user      # the user-global agent files
shipd harness status claude-code --json   # installed, stale, foreign, or absent
shipd harness remove claude-code --user   # delete them and prune the directory
```

When you install and enable the `s@shipd` plugin at user scope, `shipd
harness add claude-code --user` skips the user-global agent files. It also
retires the ones shipd wrote earlier.

`status` counts the agent files with the command files. A harness is
`installed` only when both are byte-current, and `stale` names the first
missing or differing file. `shipd harness show <name>` prints the entry's
`agent` member, its agent repo pattern.

## Adding a harness

1. Add the harness's registry entry with its agent `repo_pattern`, `user_dir`,
   `dialect`, `frontmatter`, and `extra` fields, and `subagents` among its
   `features`.
2. Confirm `shipd harness show <name>` prints the agent repo pattern.
3. Run `shipd harness add <name> --root <dir>` and check the agent files land
   where that harness reads them.

A harness that declares no `subagents` carries no `agent` member and receives
no agent files.
