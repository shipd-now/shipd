<!-- doc-type: how-to -->

# Getting started

This guide takes you from nothing installed to your first shipd-built
change, in six steps: install, preflight, tour, plan, build, and watch. Each
step names the exact command. New to the idea first? [What is
shipd?](what-is-shipd.md) explains the model this guide walks you through.

You need [Claude Code](https://claude.com/claude-code) (`claude`) and
`python3` on your PATH before you start.

## 1. Install

One command, no checkout:

```bash
curl -fsSL https://shipd.now/install | sh
```

That registers the `shipd` marketplace, installs the `s` plugin, and writes
the `shipd` launcher to `~/.local/bin/shipd`. Add that directory to your PATH
if the installer says so:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Turn on auto-update once, so later versions arrive without asking — Claude
Code leaves it off for third-party marketplaces like `shipd`. Open `/plugin`
→ **Marketplaces** → `shipd` and toggle auto-update on, or add
`"autoUpdate": true` to the `shipd` marketplace entry in
`~/.claude/settings.json`. Updates load at the next session start, or right
away after `/reload-plugins`. Two manual fallbacks work at any time.
`shipd update` applies a newer published version, and `shipd update --check`
reports what it would do without changing anything. `claude plugin update
s@shipd` does the same through the Claude Code CLI.

On a terminal, the installer finishes with a harness multi-select — Cursor,
Copilot, Codex, and the rest — and generates their `shipd` commands for you.
A headless run (CI, no usable terminal) skips the question and prints
instructions instead. Inside a repository, `shipd harness add` installs the
generated command files at the repo level.

## 2. Preflight: `shipd doctor`

```bash
shipd doctor
```

It reports one line per check, then a closing `doctor: ok` or `doctor: N
problem(s)`. The checks are `python`, `git`, `config`, `pipeline`, `schema`,
`wiki`, `gh`, `difft`, `textual`, `snapshot`, `statusline`, `protection`,
`automerge`, and `copilot-secret`. Only a `fail` line blocks you; `warn`
lines mark optional extras. This verb installs and edits nothing.

Cheapening a delivery needs nothing installed: `{"autonomous-pipeline":
"eco"}` in `.shipd-config.json` opts a delivery into the cheap preset.
Separately, `{"pr-mode": "draft"}` at a workspace root stops deliveries
beneath it at a draft PR instead of auto-merging.

## 3. Take the guided tour: `/s:onboard`

```
/s:onboard
```

Nine steps teach spec-driven development over a worked example in a
throwaway sandbox. Drive it yourself with `/s:onboard next` and `/s:onboard
back`. Progress saves to `~/.shipd/onboarding/state.json`, so you can stop
and resume later. It touches nothing in your own repositories.

## 4. Plan your first change: `/s:plan`

Open a session in the repository you want to work on and describe the
change in prose:

```
/s:plan Add a --json flag to the export command so scripts can consume its output
```

The Planner investigates your codebase first and asks only what it
genuinely cannot infer. It names the change, creates a dedicated worktree
(`.worktrees/<change>` on branch `change/<change>`), and writes the
artifacts there — then stops. No code yet:

- `plan.md` — the idea and the binding implementation decisions
- `specs/<capability>/spec.md` — the testable delta for each affected
  capability
- `tasks.md` — the implementation checklist

Read them: this is the cheapest moment to correct course. See
[`.shipd/README.md`](../.shipd/README.md) for the full requirement and delta
grammar these artifacts follow.

## 5. Build it: `/s:build`

```
/s:build <change>
```

The Orchestrator adopts the planned change and delegates the checklist to
execution sub-agents one model tier down. It answers their questions and
verifies the result against the delta spec's scenarios. Three durable
outcomes follow: working code on the `change/<name>` branch, the deltas
merged into `.shipd/verified/`, and the change archived under
`.shipd/completed/`.

## 6. Watch it

A single change's status and task progress:

```bash
shipd status              # the change currently in flight
shipd status <change>     # a named change
```

Everything in flight across the repository and its worktrees:

```bash
shipd list
```

The full-screen delivery board:

```bash
shipd board
```

To keep that status in front of you without asking, register the ☕
statusline:

```bash
shipd statusline install
```

It writes the `statusLine` entry into `~/.claude/settings.json`. When you
installed through the installer, that entry resolves the newest cached
plugin snapshot at render time rather than pinning one version. It keeps
working across upgrades this way.

## Where to go next

- [Cheatsheet](cheatsheet.md) — every `/s:` command and `shipd` verb, with
  its options and one example
- [What is shipd?](what-is-shipd.md) — the model behind the loop you just ran
- [Workspaces](workspaces.md) — standing one job up across several repos
