# Quickstart

From nothing installed to your first shipd-built change. Six steps, each with
the exact command. New to the idea? [What is shipd?](what-is-shipd.md) explains
the model; this page just gets you running.

You need [Claude Code](https://claude.com/claude-code) (`claude`) and
`python3` on your PATH before you start.

## 1. Install

One command, no checkout:

```bash
curl -fsSL https://shipd.now/install | sh
```

That registers the `shipd` marketplace, installs the `s` plugin into Claude
Code, and writes the `shipd` launcher to `~/.local/bin/shipd`. If that
directory is not on your PATH the installer says so — add it and re-open your
shell:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Then turn on auto-update once, so later versions arrive without you asking —
Claude Code leaves it off for third-party marketplaces like `shipd`. In a
session, open `/plugin` → **Marketplaces** → `shipd` and toggle auto-update on
(or add `"autoUpdate": true` to the `shipd` marketplace entry in
`~/.claude/settings.json`). Updates are fetched shortly after a session starts
and load in the next session, or right away after `/reload-plugins`; to update
by hand at any time, run `claude plugin update s@shipd`.

The [README's install section](../README.md#install) covers the by-hand
equivalent and dev mode (running `/s:*` from a checkout).

## 2. Preflight with `shipd doctor`

```bash
shipd doctor
```

It reports one line per check — `python`, `git`, `config`, `pipeline`, `gh`,
`textual`, `pydantic`, `snapshot`, `statusline` — and a closing `doctor: ok` or
`doctor: N problem(s)`. Only a `fail` line has to be resolved before you
continue: `warn` lines are optional extras (`gh` is needed only when you ship
a pull request, `textual` only for the full-screen delivery board, `pydantic`
only for declared-pipeline validation). A `warn statusline` line is the one
you can clear in a single command — `shipd statusline install`, see step 6.
Nothing is installed or edited by this verb.

`pydantic` is what unlocks the cheap-delivery opt-in: with it installed, putting
`{"autonomous-pipeline": "eco"}` in `.shipd-config.json` runs deliveries on the
eco preset.

## 3. Take the guided tour: `/s:onboard`

Start a Claude Code session and run:

```
/s:onboard
```

Nine steps that teach spec-driven development over a worked example in a
throwaway sandbox — you drive it yourself with `/s:onboard next` and
`/s:onboard back`, and step 8 builds the example for real on the engine.
Progress is saved to `~/.shipd/onboarding/state.json`, so you can stop and
resume in a later session. Nothing in your own repositories is touched.

If you would rather go straight to your own code, skip to step 4.

## 4. Plan your first change: `/s:plan`

Open a session in the repository you want to work on and describe what you
want, in prose:

```
/s:plan Add a --json flag to the export command so scripts can consume its output
```

The Planner investigates your codebase first and asks only what it genuinely
cannot infer. It then gives the work a name, puts it in its own git worktree
(`.worktrees/<change>` on branch `change/<change>`), writes the change's
artifacts to `.shipd/planned/<change>/` there — and stops. No code yet:

- `plan.md` — the idea and the binding implementation decisions
- `specs/<capability>/spec.md` — a delta spec per affected capability
- `tasks.md` — the implementation checklist

Read them. This is the moment to correct course, while the change is still
three markdown files. Planning ends by running the change through a
deterministic context gate: pass, and it is promoted to `ready`; fail, and it
is parked with the gaps written into `plan.md` for you to fill. The change name
it hands back is what you pass to build.

## 5. Build it: `/s:build`

```
/s:build <change>
```

The Orchestrator adopts the planned change, continues in its worktree,
delegates the checklist to execution sub-agents running one model tier down,
answers their questions, verifies the result against the delta spec's
scenarios, and then merges the deltas into the master library
(`.shipd/verified/`) and archives the change under `.shipd/completed/`.

`/s:build` also works from a bare description — it plans first and then builds
— but running `/s:plan` on its own first is the better habit: you get to review
the spec before anything is written.

## 6. Watch it: `shipd board` and `shipd status`

The delivery board, full-screen:

```bash
shipd board
```

This is one of the engine's two third-party dependencies (the other is
`pydantic`, used only for declared-pipeline validation) — `pip install
'textual>=8.2.8,<9'` if `shipd doctor` warned that it is not importable.
Without it, the same board printed once:

```bash
shipd board text
```

A single change's status and task progress:

```bash
shipd status              # the change currently in flight
shipd status <change>     # a named change
```

And everything in flight across the repository and its worktrees:

```bash
shipd list
```

To keep that status in front of you without asking, register the ☕
statusline:

```bash
shipd statusline install
```

It writes the `statusLine` entry into `~/.claude/settings.json`, and from your
next session the bottom line of every session carries the change's name,
lifecycle status, and task progress —
[getting started](getting-started.md#1-set-up-the-statusline) explains what
each part of the line shows.

The read verbs `list`, `status`, `locate`, `epic`, `workspace`, and `lint` all
take `--json` when you want to feed the output to something else. `shipd
--help` prints the full verb list; the
[README's CLI section](../README.md#the-shipd-cli) documents each one.

## Where to go next

- [What is shipd?](what-is-shipd.md) — the model behind the loop you just ran
- [`.shipd/README.md`](../.shipd/README.md) — the requirement and delta grammar
- The README's [Skills table](../README.md#skills) — every `/s:` command,
  including `/s:epic` to decompose a feature into changes and `/s:review` for
  a semantic review before you push
