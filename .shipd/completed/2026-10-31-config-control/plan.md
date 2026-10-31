# config-control
Status: verified
Epic: shipd-init
Planned-at: 191ef2030e4fd6e5268c03e2725cc744f545098f
Gated-hash: a3d607cc4e1b

## Idea

Make the `shipd` binary the only, validating writer of `.shipd-config.json`:
one key registry, `shipd config set/unset/check`, the four existing writers
moved onto it, and the doctor's config check driven by it.

### Motivation

A user or skill changing a setting today must hand-edit JSON, and a bad value
lands silently until a later command trips on it; the `/s:init` wizard
(`init-skill`) cannot write config at all without this writer.

### Details

- New `config_registry.py`: registry, `write_layer`, layer resolution, check.
- `spec_status.py`: `config-set`, `config-unset`, `config-check` verbs.
- `bin/shipd`: `config set|unset|check` mode words; doctor `config` check.
- `init_workspace`, `workspace-project`, `worktree hooks add/remove`, and
  `shipd statusline layout` migrate.
- `statusline` joins `RECOGNIZED_CONFIG_KEYS`; `docs/customise.md` names it
  and the new verbs.

Affected capabilities: `shipd-config`, `spec-status`, `shipd-cli` (all added).

### Non-goals

- No change to how config is read beyond an optional override argument.
- The member-map writers keep their own writers.
- No `shipd init status` verb or `/s:init` skill (members `init-status`,
  `init-skill`).

## Implementation

- **Module.** `plugins/s/skills/build/scripts/config_registry.py` holds
  `KeySpec(key, validate, hint, layer, owner)`, `REGISTRY` per
  `artefacts/registry.md`, `Finding(level, path, key, message, hint)`,
  `ConfigWriteError(sc.ConfigError)` with `.findings`, `write_layer(path,
  data, anchor=None)` (anchor defaults to `dirname(path)`; returns
  unknown-key warning findings),
  `layer_path(root, key, layer=None)`, `set_key`, `unset_key`, `check(root)`.
  It imports `spec_common` at top; `spec_common.init_workspace` imports it
  lazily, the existing `pipeline_schema` pattern. Rejected: the registry
  inside `spec_common.py` — that file is already ~3,000 lines.
- **Accessor cores.** In `spec_common.py`, split `resolve_pr_mode`,
  `resolve_pipeline`, `resolve_pr`, `resolve_room`, `resolve_merge` into
  `<name>_from_config(config, prov)` cores the root wrappers call unchanged;
  add `absolute_path_value(key, raw)` used by `memory_store_dir`,
  `wiki_base_dir`, `_workspaces_root_from_config` with their current messages.
  A validator calls a core with `{key: value}` and `{key: <path>}`.
- **Merged view.** `load_layered_config(start, override=None)` and
  `resolve_config(start, override=None)`; `override=(path, data)` substitutes
  `data` for that file (absent or not). Default `None` keeps every read as is.
- **Validation and output.** Per `config-layer-writer` and the two verb
  requirements. Rejection lines are lowercase `error:`/`hint:` findings (the
  epic's grammar), not the single `Error:` fatal line, which stays for an
  unreadable file or a missing workspace. Hints come verbatim from the table;
  unknown keys use `difflib.get_close_matches(key, REGISTRY, n=1, cutoff=0.6)`
  → `did you mean <key>?`, else `run shipd config to see the keys in effect`.
  An unchanged invalid key is also an error (Q4), hinted `fix it with shipd
  config set <key> <value> or shipd config unset <key>`.
- **Repo layer.** `git -C <root> rev-parse --show-toplevel`, falling back to
  `abspath(root)`.
- **Migration.** `init_workspace` and `worktree._write_root_config` call
  `write_layer`; `workspace-project` keeps its `validate_workspace` pre-check
  and message, then calls `write_layer(cfg_path, data, ws_root)`.
- **Statusline.** `STATUSLINE_SEGMENTS` and `_validate_layout` move from
  `bin/shipd` into `config_registry.py`, messages unchanged.
  `statusline_from_config(entry, path)`, the row's validator, raises the text
  `_load_statusline_layout` prints today. `_save_statusline_layout` calls
  `write_layer(path, data)`; a refusal prints `error:`/`hint:` and exits 1.
- **Doctor.** `check_config` in `bin/shipd` calls `config_registry.check`,
  per `doctor-config-registry-check`; the `config` remedy text becomes `fix
  with shipd config set / shipd config unset`.

Risk: per-layer checking now fails doctor on a shadowed bad outer value that
passed before; intended, since the value is still wrong in its file.

## Questions and answers

### Q1: How are keys outside the registry treated?
- **Question:** Options: (1) `set` rejects with a did-you-mean, `check` warns,
  `statusline` is externally owned and keeps its writer; (2) register
  `statusline` and migrate `statusline layout`; (3) every unknown key errors.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 2: register `statusline` (owner `shipd statusline
  layout`) and migrate that verb. Other unknown keys behave as in option 1.
- **Queued:** q-config-unregistered-keys

### Q2: Which default layer do the unassigned keys get?
- **Question:** Options: (1) user for `workspaces_root`, `model`, `models`,
  `room`; workspace for `workspace`, `clone_sources`; repo otherwise; (2) repo
  for all; (3) user for all.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1 (the user accepted the recommendation). Machine and
  person settings go to the user layer, registry settings to the workspace,
  project settings to the repo.
- **Queued:** q-config-default-layers
- **Relied on by:** init-skill

### Q3: How does `config set` parse its value?
- **Question:** Options: (1) JSON when it parses, else a plain string;
  (2) JSON only; (3) per-key coercion.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1 (the user accepted the recommendation), so `set
  pr-mode draft` and `set voice false` both work unquoted.
- **Queued:** q-config-set-value-parsing
- **Relied on by:** init-skill

### Q4: Does an unrelated invalid key block a write?
- **Question:** Options: (1) proceed, printing it as a warning; (2) refuse
  until every key is valid.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 2: refuse while the merged result holds any invalid
  key, naming the fix. Fixing that key succeeds; unknown keys only warn.
- **Queued:** q-config-write-unrelated-errors

## Readiness attestation

### Problem and motivation

Config is hand-edited with no validation, and the planned wizard needs a writer.

Evidence:

- Epic `shipd-init` Introduction and Decision "The binary is the only config
  writer".
- Three hand-rolled writers: `spec_common.py:2070-2075`,
  `spec_status.py:4630-4638`, `worktree.py:443-449`.

### Scope and non-goals

Registry, writer, verbs, migration, doctor, and the `statusline` row; reading
stays out.

Evidence:

- Epic non-goals; `RECOGNIZED_CONFIG_KEYS` at `spec_common.py:407-434`.
- `bin/shipd:1757-1771` writes `statusline` into `~/.shipd-config.json`; it
  moves onto `write_layer` per Q1.
- The epic's "No new config keys" covers unwritten keys; the engine already
  writes `statusline`.

### Affected capabilities and files

Three capabilities gain requirements; seven files and five test files
change.

Evidence:

- `shipd-config`, `spec-status`, `shipd-cli`; ADDED only, since restating
  `cli-dispatch` (30 scenarios) would overflow the delta budget.
- Files: `config_registry.py` (new), `spec_common.py`, `spec_status.py`,
  `worktree.py`, `bin/shipd`, `docs/customise.md`,
  `references/shipd.config.example.json`.
- Ran `shipd config set pr-mode bogus` → exit 2, argparse "unrecognized
  arguments" (no verb yet).
- Ran `shipd worktree hooks add "echo hi"` → exit 0, `post-worktree-scripts:
  added echo hi (<repo>/.shipd-config.json)`; `remove 0` leaves `[]`.
- Ran `workspace-project add demo demo/repo` → exit 0, `demo: demo/repo`.
- Ran `shipd doctor` with `"pr-mode": "bogus"` → `fail config` carrying the
  accessor message.

### No open task-shaping decision

The user answered Q1 to Q4; module, layer, and output choices come from the
epic and the code.

Evidence:

- Q1 to Q4 above; the `error:`/`hint:` grammar and default layers for seven
  keys come from the epic's Decisions.
