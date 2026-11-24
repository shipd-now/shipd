# store-env-override
Status: verified
Planned-at: c938fcbcfabf09ae41549d7e931f720b87f451d4
Gated-hash: 99fa87178c46

## Idea

Let the environment override `store_autocommit` and `store_sync` over every
config layer.

### Motivation

An external harness that runs the engine headless inside sandboxed jobs owns
its own commits and pushes. It must turn the engine's auto-commit and delayed
push off whatever the repo or the user's home config declares, without
replacing HOME, which would lose `workspaces_root`, `memory_dir`, `~` paths,
and the git identity.

### Details

- `SHIPD_STORE_AUTOCOMMIT` and `SHIPD_STORE_SYNC` force the matching key.
  `0`, `false`, `no`, `off` force false; `1`, `true`, `yes`, `on` force true,
  case-insensitive. Unset or any other value uses the config as today.
- The override sits inside `store_autocommit_enabled` and
  `store_sync_enabled`, so every reader gets it: the auto-commit, the
  delayed push scheduler, the session hook, autopilot's store fetch.
- The personal memory store honours it too. It goes through the same
  `wiki_autocommit`, and the environment belongs to the process owner, so the
  rule that no repository can silence memory commits still holds.
- `config-show` prints `store-autocommit:` and `store-sync:` lines with the
  effective value, marked `(environment <NAME>)` when the override decided it.
- The registry descriptions, the config example, and the docs name both
  variables.

Affected capabilities: `shipd-config` (modified). Impact: `spec_common.py`,
`spec_status.py`, `config_registry.py`, the config example, three docs, tests,
and the plugin version. No new dependency.

### Non-goals

- No new config key and no change to the delay key.
- No override for `store_push_delay`.

## Implementation

`spec_common.store_env_override(name, env=None)` returns True, False, or None.
Both `*_enabled` functions call it first and return a non-None result.
`cmd_config_show` prints the two lines. Bump `plugin.json` from 0.6.386 to
0.6.387.

## Readiness attestation

### Problem and motivation

A harness cannot disable the engine's store git without editing config.

Evidence:

- `plugins/s/skills/build/scripts/spec_common.py` `store_autocommit_enabled`
  and `store_sync_enabled` read only the resolved config.

### Scope and non-goals

Two functions, one verb's output, descriptions, and docs.

Evidence:

- `plugins/s/skills/build/scripts/spec_common.py` `wiki_autocommit` and
  `schedule_store_push` call those functions; no other reader of the keys
  exists outside `store_sync.py` and `autopilot.py`, which call them too.

### Affected capabilities and files

One capability, requirement `store-sync-keys` (modified).

Evidence:

- `.shipd/verified/shipd-config/spec.md` requirement `store-sync-keys`.
- `plugins/s/.claude-plugin/plugin.json`

### No open task-shaping decision

Value forms, precedence, and the memory-store choice are fixed above.

Evidence:

- `plugins/s/skills/build/scripts/spec_common.py` `wiki_autocommit` is the one
  commit path, and the memory store's call sites already skip the push.
