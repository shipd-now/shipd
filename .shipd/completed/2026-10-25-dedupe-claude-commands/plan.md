# dedupe-claude-commands
Status: verified
Epic: context-budget
Planned-at: 77880ceb04902914a42c88ccabe37f372b59eaa9
Gated-hash: ec760d2a7123

## Idea

Stop the harness generator from writing the claude-code user-global command and
agent files when the `s@shipd` plugin is installed, and retire the
marker-owned copies already on disk.

### Motivation

Every Claude Code session with the plugin at user scope lists each shipd
command twice, as `s:*` and `shipd:*`, so the duplicates spend context and
crowd real skill descriptions out of the listing. Users cannot avoid this,
because `shipd install` writes `~/.claude/commands/shipd/` whenever they pick
Claude Code.

### Details

- `harness_registry.py`: a data map `PLUGIN_PROVIDED` naming the plugin that
  provides a harness's user surface (`claude-code` → `s@shipd`).
- `harness_generate.py`: `plugin_installed`, `plugin_provided`; `add`
  skips and retires a plugin-provided surface; `status` reports it.
- `install_tui.py`: reports a plugin-provided harness as `provided`.
- Tests in `test_harness_registry.py`, `test_harness_generate.py`,
  `test_install_tui.py`; docs in `docs/customise.md` and
  `docs/harness-agents-reference.md`; plugin version bump.

Affected capabilities: `harness-verb`, `harness-registry`, `install-tui`
(all modified). Repo mode is unchanged.

### Non-goals

- No change to repo mode (`--root`) or to `shipd harness remove`.
- No change to any other harness, including project-scope plugin installs.
- No override flag to write the files anyway (Q3).
- No `shipd doctor` check and no SessionStart cleanup (Q4).
- No change to the shared reference files.
- No checked-in context ceiling; the `/context` reading is the only
  measurement (Q5, Q6).

## Implementation

- **Registry data.** In `harness_registry.py`, beside
  `LEGACY_USER_PATTERNS`, add `PLUGIN_PROVIDED = {"claude-code": "s@shipd"}`
  with a comment: a harness whose user surface a Claude Code plugin already
  provides. A module constant, not a new entry key, so the entry key
  invariants stay as they are.
- **Detection** (Q2). `harness_generate.plugin_installed(plugin_id) -> bool`
  is true only when both hold: `~/.claude/plugins/installed_plugins.json`'s
  `plugins[plugin_id]` is a list holding a dict whose `scope` is `"user"`,
  and `~/.claude/settings.json`'s `enabledPlugins[plugin_id]` is `True`.
  A missing, unreadable, or malformed file, or any other shape, returns
  `False`, so the files keep being written. Paths expand `~` at call time.
  Offline, no subprocess. Rejected: any-scope entries (a project install
  does not load in other repos), and `claude plugin list` (network-free
  actions must not spawn the CLI).
- **`plugin_provided(entry, mode) -> str | None`**: the plugin id when `mode`
  is `USER_MODE`, `entry["id"]` is in `PLUGIN_PROVIDED`, and
  `plugin_installed` is true; else `None`.
- **Scope of the skip** (Q1): the whole claude-code user surface,
  `surface_paths(entry, USER_MODE)`, which is the command files and the
  agent files. The plugin ships both `/s:*` skills and the `s:` agents.
- **`add`.** Split `entries` into provided and the rest; call `planned` on
  the rest only, so a provided entry adds no payload and no reference
  files. For each provided entry, append
  `skipped <id> (provided by the <plugin> plugin)`, then retire: for each
  path in `surface_paths(entry, mode)` that is `owned`, delete it, append
  `retired <display path>`, and record its directory; prune those
  directories with `_prune` and `_boundaries(mode)`. Unowned files are left
  alone and do not block. Retiring runs after the payload writes and the
  legacy removal. Shared reference files are left alone; `remove` still
  cleans them.
- **`status`.** For a provided entry: when any owned surface path exists,
  `state` is `stale` with detail `<n> duplicate files the <plugin> plugin
  provides — `shipd harness add <id> --user` retires them`; otherwise
  `state` is `skipped` with detail `provided by the <plugin> plugin`.
  `expected` is 0 and `present` is the count of owned paths.
- **`install_selection`.** A provided entry is still passed to `hg.add`, so
  retiring happens. Its report line is
  `  provided   <id>  by the <plugin> plugin — no command files needed`,
  in place of `installed`.
- **Retiring existing installs** (Q4, oracle): the generator's marker-owned
  removal, run by `shipd harness add claude-code --user` and
  `shipd install`; `status` points at it.
- **Proof** (Q5): on the build machine, from an empty scratch directory,
  run `claude -p "/context" --output-format json --max-turns 1` before and
  after `shipd harness add claude-code --user`. Its `result` field is a
  markdown report with a Skills category total and a per-skill table
  (Skill | Source | Tokens). The PR body records both readings: every
  `shipd:*` row gone after, and the Skills category total before and
  after. Beside them it records the count of files in
  `~/.claude/commands/shipd/` before and after (30 before, 0 after).
  This reading is the only measurement; no checked-in ceiling is added or
  lowered (Q6).
- **Version.** Bump `plugins/s/.claude-plugin/plugin.json` from `0.6.348` to
  the next patch, per `AGENTS.md`.

Risk: a user who relied on the `shipd:*` names loses them once the plugin
is detected; the `s:*` names do the same work. Detection that misreads the
files fails safe: it returns `False` and the files are written as today.

## Questions and answers

### Q1: Which claude-code user files does the skip cover?
- **Question:** When the plugin is installed, stop writing and retire
  (1) both the command files and the agent files, or (2) the command files
  only. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1: the plugin provides both the `/s:*` skills and the
  `s:` agents, so both generated copies are duplicates.
- **Queued:** q-dedupe-claude-commands-agent-files

### Q2: How does the generator detect the installed plugin?
- **Question:** (1) a user-scope `s@shipd` entry in
  `~/.claude/plugins/installed_plugins.json` and `enabledPlugins["s@shipd"]`
  true in `~/.claude/settings.json`, unreadable meaning not installed;
  (2) an entry at any scope; (3) run `claude plugin list`.
  Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1: only a user-scope, enabled install loads in every
  session, and a file read stays offline and fails safe.
- **Queued:** q-dedupe-claude-commands-plugin-installed-detection

### Q3: Is there a flag to write the files anyway?
- **Question:** (1) no override flag; (2) a `--with-plugin` flag on
  `shipd harness add`. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1: no flag; a user who wants the `shipd:*` files
  disables the plugin.
- **Queued:** q-dedupe-claude-commands-override-flag

### Q4: What retires the files already on disk?
- **Question:** (1) `shipd harness add claude-code --user` and
  `shipd install` retire marker-owned files and `status` reports them stale
  with that hint; (2) also a `shipd doctor` check; (3) a SessionStart hook.
  Recommendation: (1).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option 1. The epic names the generator's marker-owned removal
  as the retiring path; an automatic SessionStart cleanup is out.
- **Cited:** epic/context-budget

### Q5: How does this member prove its gain?
- **Question:** What evidence in the PR body shows the duplicates no
  longer reach the session?
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** The PR body records a
  before and after `/context` reading from
  `claude -p "/context" --output-format json --max-turns 1`, run on the
  build machine from an empty scratch directory, showing every `shipd:*`
  row gone and the Skills category total, plus the
  `~/.claude/commands/shipd/` file count before and after.
- **Queued:** q-dedupe-claude-commands-gain-proof

### Q6: Does this member hold its gain with a checked-in ceiling?
- **Question:** Does the PR add or lower a checked-in context ceiling, or
  is the before and after reading enough?
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** No ceiling: the before and after `/context` reading in the
  PR body is the only measurement, and this member has no `After`
  dependency for it.
- **Queued:** q-dedupe-claude-commands-ratchet-absent

## Readiness attestation

### Problem and motivation

Plugin users see every shipd command twice, which spends session context.

Evidence:

- epic/context-budget Introduction: "every command is listed twice, as
  `s:*` and `shipd:*`".
- This session's skill listing shows both `shipd:*` and `s:*` entries.

### Scope and non-goals

The claude-code user surface only, in three modules; repo mode and other
harnesses stay unchanged.

Evidence:

- epic/context-budget Design: the member "stops writing duplicate command
  files ... and retires the stale ones through the generator's
  marker-owned removal".
- Repo mode (`--root`) is out of scope and stays unchanged.

### Affected capabilities and files

Three capabilities and three modules, plus tests, two docs, and the version.

Evidence:

- `harness-verb` (requirement `harness-status`, base 6e06e167a7b0 from
  `spec_status.py base-hash`), `harness-registry`, `install-tui`.
- `harness_generate.py` `add`, `status`, `surface_paths`, `_prune`;
  `install_tui.py` `install_selection`; `harness_registry.py`
  `LEGACY_USER_PATTERNS`.
- Runnable premise: `HOME=<tmp> plugins/s/bin/shipd harness add claude-code
  --user` → exit 0; 31 command files, 3 agent files, 20 reference files;
  `status --json` → `installed`, 34 files.
- Runnable premise: `~/.claude/plugins/installed_plugins.json` (version 2)
  holds `s@shipd` entries with `scope` `user` and `project`;
  `~/.claude/settings.json` `enabledPlugins` has `s@shipd: True`;
  `~/.claude/commands/shipd/` holds 30 marker-owned files.
- Tests isolate `HOME`, so existing claude-code `--user` tests keep writing.

### No open task-shaping decision

Every decision is settled.

Evidence:

- Retirement trigger: oracle, Q4.
- Skip scope, detection, override: planner defaults, Q1, Q2, Q3.
- Proof and measurement: user, Q5, Q6.
