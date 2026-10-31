# init-status
Status: verified
Epic: shipd-init
Planned-at: 191ef2030e4fd6e5268c03e2725cc744f545098f
Gated-hash: dcd4e427f6b3

## Idea

Add a read-only `shipd init status` verdict verb and have the detached
autopilot mark its sessions unattended with `SHIPD_UNATTENDED=1`.

### Motivation

Each layout-requiring skill guesses on its own whether a project is new,
half set up, or ready, so `/s:init` (member `init-skill`) has no single check
to decide between running its wizard and creating folders silently. Autopilot
sessions have no human, and nothing tells a skill inside them to skip the
wizard.

### Details

- `spec_status.py init-status [--root DIR] [--unattended] [--json]` prints a
  `first-run` / `layout-missing` / `ready` verdict plus the action a skill
  takes (`wizard`, `scaffold`, `none`).
- `shipd init status` routes to it through a new `INIT_MODES` table in
  `bin/shipd`; bare `shipd init` is unchanged.
- `session_driver.run_turn` / `run_turn_result` gain an `env` overlay; the
  autopilot's session seam and drift-judge seam pass
  `{"SHIPD_UNATTENDED": "1"}`.
- `docs/cheatsheet.md` gains the `status` mode.

Affected capabilities: `spec-status` (added `layout-status-verb`),
`shipd-cli` (added `cli-init-status-mode`), `epic-autopilot` (modified
`session-turn-result-text`, added `unattended-session-env`). Impact:
`plugins/s/skills/build/scripts/spec_status.py`, `plugins/s/bin/shipd`,
`plugins/s/skills/build/scripts/session_driver.py`,
`plugins/s/skills/build/scripts/autopilot.py`, their tests, and
`docs/cheatsheet.md`.

### Non-goals

- No skill reads the verdict yet; the shared "needs setup" reference and the
  `/s:init` wizard belong to `init-skill`.
- No config writes; `shipd config set/unset/check` belong to `config-control`.
- The in-session drive's sub-agent instructions are not changed here.
- `shipd init` itself (the scaffold) is not changed.

## Implementation

- **Verdict rule** (`cmd_init_status(root, unattended, as_json)` in
  `spec_status.py`, beside `cmd_init`). `content = sc.specs_dir(root)`.
  `ready` when every name in `LAYOUT_DIRS` is a directory under `content`;
  else `first-run` when `<root>/.shipd-config.json` is not a file and
  `content` is not a directory; else `layout-missing`. This is the epic's
  strict first-run decision verbatim. Rejected: treating any ancestor config
  as "set up" — the epic says workspace and user config do not count.
- **Unattended**: `args.unattended or os.environ.get("SHIPD_UNATTENDED") ==
  "1"` (Q2). The `--unattended` flag (Q3) lets a caller that cannot set an
  environment variable — an in-session autopilot sub-agent — claim the same
  mode; `init-skill` decides whether its reference passes it.
- **Action** is derived in the engine so no skill re-derives it: `ready` →
  `none`, `layout-missing` → `scaffold`, `first-run` → `wizard` when attended,
  `scaffold` when unattended.
- **Output** (Q1): four keyed lines `verdict:`, `content-dir:`,
  `unattended: true|false`, `action:`; `content-dir` is
  `os.path.relpath(content, root)` when `content` is inside `root`, else
  absolute. `--json` (via `_add_json_flag`) prints
  `{"verdict", "content_dir" (absolute), "unattended", "action"}`. Exit `0`
  for every verdict; config errors go through the existing
  `except sc.ConfigError` handler (`Error:` line, exit 1). Rejected: one exit
  code per verdict — skills read keyed lines everywhere else, and a non-zero
  `first-run` would look like a failure.
- **Dispatch in `spec_status.py`**: a new `init-status` subparser repeating
  `--root` with `default=argparse.SUPPRESS` exactly as `init` does, plus
  `--unattended` (`store_true`) and `--json`. The schema-compat exemption
  becomes `if args.verb not in ("init", "init-status")`: the verb reads no
  artifacts.
- **Binary** (`bin/shipd`): add `INIT_MODES = {None: ("spec_status.py",
  ["init"]), "status": ("spec_status.py", ["init-status"])}` and a mode
  selection block in `main` identical to the `WIKI_MODES` one. The banner line
  becomes `init [status] [--root DIR]` with a continuation line describing
  `status`. The module docstring needs no edit (`status` writes nothing).
  The dispatch is an ADDED requirement rather than an edit of `cli-dispatch`,
  whose 200-line block `config-control` also touches; a separate block keeps
  the two members' deltas from colliding.
- **Env seam** (Q4): `run_turn` and `run_turn_result` take `env=None`;
  `run_turn_result` passes `env=None if env is None else {**os.environ,
  **env}` to `subprocess.run` (add `import os`). `autopilot.py` defines
  `UNATTENDED_ENV = {"SHIPD_UNATTENDED": "1"}` and passes it from the runner
  in `_make_session_fn` and from `judge_fn` in `_make_judge_fn`. Rejected:
  setting `os.environ` in `autopilot.main` — it leaks into every
  subprocess and is not testable through the seams.
- **Judge-seam fix**: `judge_fn` currently passes `effort=effort`, a name not
  in scope, so the turn would raise `NameError`. Pass `effort=model` — its own
  resolved `model` argument, matching `run_turn_result`'s "effort level or
  concrete model id" contract. The new judge-seam test runs this line, so it
  must be fixed here.
- **Test fakes**: `ProductionSessionEffortTest.fake_run_turn` in
  `test_autopilot.py` has a fixed signature; add `env=None` to it.

Risk: a user's `~/.shipd-config.json` declaring `dir` or `store_root` would
change test verdicts; the new tests set `HOME` to a temp directory.

## Questions and answers

### Q1: What does shipd init status print and how does it exit?
- **Question:** Options: (1) four keyed lines (verdict, content-dir,
  unattended, action) plus `--json`, exit 0 for every verdict; (2) the
  verdict word alone; (3) a distinct exit code per verdict. Recommendation:
  (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. Keyed lines match `locate` and `config-show`, the
  `action` line spares every skill from re-deriving it, and exit 0 keeps a
  first run from reading as a failure.
- **Queued:** q-init-status-output-shape
- **Relied on by:** init-skill

### Q2: Which SHIPD_UNATTENDED values switch unattended mode on?
- **Question:** Options: (1) exactly `1`; (2) any non-empty value other than
  `0`. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1, exactly `1` — the value the epic names and the one
  autopilot sets; anything else is attended.
- **Queued:** q-shipd-unattended-value

### Q3: How does an in-session sub-agent signal unattended?
- **Question:** In-session autopilot sub-agents cannot inherit an environment
  variable. Options: (1) an `--unattended` flag on the verb, in-session
  prompts unchanged here; (2) in-session stage instructions tell sub-agents
  to prefix `SHIPD_UNATTENDED=1`; (3) not handled. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. The flag gives the same verdict without an env var;
  whether the shared reference passes it when a prompt says no human is
  available is `init-skill`'s call.
- **Queued:** q-init-status-in-session-unattended
- **Relied on by:** init-skill

### Q4: How does autopilot set the flag on its sessions?
- **Question:** Options: (1) an `env` argument on `session_driver.run_turn` /
  `run_turn_result` that autopilot passes; (2) autopilot sets `os.environ` at
  startup. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1 — scoped to the sessions, testable through the
  existing seams, and invisible to the eval and room runners.
- **Queued:** q-autopilot-unattended-env-seam

## Readiness attestation

### Problem and motivation

Skills have no shared check for setup state, and autopilot sessions have no
marker that no human is present.

Evidence:

- Epic `shipd-init` Decisions "First run is strict" and "Unattended runs
  never ask" assign the verdict verb and the flag to this member.
- `python3 plugins/s/bin/shipd init status --root <tmp>` → exit 2,
  `unrecognized arguments: status`: no such check exists today.

### Scope and non-goals

The verb, its binary mode, the session env seam, and the autopilot flag; skill
wiring and config writes stay with the sibling members.

Evidence:

- In scope: `spec_status.py` `cmd_init` neighbourhood and `main` (lines
  ~575-620, ~5308-5320, ~5648), `bin/shipd` `WIKI_MODES` pattern (~144-149,
  ~3544-3548), `session_driver.py` `run_turn_result` (~262-295),
  `autopilot.py` `_make_session_fn` / `_make_judge_fn` (~833-868, ~1101-1112).
- Out of scope: skill `SKILL.md` files (`init-skill`), config writers
  (`config-control`).

### Affected capabilities and files

Three capabilities and four engine files plus tests and the cheatsheet.

Evidence:

- `spec-status`: new `layout-status-verb`. `shipd-cli`: new
  `cli-init-status-mode`. `epic-autopilot`: `session-turn-result-text`
  (base 26431e01c989 from `spec_status.py base-hash`), new
  `unattended-session-env`.
- Runnable premise: `shipd init --root <tmp>` → exit 0, created the four
  directories and printed `all shipd directories are ready`.
- Runnable premise: `config-show` prints `content-dir: .shipd`; `specs_dir`
  honors `dir`/`store_root` (`spec_common.py:809-829`).
- Tests: `test_spec_status.py` (`TestInitVerb` pattern), `test_shipd_cli.py`
  (`test_wiki_modes_map_to_the_status_script`), `test_session_driver.py`
  (`ResultTextTest`), `test_autopilot.py` (`ProductionSessionEffortTest`).

### No open task-shaping decision

Every decision is settled; the four open ones took planner defaults.

Evidence:

- Output shape Q1, unattended value Q2, in-session flag Q3, env seam Q4.
- Verdict rule and layer handling come from the epic's Decisions.
