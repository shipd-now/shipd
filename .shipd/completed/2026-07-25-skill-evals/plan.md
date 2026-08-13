# skill-evals

Status: verified

## Idea

The engine scripts under `plugins/s/skills/build/scripts/` are covered by
pytest, but the LLM-facing skills (`/s:plan`, `/s:epic`, `/s:build`,
`/s:status`) have no regression signal at all: a SKILL.md edit that degrades
what a real session produces is only discovered when a human notices a bad
session. The repo already ships deterministic graders (`spec_lint.py`,
`spec_status.py`) — what is missing is a harness that runs a skill for real
and feeds its output to those graders.

This change adds a local eval harness:

- A stdlib-only runner, `evals/run.py`, that executes each eval case as a
  headless Claude Code session (`claude -p`) in an isolated scratch copy of a
  checked-in fixture repo, loading the working tree's plugin via
  `--plugin-dir`.
- Deterministic grading: the runner asserts the session produced exactly one
  change under `am/planned/`, that `spec_lint.py` passes on it, and that the
  plan was promoted to `Status: ready`.
- Two starter cases exercising `/s:plan`, plus unit tests for the runner's
  discovery and grading logic (no live session needed for the tests).
- An AGENTS.md note documenting when and how to run evals.

### Non-goals

- No CI wiring — eval runs need Claude credentials and real model spend; they
  run locally on demand. A scheduled/manual GitHub Actions job is future work.
- No LLM-as-judge grading — v1 grades structurally only.
- No eval cases for `/s:build`, `/s:epic`, or `/s:status` yet — the case
  layout supports them later, but v1 targets `/s:plan` only.
- No MODIFIED-delta case: the emission guide's base-hash snippet assumes the
  plugin checkout is present in the repo being planned, which is false in a
  fixture; both v1 cases use ADDED-only deltas.
- No changes under `plugins/s/` and no plugin version bump.

Affected capabilities: `skill-evals` (added). Impact: new `evals/` tree at the
repo root (`run.py`, `cases/`, `tests/`), one AGENTS.md section. No new
dependencies; runner is Python 3 stdlib only.

## Implementation

- **Evals live at the repo root (`evals/`), not inside `plugins/s/`.** The
  skill sources being tested exist only in this repo, and the plugin cache
  snapshot should not carry test fixtures to consumers or need a version bump
  per eval edit. Rejected: `plugins/s/evals/` — ships dead weight and couples
  eval edits to snapshot refreshes.
- **Sessions load the live plugin via `claude -p ... --plugin-dir
  <repo>/plugins/am`.** This tests the working tree, immune to the stale-cache
  problem. Rejected: running `claude plugin update s@shipd` before each
  eval — mutates user-scope state and still tests an installed copy, not the
  tree under edit.
- **Case layout is fixture + prompt only.** A case is
  `evals/cases/<name>/prompt.md` plus `evals/cases/<name>/fixture/` (a minimal
  repo with an `am/` layout). Assertions are fixed in the runner for v1, not
  per-case config. Rejected: a per-case `expect.json` — premature knobs; both
  v1 cases share the same structural contract.
- **Scratch assembly.** Per run the runner copies the fixture to a temp
  directory, overwrites `am/README.md` with the host repo's copy (grammar
  authority must not drift inside fixtures), then `git init` + initial commit
  so the session sees a clean repo. The session runs with the scratch dir as
  cwd, `--permission-mode bypassPermissions`, `--output-format json`, and a
  20-minute timeout; the transcript is saved into the scratch dir. Risk: a
  bypass-permissions session could write outside its cwd; mitigated by the
  scratch cwd, prompts scoped to the fixture, and a `--keep-scratch` flag for
  inspection — accepted for a dev-only tool.
- **Grading is the host repo's own linter.** The runner invokes
  `plugins/s/skills/build/scripts/spec_lint.py <change> --root <scratch>`
  from the host checkout, then asserts: exactly one directory under
  `am/planned/`, lint exit 0, and `Status: ready` in the produced `plan.md`
  (the `/s:plan` contract ends at ready). Rejected: duplicating structural
  checks in the runner — the linter is already the oracle.
- **Repetition and exit semantics.** `--runs N` (default 1) repeats each case;
  the runner prints a per-case pass-rate and exits non-zero if any case has a
  pass-rate below 1.0. Other flags: `--case <name>` to filter, `--claude-bin`
  to override the CLI binary, `--keep-scratch` to retain scratch dirs.
- **Runner is testable without a live session.** Case discovery, scratch
  assembly, and grading are pure-ish functions unit-tested under
  `evals/tests/` against prebaked directory trees; only the end-to-end
  verification task invokes the real `claude` CLI.

Risk: eval outcomes are model-dependent and nondeterministic — a failing run
may be model variance, not a skill regression. Guarded by the pass-rate
reporting (`--runs N`) and by keeping v1 assertions purely structural, where
compliant sessions should pass reliably.
