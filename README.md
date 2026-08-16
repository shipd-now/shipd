```
         __    _           __
   _____/ /_  (_)___  ____/ /
  / ___/ __ \/ / __ \/ __  /
 (__  ) / / / / /_/ / /_/ /
/____/_/ /_/_/ .___/\__,_/
            /_/
```

**shipd** ([shipd.now](https://shipd.now)) is a spec-driven delivery system for
AI coding agents, distributed as a Claude Code plugin — everything is invoked as
`/s:<name>`. Instead of prompting an agent and hoping the result matches what you
meant, it makes the agent converge on a specification first — a plan, testable
requirement deltas, and a task checklist, all checked into your repository — and
only then build the change, validate it against those requirements, and ship it
as a pull request. For the longer version, see
[What is shipd?](docs/what-is-shipd.md).

## Install

### Install mode

One command, no checkout:

```bash
curl -fsSL https://shipd.now/install | sh
```

That URL redirects to this repo's [`install.sh`](install.sh); the raw form is
the documented equivalent, and works the same:

```bash
curl -fsSL https://raw.githubusercontent.com/shipd-now/shipd/main/install.sh | sh
```

The script needs `claude` and `python3` on your PATH and downloads nothing
itself — it registers the marketplace and installs the plugin through the
Claude Code CLI, which you can equally run by hand:

```bash
claude plugin marketplace add shipd-now/shipd
claude plugin install s@shipd
```

Then it writes the `shipd` launcher to **`~/.local/bin/shipd`** and prints a
hint if that directory is not on your PATH. The launcher resolves the newest
plugin snapshot under `~/.claude/plugins/cache/shipd/s/<version>/` at every
invocation (dotted-version ordering, so `0.6.10` beats `0.6.9`) and hands off
to it, so `claude plugin update s@shipd` upgrades the CLI too — nothing to
re-link. Re-running the installer is safe: an already-registered marketplace or
already-installed plugin counts as success. Set `SHIPD_PLUGIN_CACHE` to point
the launcher at a different cache root.

Claude Code can then keep the plugin current on its own, but **auto-update is
off by default for third-party marketplaces** like `shipd`, so turn it on once.
From a session, open `/plugin` → **Marketplaces** → `shipd` and toggle
auto-update on; or add `"autoUpdate": true` to the `shipd` marketplace entry in
`~/.claude/settings.json`, keeping whatever `source` that entry already has:

```json
{
  "extraKnownMarketplaces": {
    "shipd": {
      "source": "<keep this entry's existing source value>",
      "autoUpdate": true
    }
  }
}
```

An entry that loses its `source` is invalid and gets ignored, so add the flag
to the entry you already have rather than replacing it wholesale.

Enabled, updates are fetched shortly after a session starts and load in the
**next** session (or right away after `/reload-plugins`) — the launcher already
runs the newest installed snapshot, so nothing needs re-linking. Updating by
hand works at any time and is the fallback if you leave auto-update off:

```bash
claude plugin update s@shipd
```

Verify with:

```bash
shipd doctor
```

### Dev mode (working on shipd itself)

Clone the repo and register **the checkout** as a local directory marketplace,
so `/s:*` runs from your working tree instead of GitHub:

```bash
git clone https://github.com/shipd-now/shipd.git
cd shipd
claude plugin marketplace add "$PWD"
claude plugin install s@shipd
```

The same two steps from inside a Claude Code session:

```
/plugin marketplace add <path-to-your-checkout>
/plugin install s@shipd
```

For the CLI, symlink the copy in your **repo checkout** into a PATH directory:

```
ln -s "$PWD/plugins/s/bin/shipd" ~/bin/shipd
```

Never symlink the versioned plugin cache
(`~/.claude/plugins/cache/shipd/s/<version>/…`) — that path changes on every
version bump, so the link breaks the next time the plugin updates. (Install
mode's launcher exists precisely to avoid that.)

## Quickstart

New here? [**docs/quickstart.md**](docs/quickstart.md) walks from the install
above to your first shipd-built change in six steps — `shipd doctor`, the
guided `/s:onboard` tour, a first `/s:plan` and `/s:build` in your own
repository, and watching the result on the delivery board.

## Skills

Everything the plugin ships is invoked as `/s:<name>`.

**The core loop** — take one change from idea to merged.

| Invocation | What it does |
| --- | --- |
| `/s:onboard` | The guided tour: a nine-step walkthrough you drive with `/s:onboard next` and `/s:onboard back`, explaining spec-driven development over a worked example in a throwaway sandbox and building it for real on the engine. Progress persists, so the tour resumes across sessions. |
| `/s:doctor` | Diagnose and repair the environment shipd runs in: run the read-only `shipd doctor` preflight, propose one remedy per finding, run only the remedies you consent to in a single batched dialog, then re-run the preflight and report the before/after. Interpreter and config failures stay report-only, and `gh auth login` is handed to you to run. |
| `/s:plan` | Converge context into an execution-ready spec: investigate the codebase first, ask only what can't be inferred, then emit the lean `.shipd/` artifacts (`plan.md`, delta specs, `tasks.md`) and stop. Use it to work out an approach before writing any code. |
| `/s:build` | A spec-driven orchestrator: it plans and designs the `.shipd/` artifacts on the strongest model, then delegates the coding to execution sub-agents running one model tier below, answers their questions, verifies, and merges + archives the change with the plugin's own spec engine. Use it to build a non-trivial feature end-to-end. |
| `/s:review` | A CodeRabbit-style, AST-aware semantic review of local changes against a base ref before they are pushed: changed files mapped into cohorts, findings reported by cohort with a high/medium/low rubric and a ship-it/fix-required verdict. Read-only, with a `--json` mode for the PR gate. |
| `/s:status` | Report or change a spec's lifecycle status through the guarded status CLI: print the bare status, validate a change's structure, or run a guarded `set-status` transition that asks before forcing past a guard. |

**Bigger than one change** — decompose, deliver, and track work at scale.

| Invocation | What it does |
| --- | --- |
| `/s:epic` | Decompose a feature into an epic: investigate the codebase, ask one batched round of what can't be inferred, record the epic's Decisions and Design, and emit the stub table of member changes with complexity ratings — then stop. Members are planned later, one at a time, via `/s:plan`. |
| `/s:autopilot` | Drive an approved epic's unplanned members to shipped PRs unattended — plan → gate → build → auto-merging PR per member, in risk-ascending order, one worktree and branch each. Reports back with resume pointers for any parked member. |
| `/s:research` | Turn a question into a cited research report: bounded sub-questions, web search and fetch, anchored findings, and a numbered `## Sources` list — installed through the spec engine so an epic can link it. |
| `/s:video-ingest` | Turn a screen recording into an intent brief: transcribe and index the video, extract candidate intents anchored on transcript words, ground each on its nearest frame, and install a cited brief that flows straight into planning. |
| `/s:initiative` | Drive workspace initiatives through their CLIs: create a lint-clean brief from a workspace-first interview, report every initiative's status and requirement progress, walk a brief's outcomes and sync its status, or tag an epic with exactly one initiative via a PR. |
| `/s:workspace` | Set up and inspect the shipd workspace: create the workspace marker with a guided target-root choice, report the roster of projects and initiatives, bootstrap a job workspace from its repository URL, or materialize its members with real git. |

**Knowledge** — so a decision made once is never asked twice.

| Invocation | What it does |
| --- | --- |
| `/s:ask` | Query the ask-mikk oracle before interrupting a human: shape a request into one compact decision, consult the workspace wiki and the repo's spec surfaces, and relay the verdict — a cited recommendation, or a question queued for a person to answer later. |
| `/s:teach` | Distill the repo's spec artifacts and answered queue entries into the workspace wiki: scan the spec surfaces, interview only on the gaps and contradictions the scan surfaces, and ingest through the store's staged, lint-gated emit verb. |
| `/s:remember` | Capture durable preferences into the personal memory store: extract candidates from the invocation or the session, reconcile each against existing `memory-*` pages, confirm the set, and install it in one staged call. |
| `/s:memory` | List the durable preferences captured in the personal memory store — the read-only browse counterpart to `/s:remember`. |
| `/s:forget` | Remove a captured preference from the personal memory store: locate the matching `memory-*` page from a free-text description, confirm with a single dialog, and delete it. |

## The spec engine

shipd carries its own LLM-free spec system under `.shipd/` — exact-keyed CRUD
over markdown, driven by the scripts in `plugins/s/skills/build/scripts/`
(`spec_merge.py`, `spec_lint.py`, `spec_status.py`, `spec_emit.py`). No language
model reads or writes the library; the skills only orchestrate the scripts.

The content directory is **configurable**. `.shipd-config.json` files are resolved
by **layered upward search** — from a start directory parent-by-parent to the
filesystem root, then `~/.shipd-config.json`, then built-in defaults — merged
shallowly per top-level key (nearest layer wins). Its `dir` key renames the
content directory (default `.shipd`); the config filename itself is fixed.
`spec_status.py config-show` prints the resolved keys, their provenance, and the
active content directory.

The same layered config also carries the **autonomous pipeline** — an optional
`autonomous-pipeline` key holding an ordered list that _is_ the delivery
pipeline over the `research → epic → plan → gate → build → review` stage
registry. Entries run a stage as built in, skip it, bind tools to it, replace
its implementation, or insert a `custom` step; a declared list is wholesale
(omitted stages do not run) and, absent the key, the full default pipeline runs.
The key also accepts a **built-in preset name** — `default`, `eco`, or `basic` —
so cheapening a delivery is a one-line opt-in, and
`spec_status.py pipeline-show --expand <preset>` prints a preset's entry list as
the starting point for a custom one.
`spec_status.py pipeline-show` prints the effective pipeline and its provenance.
See [`.shipd/README.md`](.shipd/README.md) for the full entry grammar.

```
.shipd/
├── README.md                     # the format authority (grammar lives here)
├── constitution.md               # optional global steering rules, binding on plan/build
├── planned/                      # in-flight changes (not yet merged)
│   └── <change>/                 # lean artifact set per change:
│       ├── plan.md               #   idea + implementation decisions (carries the Status line)
│       ├── tasks.md              #   the implementation checklist
│       └── specs/<capability>/spec.md   # a delta spec per affected capability
├── completed/<date>-<change>/    # applied changes, retained immutably after merge
└── verified/                     # master library — canonical, one folder per capability
    └── <capability>/spec.md
```

`.shipd/verified/` is the single source of truth; a change under
`.shipd/planned/` carries the lean artifact set (`plan.md` with its `## Idea`
and `## Implementation` sections, `tasks.md`, and a delta spec per affected
capability) regardless of size, and moves into `completed/` once its
delta is merged. An optional `.shipd/constitution.md` holds the repo's
non-negotiable engineering rules; when present, plan and build load it as
binding constraints.

### Lifecycle

Every change flows through six statuses. The main line runs, in order:

```
draft → ready → active → complete → verified
```

- **draft** — the change is proposed and its artifacts are written; no guards.
- **ready** — the artifacts validate and build has the go-ahead to execute.
- **active** — execution sub-agents are running against the task checklist.
- **complete** — every task in `tasks.md` is done.
- **verified** — verification passed; the change is ready to merge and archive.
- **rejected** — the context-sufficiency gate found the plan lacking the
  context to build against the codebase, and parked it for human enrichment.

`rejected` is off to the side: the gate (`spec_gate.py <change>`) enters it from
`draft` or `ready` when a check fails, writing its findings into `plan.md` as a
`## Context insufficient` section; a human exits it back to `draft` or `ready`
after enriching the plan. A passing gate instead removes that section and
promotes the plan to `ready`.

Transitions run through `spec_status.py set-status <status> [change]` and are
**guarded**: `ready`/`active`/`complete`/`verified` require the change to
validate, and `complete`/`verified` additionally require a finished checklist.
`draft` and `rejected` carry no structural guard (a rejected plan may be broken
— that is the point). A refused transition surfaces its reason; `--force`
bypasses the guards (but never the value check on the status name itself).
`/s:status` wraps this and asks before it ever forces.

For the requirement and delta grammar (`id:` merge keys, `base:` hashes, the
four operation headers), see [`.shipd/README.md`](.shipd/README.md) — the
format authority. This README does not restate it.

## The `shipd` CLI

`plugins/s/bin/shipd` is a single stdlib-only binary fronting the engine's
read/inspect verbs, so a terminal never needs a raw script path:

```
shipd list [--all]             in-flight changes across the root and its worktrees
shipd status [change]          a change's status and progress
shipd locate [change]          where an installed change lives
shipd epic <slug>              an epic's status, metadata, and member states
shipd workspace                the workspace root, its projects, and initiatives
shipd board                    the interactive delivery board, full-screen
shipd board text               the delivery board, printed once
shipd metrics                  delivery metrics (default: summary)
shipd lint [change]            structurally validate specs and change deltas
```

Every verb but `list` delegates straight to the engine script, so output, exit
codes, and trailing flags (`--root`, slugs) behave exactly as they do against
the script itself. `board`'s optional mode word — `text`, and only as the
first argument — is the one thing consumed on the way through; everything
after it still passes verbatim. Mutating verbs (`set-status`, `merge`, `emit`, `autopilot`,
`worktree remove`) stay behind their guarded scripts and skills.

### Put `shipd` on your PATH

[Install mode](#install-mode) already did this: the installer writes a
version-independent launcher to `~/.local/bin/shipd` that re-resolves the newest
installed plugin snapshot on every run, so `claude plugin update s@shipd` is all
an upgrade ever takes. Working on shipd itself instead? See
[dev mode](#dev-mode-working-on-shipd-itself).

## Statusline

`plugins/s/integrations/statusline.sh` renders a live spec — its name,
lifecycle status, and task progress:

```
☕ <name> · <status> · <done>/<total>
```

It scans the workspace root's `.shipd/planned/` **plus** one level of
`.worktrees/*/.shipd/planned/`, so a change developed inside a worktree still
shows up. An `active` change owns the line wherever it lives (newest
`tasks.md` mtime breaks ties among several); otherwise it falls back to the
root's recorded selection, then to a sole live change. When more than one
change is live, the name gains a position bracket and the counts gain an
aggregate over every live spec's total:

```
☕ <name> (1 of X) · <status> · <done>/<total> (<total> of <Y>)
```

An `.shipd/` project with no live change reports `☕ no active specs` rather
than vanishing; only a workspace with no `.shipd/` directory at all stays
silent. When several changes are live but none is pickable it prints
`☕ <n> specs · none selected`. To pin the tracked change explicitly:

```
python3 plugins/s/skills/build/scripts/spec_status.py use <change>
```

which records the selection in `.shipd/state.json`. Register the statusline
in `.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "bash plugins/s/integrations/statusline.sh"
  }
}
```

## Build telemetry

At the end of a build, `/s:build` prints a report — a summary line, the
change and its task counts, any merge warnings, and a table of per-model and
total elapsed time — via `plugins/s/skills/build/scripts/build_report.py`.

The reporter reads its optional settings from the `build` key of the resolved
layered configuration — typically declared in `~/.shipd-config.json`. The config is
read-only (nothing is created on first run); all keys are optional and fall back
to these defaults:

| `build` key | Default | Meaning |
| --- | --- | --- |
| `logging_enabled` | `true` | append a record for each build |
| `log_dir` | `~/.shipd/builds` | where per-build files are written |
| `number_format` | `short` | how counts are rendered in the report |
| `parallelism` | `3` | default execution-sub-agent fan-out |

See [`references/shipd.config.example.json`](plugins/s/skills/build/references/shipd.config.example.json)
for a copyable template. Each build appends one record to
`~/.shipd/builds/builds.jsonl` plus a per-build file under the configured
`log_dir`.

## CI: lint your specs on every PR

The repository root carries `action.yml`, a composite GitHub Action that runs
shipd's structural spec lint against **your** repository: first the master
library, then every in-flight change under your resolved `planned/`
directory. Any lint finding fails the step, so a malformed spec or delta never
reaches `main`.

Add it to a workflow — check out your repo, then use the action:

```yaml
name: specs

on:
  pull_request:
  push:
    branches: [main]

jobs:
  spec-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: shipd-now/shipd@main
```

Prefer a pinned ref over `@main` — `shipd-now/shipd@<tag-or-sha>`, where
`<tag-or-sha>` is a release tag or commit SHA — so a change to the engine can
never move your CI underneath you.

- **`path`** — the directory to lint, defaulting to `.` (the checked-out
  repository root). Point it at a subdirectory when your specs live in one:
  `with: { path: services/api }`. The content directory itself is resolved
  from your `.shipd-config.json`, so a custom `dir` needs no extra input.
- **Runner requirement: `python3` on `PATH`** — the only one. GitHub-hosted
  runners ship it. The engine scripts are stdlib-only Python 3 and travel
  inside the action's own checkout, so the action installs nothing, downloads
  nothing, caches nothing, and uses no third-party action steps.

## Structure

```
shipd/
├── .claude-plugin/
│   └── marketplace.json          # marketplace manifest (name: "shipd")
├── .claude/
│   └── settings.json             # registers the ☕ statusline
├── .shipd/                         # the spec library (see .shipd/README.md)
│   ├── README.md
│   ├── constitution.md          # optional global steering rules
│   ├── verified/                # master library — one folder per capability
│   ├── planned/                 # in-flight changes (not yet merged)
│   └── completed/               # applied changes, retained immutably
└── plugins/
    └── s/                        # the plugin (name: "s" → /s: prefix)
        ├── .claude-plugin/
        │   └── plugin.json       # plugin manifest (carries the version)
        ├── agents/               # sub-agent definitions (s:sub-agent, s:validator, s:oracle)
        ├── bin/
        │   └── shipd             # the CLI
        ├── integrations/
        │   └── statusline.sh     # ☕ spec statusline
        └── skills/               # skills → /s:<skill-name>, one folder each
            ├── plan/
            │   └── SKILL.md
            ├── build/
            │   ├── SKILL.md
            │   ├── references/   # config example + sub-agent prompt
            │   └── scripts/      # spec engine, coordinator, reporting
            └── …                 # every other skill in the table above
```

Slash commands, when the plugin ships any, live in a sibling `commands/`
directory (see [Adding a command](#adding-a-command)).

The `/s:` prefix comes from the **plugin** name (`s`), not the marketplace name.

## Adding a command

Create `plugins/s/commands/<name>.md`. It becomes `/s:<name>`.
Frontmatter supports `description`, `argument-hint`, `model`, and `allowed-tools`.
Use `$ARGUMENTS` (or `$1`, `$2`, …) in the body to interpolate what the user typed.

## Adding a skill

Create `plugins/s/skills/<name>/SKILL.md` with `name` and `description`
frontmatter, then write the skill's instructions in the body. Put any supporting
files (scripts, references, templates) alongside `SKILL.md` in the same folder.
`plugins/s/skills/build/` is a live example to model a new skill on. Skills are
auto-invoked by Claude when their `description` matches the task, or explicitly
via `/s:<name>`.

## After editing

Run `/plugin marketplace update shipd` (or restart Claude Code) to pick up changes.
Validate with `claude plugin validate .`
