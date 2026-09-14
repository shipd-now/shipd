# review-static-analysis
Status: verified
Epic: review-rubric

## Idea

Give `/s:review` the repo's own linter output, through a `semdiff lint`
subcommand that detects linters, runs them over the changed paths, and emits
findings in the engine's JSON envelope.

### Motivation

The review reasons out by hand what a static check settles for free: the epic's
Introduction states that it "runs no linter over the changed code", and
`.shipd/verified/semantic-review/spec.md` defines five subcommands, none of
which runs one. A reviewer therefore spends judgement on findings a linter
would have handed it.

### Details

- Add `semdiff lint <base> [<head>]`, detecting `ruff`, `eslint`, `flake8` and
  `pylint` by their conventional marker files, running each over the changed
  paths its language owns, and emitting one JSON object in the shape the other
  subcommands use.
- Execute only binaries whose argv the engine constructs, resolving
  `node_modules/.bin` before `PATH`. Report a script-based linter as detected
  but not run, unless the repository opts in.
- Add a `lint` key to the engine's configuration registry so a repository can
  override a detected linter, disable one, or opt into script execution.
- Add a `### 3b. Read the linter output` step to the skill, with the detail
  behind a new reference.
- Bump the plugin version.

Affected capabilities: `semantic-review` (one added requirement) and
`shipd-config` (one modified requirement). Impact:
`plugins/s/skills/review/scripts/semdiff.py`,
`plugins/s/skills/build/scripts/spec_common.py`,
`plugins/s/skills/build/references/shipd.config.example.json`,
`plugins/s/skills/review/SKILL.md`, a new
`plugins/s/skills/review/references/linters.md`,
`plugins/s/skills/review/tests/`, and
`plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No fix mode. The epic binds linters to check mode, and the review never edits
  the repository.
- No declare-to-enable for linters outside the detected four. Configuration
  overrides, disables, or opts into script execution; it does not teach the
  engine a new linter.
- No parsing of human-readable linter output. Only machine formats are read.
- No change to the four existing subcommands.
- No blocking. A missing linter, a crash, or a timeout degrades and is
  reported, exactly as a missing difftastic does.

## Implementation

- **BLOCKED ON AN EPIC AMENDMENT — read this before building.** The epic's
  Decision states that `.shipd-config.json` "overrides the detection or
  disables a linter". It does not grant configuration the power to **enable**
  script execution, which is what this change's `run_scripts` opt-in does. Run
  `/s:epic review-rubric amend` to extend that Decision before task 1.1 is
  claimed. The oracle identified this gap independently while answering the
  detection-breadth question, so it is a known divergence rather than an
  oversight.

- **Detection is by marker file plus an available binary.** A linter counts as
  detected when its conventional marker is present **and** its binary resolves.
  A marker without a binary is reported as detected-but-unavailable, never
  silently dropped — the reviewer needs to know a configured check did not run.

  | Linter | Marker | Binary | Machine format |
  | --- | --- | --- | --- |
  | `ruff` | `ruff.toml`, `.ruff.toml`, or `[tool.ruff]` in `pyproject.toml` | `ruff` | `--output-format json` |
  | `flake8` | `.flake8`, or `[flake8]` in `setup.cfg`/`tox.ini` | `flake8` | `--format=json` |
  | `pylint` | `.pylintrc`, or `[tool.pylint]` in `pyproject.toml` | `pylint` | `--output-format=json` |
  | `eslint` | any `eslint.config.*` or `.eslintrc*` | `eslint` | `--format json` |

  Rejected: scoping detection to what this workspace uses. A survey of all six
  workspace repos found one linter — eslint in `shipd-now-website` — and no
  Python linter at all, but `semdiff.py` is vendored into arbitrary user repos
  by `shipd copilot add`, so this workspace does not bound what must be
  detected. The epic's bar is that a repository configuring nothing still gets
  a working check.

- **Binary resolution prefers the project's own install.** For each linter, try
  `node_modules/.bin/<tool>` from the repository root, then `PATH` via
  `shutil.which`. `shipd-now-website`'s `lint` script is literally `eslint`, so
  a constructed argv reproduces that script's behaviour exactly — which is why
  the fixed-argv default is not merely the safe option but the equivalent one.

- **Only the engine's own argv runs, unless a repository opts in.** This is the
  posture `semdiff` already holds: it shells out to `git`, `difft` and `rg`,
  each a known binary with arguments the engine chose. A repo-defined script is
  a wider trust posture because `semdiff.py` runs inside every gated
  repository's GitHub Actions. So a `lint` script is reported as detected but
  not run, and running it requires `{"lint": {"run_scripts": true}}` in
  `.shipd-config.json`. Rejected: running scripts by default, which would have
  the vendored engine execute repo-authored commands in CI without the
  repository ever saying so.

- **Changed paths only, partitioned by language.** Take the changed paths from
  the same endpoint resolution `diff` and `files` use, then give each linter
  only the paths whose extension it owns — `.py` for the three Python linters,
  the JavaScript and TypeScript extensions for eslint. A linter with no owned
  path in the diff is skipped and reported as such, so it never lints the whole
  repository.

- **One JSON object, matching the house shape.** Echo the resolved
  `base`/`head`/`mode` as the other subcommands do, then a `linters` list — one
  entry per detected linter carrying its `name`, `state`
  (`ran`, `unavailable`, `skipped`, `not-run`, `failed`), the `argv` actually
  executed, and its `findings` (`path`, `line`, `rule`, `message`,
  `severity`) — plus a `summary` with per-state and finding counts. The `argv`
  is emitted so a reader can reproduce the run, which matters most when a
  linter failed.

- **Failure is reported, never raised.** Each linter runs under a timeout; a
  non-zero exit is normal (findings exist) and is distinguished from a crash by
  whether the output parses. A timeout, a crash, or unparseable output sets
  `state: failed` with the captured stderr excerpt, and the subcommand still
  exits `0`. This mirrors the difftastic degradation the skill already
  performs: a missing tool loses accuracy and never blocks the review.

- **The skill step is a trigger inline and detail behind a reference.** The
  epic's amended ceiling Decision binds `SKILL.md` to stay under 300 lines —
  it stands at 291 — and to buy space with a reference rather than a raised cap.
  So `### 3b. Read the linter output` is a short inline step naming the command
  and the rule that a linter finding is corroboration rather than a finding of
  its own, and
  `plugins/s/skills/review/references/linters.md` carries the detail. The new
  reference must satisfy the existing agreement test, whose threshold has no
  slack.

- **A linter finding is not automatically a review finding.** The step states
  the judgement rule explicitly: a linter hit on a changed line is evidence the
  reviewer weighs, and it is reported only when it bears on the change. This
  keeps the review from degrading into a linter report, which is the failure
  mode that makes static-analysis integration unwelcome.

- **The config key touches a second capability.** `RECOGNIZED_CONFIG_KEYS` in
  `spec_common.py` is a closed registry, and the `config-sample-coverage`
  requirement in `shipd-config` enumerates its members verbatim while a test
  asserts the registry and `references/shipd.config.example.json` agree in both
  directions. Adding `lint` therefore edits the constant, the example file, and
  that requirement together, in this change.

- **Risk: a linter that hangs stalls every review.** The timeout is the guard,
  and it is per-linter rather than overall so one slow tool cannot consume the
  budget of the others.

- **Version bump.** `plugins/s/.claude-plugin/plugin.json` moves to `0.6.218`,
  per the cache-snapshot rule in AGENTS.md. The new subcommand also marks every
  existing gate install stale, which `/s:gate update` refreshes — the designed
  path, per the epic's Decision.

## Questions and answers

### Q1: How wide should linter auto-detection be in its first version?

- **Question:** For the new `semdiff lint` subcommand, how wide should linter auto-detection be in its first version? Options: evidence-grounded, detecting only what the workspace uses today (an npm `lint` script plus `ruff`); the standard set, detecting `ruff`, `eslint`, `flake8` and `pylint` by conventional marker files; or config-only, with no auto-detection. Recommended: evidence-grounded.
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Build the standard set. Detect `ruff`, `eslint`, `flake8` and `pylint` by their conventional marker files, with `.shipd-config.json` overriding or disabling a detected linter. The six-repo workspace survey is the wrong population to scope against, because `semdiff.py` is vendored into arbitrary user repositories by `shipd copilot add` and runs there, so what this workspace uses today does not bound what the subcommand must detect. The recommended option fails the epic's zero-config bar in any repository running flake8 or pylint. Detection by marker file costs one table entry and one test case per linter and stays inside the stdlib-only, single-file constraint.
- **Cited:** `epic/review-rubric` — "**Linter discovery detects first and reads config second.** `semdiff lint` infers linters from repo files. `.shipd-config.json` overrides the detection or disables a linter. A repo that configures nothing still gets a working check."

### Q2: May the subcommand execute a repository-defined script?

- **Question:** May `semdiff lint` execute a repository-defined script such as `npm run lint`, or should it only execute known linter binaries with a fixed argv it constructs itself? Options: fixed argv only, reporting script-based linters as detected but not run; execute repository scripts too when `package.json` declares one; or execute repository scripts only on an explicit `.shipd-config.json` opt-in. Recommended: fixed argv only.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Fixed argv by default, with a repository able to opt into script execution through `.shipd-config.json`. The engine executes only known linter binaries with an argv it constructs, resolving `node_modules/.bin` before `PATH`, because `semdiff.py` is vendored byte-identical into user repositories and runs inside their GitHub Actions — a wider trust posture than its existing fixed-argv calls to `git`, `difft` and `rg`. Absent the opt-in, a script-based linter is reported as detected but not run.
- **Queued:** `q-semdiff-lint-repo-script-execution`
