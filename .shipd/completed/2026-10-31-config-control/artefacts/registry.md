# Config key registry table

One row per `spec_common.RECOGNIZED_CONFIG_KEYS` member. `config_registry.REGISTRY`
carries exactly these rows. "Validator" names the check the entry runs on a
declared value; "Hint" is the entry's one-line `hint:` text, printed verbatim;
"Owner" is set only on keys `config set`/`config unset` refuse, and the refusal's
hint reads `use <owner>`.

| Key | Default layer | Validator | Hint | Owner |
| --- | --- | --- | --- | --- |
| `autonomous-pipeline` | repo | `sc.pipeline_from_config` | a preset name (basic, default, eco) or a list of stage entries | |
| `build` | repo | a JSON object | an object of /s:build settings, e.g. {"parallelism": 3} | |
| `clone_sources` | workspace | `sc.resolve_clone_sources` | a list of directory paths | |
| `completed_retention_days` | repo | a non-negative integer (not a boolean), or null | a non-negative number of days; 0 or null disables retention | |
| `dir` | repo | `sc.specs_dirname` | a relative path such as .shipd | |
| `guardrails` | repo | `false`, or an object whose optional `disable` is a list of non-empty strings | false, or an object such as {"disable": ["<rule>"]} | |
| `lint` | repo | an object; optional `run_scripts` a boolean, optional `disable` a list of non-empty strings | an object with run_scripts (true or false) and disable (a list of linter names) | |
| `memory_dir` | user | `sc.absolute_path_value` | an absolute path such as ~/.shipd-memory | |
| `merge` | repo | `sc.merge_from_config` | an object with approvals, dismiss_stale, last_push_approval, required_checks, strict, thread_resolution | |
| `model` | user | `sc.resolve_model_base` | a non-empty model id | |
| `models` | user | `sc.resolve_models` | an object mapping effort levels to model ids | |
| `post-worktree-scripts` | repo | a list of non-empty strings | a list of shell command lines | `shipd worktree hooks add` |
| `pr` | repo | `sc.pr_from_config` | an object with title (containing {summary}) and ticket_pattern (a regular expression) | |
| `pr-mode` | repo | `sc.pr_mode_from_config` | accepted values: auto, draft | |
| `room` | user | `sc.room_from_config` | an object with agent (a non-empty string) and max_rounds (an integer of at least 1) | |
| `statusline` | user | `config_registry.statusline_from_config`: an object whose `lines` is a non-empty list of non-empty segment lists, each segment one of `STATUSLINE_SEGMENTS` and used once | an object such as {"lines": [["spec", "context"]]}; segments: spec, directory, context | `shipd statusline layout` |
| `store_autocommit` | repo | a boolean | true or false | |
| `store_root` | repo | a non-empty string | a path to the external store root | |
| `store_sync` | repo | a boolean | true or false | |
| `valid_themes` | repo | a list of non-empty strings | a list of theme slugs | |
| `voice` | user | a boolean | true or false | |
| `wiki_base` | user | `sc.absolute_path_value` | an absolute path to the base wiki store | |
| `workspace` | workspace | a JSON object with no `sc.validate_workspace` errors | an object declaring the workspace registry | `shipd workspace init` |
| `workspaces_root` | user | `sc.absolute_path_value` | an absolute path such as ~/projects | |
| `worktree_idle_minutes` | repo | a non-negative integer (not a boolean) | a non-negative number of minutes; 0 disables the guard | |
| `worktree_stale_days` | repo | a positive integer (not a boolean) | a positive number of days | |
| `worktree_sweep` | repo | a boolean | true or false | |

Comment keys — any top-level key starting with `//` — are skipped by every check.
