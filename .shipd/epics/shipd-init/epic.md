# shipd-init
Status: ready
Theme: developer-experience

## Introduction

A user who starts shipd in a new project has no guided way to set it up. The
`shipd init` verb creates the content directory's folders and asks nothing, so
choices such as where specs live, how PRs ship, or where personal memory sits
are left to hand-edited JSON. Meanwhile each skill meets a missing layout in
its own way: `/s:plan` and `/s:epic` ask scaffold-or-stop, `/s:research` stops
cold, `/s:autopilot`, `/s:status`, and `/s:initiative` state the requirement
and handle nothing, and `/s:build` wrongly claims the layout appears on first
merge. Config writes are just as scattered: `workspace-init`,
`workspace-project`, and `worktree hooks add` each hand-roll their own JSON
read and write into one fixed file, and nothing validates a value before it
lands — a bad key surfaces only when a later command reads it.

This epic gives shipd one front door for setup and one owner for config. The
`shipd` binary becomes the only writer of `.shipd-config.json`: it validates
every change against a single key registry, rejects an invalid change with an
`error:` line naming what is wrong and, where it helps, a `hint:` line saying
how to do it, and picks the right layer file itself. A new `shipd init status`
check tells a skill whether the project is on its first run, missing only its
folders, or ready. A new `/s:init` skill walks the user through setup with
AskUserQuestion dialogs — a full wizard on a true first run, or one section on
demand — and every layout-requiring skill routes through one shared reference
instead of six divergent copies.

Success criteria: a fresh repo's first `/s:plan` runs the `/s:init` wizard and
then continues; a repo with config but no folders gets its folders silently and
continues; `shipd config set pr-mode bogus` writes nothing, exits non-zero, and
names the accepted values; every `.shipd-config.json` write in the engine goes
through the one writer; and `/s:init config` re-asks only the config section.

### Non-goals

- **No new config keys.** The registry covers `RECOGNIZED_CONFIG_KEYS` as they
  stand; adding keys is separate work.
- **No move of setup logic into `/s:init`.** Workspace, wiki, memory, worktree
  hook, and gate setup keep their existing verbs and skills; `/s:init` calls or
  hands off to them.
- **No GitHub-side setup.** Branch protection, rulesets, and secrets stay with
  `/s:gate` and `/s:doctor`.
- **No change to how config is read.** Layered resolution
  (`load_layered_config`, `resolve_config`) is unchanged; only writing and
  validation are new.
- **No onboarding tour changes.** `/s:onboard` keeps its own sandbox template.
- **The machine-local member map** (`.shipd-workspace.local.json`) is not a
  config layer and keeps its own writer.

## Decisions

- **The binary is the only config writer.** Every `.shipd-config.json` write
  goes through one engine writer exposed as `shipd config set <key> <value>`,
  `shipd config unset <key>`, and `shipd config check`. The existing writers in
  `workspace-init` (`spec_common.py`), `workspace-project` (`spec_status.py`),
  and `worktree hooks add`/`remove` (`worktree.py`) move onto it and keep their
  current output and tests. Skills never edit the JSON by hand. Rejected: a
  skill editing JSON directly (the repo already forbids it), and one verb per
  key.
- **One key registry validates everything.** Each entry of
  `RECOGNIZED_CONFIG_KEYS` gets a validator (reusing the existing accessor
  logic — `resolve_pr_mode`, `workspaces_root_dir`, `resolve_models`,
  `pipeline_schema`, `validate_workspace`, the hook-list checks), a one-line
  hint, and a default layer. A write validates the **merged** config the
  change would produce before touching disk.
- **Reject with reasons and suggestions.** An invalid change writes nothing
  and exits non-zero, printing one `error: <what is wrong>` line per problem
  and, where it helps, a `hint: <how to do it>` line: a "did you mean" for an
  unknown key, the accepted values for an enum, and the owning verb for a key
  that has one (for example `use shipd worktree hooks add`). `/s:doctor`'s
  config check runs the same validation over every key.
- **The engine picks the layer.** A write lands in the layer that already
  declares the key; when no layer declares it, the registry's default layer
  applies (repo for `pr-mode`, `autonomous-pipeline`, `dir`, `store_root`;
  user `~/.shipd-config.json` for `memory_dir`, `voice`, `wiki_base`).
  `--layer repo|workspace|user` overrides it.
- **First run is strict.** A project is on its first run only when its repo
  root has no `.shipd-config.json` and no content directory resolves
  (`dir`/`store_root` honored from any layer). Workspace and user config do
  not count as the project being set up. `shipd init status` reports
  `first-run`, `layout-missing`, or `ready`, so no skill guesses.
- **Auto-run respects existing config.** A skill that needs the layout runs
  `shipd init status`: `first-run` runs the full `/s:init` wizard, then the
  original skill continues; `layout-missing` creates the folders through
  `shipd init` (honoring config), prints one line, and continues; `ready` does
  nothing.
- **Unattended runs never ask.** `/s:autopilot` sets `SHIPD_UNATTENDED=1` on
  the sessions it launches. Under that flag a skill treats a `first-run`
  verdict like `layout-missing`: it creates the folders only, never opens the
  wizard, and continues.
- **`/s:init` is a front door.** Its sections call the existing verbs
  (`shipd init`, `workspace-init`, `wiki-init [--personal]`, `shipd config
  set`) and hand off to `/s:worktree-hooks` and `/s:gate`; no setup logic
  moves into the skill.
- **Wizard order and sections.** The full wizard runs, in order: where files
  live (`dir`, `store_root`), how changes ship (`pr-mode`,
  `autonomous-pipeline`), personal stores (`memory_dir`, `wiki_base`), session
  behaviour (`voice`, `guardrails`), then the constitution. Each step skips
  what is already set, and `/s:init <section>` runs one step alone. Questions
  use AskUserQuestion dialogs with the current value or default first.
- **Constitution starter in the wizard only.** The wizard offers a commented
  `constitution.md` starter template; silent or section-only init never writes
  one.
- **One shared "needs setup" reference.** The six divergent missing-layout
  passages (`/s:plan`, `/s:epic`, `/s:research`, `/s:autopilot`, `/s:status`,
  `/s:initiative`) and `/s:build`'s first-merge claim are replaced by one
  reference that runs `shipd init status` and acts on its verdict.

## Design

```
shipd binary (engine)                         /s:init skill (front door)
├ config set/unset/check  ◄────────────────── config sections (AskUserQuestion)
│   key registry: validator + hint + layer    layout section ──► shipd init
│   validate merged config → write or reject  constitution section (starter)
├ init status → first-run | layout-missing    workspace / wiki / memory ──► verbs
│               | ready  (SHIPD_UNATTENDED)   hooks / gate ──► /s:worktree-hooks,
└ workspace-init, workspace-project,                           /s:gate
  hooks add/remove ──► the one writer
                                              layout-requiring skills:
                                                shared reference → init status
```

The seams follow ownership. `config-control` builds the registry and the
writer and migrates the existing writers; nothing user-facing depends on it
except `shipd config`. `init-status` adds the read-only verdict verb and the
unattended flag; it reads config but writes none. `init-skill` consumes both:
the wizard writes through `shipd config set`, and the shared reference keys on
`shipd init status`.

## Changes

| Change | Description | Code | Integration | Unknowns | Risk | After |
| --- | --- | --- | --- | --- | --- | --- |
| config-control | Key registry, `shipd config set/unset/check` with error and hint output, existing writers migrated, doctor check | high | high | medium | medium | |
| init-status | `shipd init status` verdict verb and the `SHIPD_UNATTENDED` flag set by autopilot | low | medium | low | low | |
| init-skill | The `/s:init` wizard and section skill plus the shared "needs setup" reference wired into the layout-requiring skills | medium | high | medium | medium | config-control, init-status |
