# shipd-dx
Status: complete
Theme: developer-experience

## Introduction

shipd is going public. The active `shipd-port` epic moves the whole system
under the `shipd.now` brand in the `shipd-now/shipd` repository — but the
first hour of a newcomer's experience still assumes they are the author:
install means cloning the repo and registering a local directory marketplace,
putting `shipd` on PATH means hand-symlinking a script out of the checkout,
nothing preflights the environment (Python version, `git`, `gh` auth,
`textual` for the board), the engine scripts each grew their own output and
error conventions, consumer repos have no way to run shipd's lint as a CI
check, and the README is written as a format authority rather than a first
hour.

The commissioned research report on agentic-CLI developer experience (linked
below) confirms the core is not the problem: shipd already embodies the
report's governance and harness recommendations — spec-anchored SDD with a
constitution and human-in-the-loop gates, per-change git-worktree isolation,
AST-aware semantic review, and a terminal-native delivery board. What the
report identifies as the top-of-funnel levers — installation vectors,
human-first CLI conventions per clig.dev, and CI integration — are exactly
shipd's unbuilt edges. This epic closes them.

Intended outcome: a developer who finds `shipd-now/shipd` on GitHub reaches
a working `/s:plan` in their own repository within minutes, and their first
hour is guided rather than reverse-engineered.

Success criteria:

- One command installs the plugin from GitHub and puts a working `shipd` on
  PATH, with no repo clone and no manually maintained symlink into a
  versioned cache path.
- `shipd doctor` reports every prerequisite as green or as an actionable
  finding, and exits nonzero when a required check fails.
- The `shipd` binary and the engine scripts share one documented output
  convention — error format, usage style, TTY-aware color — and the read
  verbs offer `--json` for scripting.
- A consumer repository turns on shipd's structural lint as a GitHub check
  with a few lines of workflow YAML.
- A quickstart document takes a newcomer from install to their first shipped
  change without reading engine source.

### Non-goals

- **No web surface.** The report's xterm.js/web-terminal bridging and the
  shipd.now site are out of scope (the port epic also deferred the site);
  the board's existing `html` verb is unchanged.
- **No package-manager distribution.** No Homebrew, Scoop, Winget, npm, or
  GoReleaser pipelines — shipd ships no compiled binary; the Claude Code
  plugin marketplace is the distribution vector.
- **No MCP client, model routing (BYOK), or context virtual memory.** shipd
  rides Claude Code, which owns the agentic substrate — MCP, model
  selection, hooks, and context management are inherited, not rebuilt.
- **No TUI rewrite.** The report's Bubbletea/tmux stack guidance is
  consciously not adopted; the `textual` board is spec'd, shipped, and owns
  board DX (see the `update-ui-look-feel` epic).
- **No new mutating CLI verbs.** Mutations stay behind the guarded scripts
  and skills; this epic polishes the read/inspect surface only.
- The epic does not itself plan or build its member changes.

## Research

- [Architecting the Next-Generation Developer Experience for Agentic Development Tools](../../research/cli-developer-experience/report.md) — commissioned DX survey covering SDD governance, CLIG-conformant CLI design, TUI architecture, installation vectors, agentic harnesses, and pain-point desiderata; this epic implements its installation, CLI-convention, and CI recommendations and records its substrate recommendations as inherited or rejected.

## Decisions

- **The audience is the GitHub consumer; the checkout stays the dev mode.**
  Every member optimizes for someone who installed from `shipd-now/shipd`
  without cloning it. Nothing may regress the author workflow (local
  directory marketplace, worktrees, checkout symlink) — the two paths
  coexist, documented as install mode vs dev mode.
- **Claude Code is the substrate; shipd invests only in what it owns.** The
  report's MCP, BYOK, hook-system, and context-memory recommendations are
  satisfied by the host platform. shipd's DX surface is its engine CLIs,
  plugin packaging, docs, and CI integration — nothing else.
- **The constitution beats the report's stack advice.** The engine stays
  stdlib-only Python 3 with `textual` as the single named exception; the
  report's Go/Charm ecosystem recommendation is rejected. Its TEA,
  adaptive-color, and keybinding guidance is already embodied by the
  `textual` board.
- **One install vector: the Claude Code plugin marketplace with the GitHub
  repo as source.** A bootstrap script (the report's `curl | sh` fallback)
  may wrap `claude plugin marketplace add` + `claude plugin install` + PATH
  setup, but it downloads nothing beyond the repo/plugin itself and runs no
  postinstall-style fetches — the supply-chain cautions in the report are
  binding.
- **The consumer `shipd` launcher must survive version bumps.** The plugin
  cache path is versioned (`~/.claude/plugins/cache/shipd/s/<version>/`), so
  the PATH entry resolves the current snapshot at runtime instead of
  symlinking a versioned path. The README's checkout symlink remains the
  dev-mode story.
- **clig.dev is the conformance authority for the human surface.** The
  conventions are codified once in a spec'd shared helper and adopted per
  script: errors are a single `Error: <reason>` line on stderr with a
  nonzero exit, usage errors exit 2, color renders only on a TTY and honors
  `NO_COLOR`, and output verbosity follows progressive disclosure — say
  what changed, keep diagnostics behind a flag.
- **Pinned output changes travel with spec deltas.** Existing scenarios pin
  exact stderr strings and exit codes; a member that changes one carries the
  amendment to that capability's spec in the same change.
- **`doctor` is read-only.** It preflights `python3` version, `git`, `gh`
  presence and auth, plugin snapshot presence/freshness, optional `textual`
  (board-only), and config resolution; it prints actionable findings, exits
  nonzero on a failed required check, and never mutates anything.
- **`--json` is for read verbs only.** Machine output lands on the
  read/inspect verbs (`status`, `list`, `locate`, `epic`, `workspace`,
  `lint`); guarded mutating scripts keep their human/interactive contract.
- **The CI action is a repo-root composite action running the stdlib lint.**
  `uses: shipd-now/shipd@<ref>` gets checkout-free structural lint with tool
  caching keyed by OS and version and cache access scoped against the
  report's cache-poisoning caution. The semantic review gate needs an LLM
  and is explicitly not part of the action.
- **Engine constraints hold.** Every member touching `plugins/s/` bumps the
  plugin version in its own PR; the stdlib-only `tests/` suite keeps passing
  without `textual`.

## Design

The epic is four tracks along the seams the research report names, six
member changes in total:

1. **Conventions (foundation)** — a spec'd output-convention helper in the
   engine's shared module and its adoption across `shipd` and the engine
   scripts. Lands first; `doctor` and `--json` build on it.
2. **Install & first-run** — the public install path: a bootstrap script
   wrapping marketplace registration, plugin install, and PATH setup with a
   version-independent launcher; plus the `shipd doctor` preflight verb.
3. **CI integration** — the composite action exposing `shipd lint` to
   consumer repositories.
4. **Docs** — the first-hour quickstart and a newcomer-first README
   restructure, written last so it documents the installed reality.

Dependency order: `cli-conventions` → {`shipd-doctor`, `cli-json`};
`public-install` is independent but precedes `quickstart-docs`;
`ci-lint-action` is independent. `quickstart-docs` lands last.

## Changes

| Change | Description | Code | Integration | Unknowns | Risk |
| --- | --- | --- | --- | --- | --- |
| cli-conventions | Codify one human-first output convention (error format, usage/help style, TTY-aware color with NO_COLOR, progressive-disclosure verbosity) in a shared helper and adopt it across `shipd` and the engine scripts, amending pinned-output scenarios in the same change | medium | high | low | medium |
| shipd-doctor | Read-only `shipd doctor` preflight verb checking python3 version, git, gh auth, plugin snapshot presence/freshness, optional textual, and config resolution, with actionable findings and a nonzero exit on failed required checks | medium | low | low | low |
| public-install | One-command consumer install: a bootstrap script wrapping marketplace add + plugin install + PATH setup, a version-independent `shipd` launcher resolving the current plugin cache snapshot at runtime, and the README install section split into install mode vs dev mode | medium | medium | medium | medium |
| cli-json | `--json` machine output on the read/inspect verbs (`status`, `list`, `locate`, `epic`, `workspace`, `lint`) for scripting and future surfaces | medium | medium | low | low |
| ci-lint-action | Repo-root composite GitHub Action running `shipd lint` in consumer repositories, with OS/version-keyed tool caching and branch-scoped cache access | low | medium | medium | low |
| quickstart-docs | First-hour documentation: a quickstart from install to first shipped change, a skill index, and a newcomer-first README restructure | low | low | low | low |
