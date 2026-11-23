<!-- doc-type: how-to -->

# Your first change

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
the `shipd` launcher to `~/.local/bin/shipd`. [Install](install.md) covers
updates, harnesses, and the other install modes.

## 2. Preflight: `shipd doctor`

```bash
shipd doctor
```

It reports one line per check, then a closing `doctor: ok` or `doctor: N
problem(s)`. Only a `fail` line blocks you; `warn` lines mark optional extras.
[Doctor](doctor.md) lists every check and the `--fix` remedies.

Cheapening a delivery needs nothing installed: `{"autonomous-pipeline":
"eco"}` in `.shipd-config.json` opts a delivery into the cheap preset.
Separately, `{"pr-mode": "draft"}` at a workspace root stops deliveries
beneath it at a draft PR instead of auto-merging. See
[Customising shipd](customise.md) for every preset and every other
surface.

## 3. Take the guided tour: `/s:onboard`

```
/s:onboard
```

Nine steps teach spec-driven development over a worked example in a
throwaway sandbox. Drive it yourself with `/s:onboard next` and `/s:onboard
back`. Progress saves to `~/.shipd/onboarding/state.json`, so you can stop
and resume later. It touches nothing in your own repositories.

## 4. Plan your first change: `/s:plan`

Open a session in the repository you want to work on and describe the change in prose:

```
/s:plan Add a --json flag to the export command so scripts can consume its output
```

The Planner investigates your codebase first and asks only what it
genuinely cannot infer. It names the change, creates a dedicated worktree
(`.worktrees/<change>` on branch `change/<change>`), and writes the
artifacts there — then stops. No code yet:

- `plan.md` — the idea and the binding implementation decisions
- `specs/<capability>/spec.md` — the testable delta for each affected capability
- `tasks.md` — the implementation checklist

The first `/s:plan` in a new repository runs the `/s:init` wizard first; `/s:init <section>` changes one section later.

Read them: this is the cheapest moment to correct course. See
[`.shipd/README.md`](../.shipd/README.md) for the full requirement and delta
grammar these artifacts follow. [Plan a change](plan.md) covers the planning
flow in full.

## 5. Build it: `/s:build`

```
/s:build <change>
```

The Orchestrator adopts the planned change and delegates the checklist to
execution sub-agents one model tier down. It answers their questions and
verifies the result against the delta spec's scenarios. Three durable
outcomes follow: working code on the `change/<name>` branch, the deltas
merged into `.shipd/verified/`, and the change archived under
`.shipd/completed/`. [Build a change](build.md) covers the build in full.

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
[Statusline and telemetry](statusline-and-telemetry.md) covers the statusline
and the delivery metrics.

## Where to go next

- [Cheatsheet](cheatsheet.md) — every `/s:` command and `shipd` verb, with
  its options and one example
- [What is shipd?](what-is-shipd.md) — the model behind the loop you just ran
- [Core ideas](core-ideas.md) — the definitions of shipd's terms
- [Workspaces](workspaces.md) — standing one job up across several repos
