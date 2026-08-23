# Command cheatsheet

A lookup reference for the `/s:` commands and the `shipd` CLI — not a
walkthrough. New to shipd? Start with [Getting started](getting-started.md)
instead; come back here once you know the loop and just need the invocation
you forgot.

## Conventions

Flags shared across several verbs, stated once here instead of on every row
below:

- `--json` — emit machine-readable JSON instead of the text report.
- `--root DIR` — run against a repository root other than the current
  directory.

## /s: commands

| Command | What it does | Example |
|---|---|---|
| `/s:ask` | Ask the ask-mikk oracle before interrupting a human — a cited recommendation, or a queued question. | `/s:ask Should the new endpoint require auth?` |
| `/s:autopilot <epic> [detached]` | Drive an approved epic's unplanned members to shipped PRs unattended. | `/s:autopilot export-cli` |
| `/s:build [change]` | Plan, delegate to execution sub-agents, verify, and ship a change end to end. | `/s:build export-json-flag` |
| `/s:doctor` | Diagnose a shipd environment and run only the remedies you consent to. | `/s:doctor` |
| `/s:epic` | Decompose a feature into an epic of member changes with shared decisions. | `/s:epic Add multi-tenant billing` |
| `/s:fix` | Debug a reported problem against the spec library, then fix the drifted code. | `/s:fix The export command crashes on empty input` |
| `/s:forget` | Remove a captured preference from the personal memory store. | `/s:forget my vim preference` |
| `/s:gate` | Install the semantic review gate in a repository end to end. | `/s:gate` |
| `/s:initiative <new\|list\|review\|set> [args]` | Author, list, review, or attach workspace initiatives. | `/s:initiative list` |
| `/s:memory` | List the preferences captured in the personal memory store. | `/s:memory` |
| `/s:onboard [next\|back]` | Run the guided nine-step shipd tour. | `/s:onboard next` |
| `/s:plan` | Converge context into an execution-ready spec, then stop. | `/s:plan Add a --json flag to the export command` |
| `/s:remember` | Capture a durable user preference into the personal memory store. | `/s:remember I prefer terse commit messages` |
| `/s:research` | Turn a question into a cited research report an epic can link. | `/s:research What are common approaches to rate limiting?` |
| `/s:review [target]` | Run a semantic review of local changes before you push. | `/s:review` |
| `/s:status <status\|validate\|set-status\|pipeline> [args]` | Report or change a spec's lifecycle status through the guarded CLI. | `/s:status status export-json-flag` |
| `/s:teach [<change> Q<n>]` | Distill spec artifacts and answered queue entries into the workspace wiki. | `/s:teach` |
| `/s:video-ingest <video-or-slug>` | Turn a screen recording into a grounded, cited intent brief. | `/s:video-ingest recording.mp4` |
| `/s:workspace <init\|show\|clone\|sync>` | Set up and inspect the shipd workspace. | `/s:workspace show` |

## shipd CLI

| Command | What it does | Example |
|---|---|---|
| `list [--all]` | In-flight changes across the root and its worktrees; `--all` adds the applied ones from `completed/`. | `shipd list` |
| `status [change]` | A change's status and progress. | `shipd status` |
| `locate [change]` | Where an installed change lives. | `shipd locate` |
| `related <term> [term...]` | Spec artifacts ranked by term-hit count. | `shipd related statusline` |
| `epic <slug>` | An epic's status, metadata, and member states. | `shipd epic autonomous-delivery` |
| `workspace` | The workspace root, its projects, and initiatives. Needs an ancestor `.shipd-config.json` declaring `workspace` (see `/s:workspace init`). | `shipd workspace` |
| `board [text] [--epic EPIC] [--interval N]` | The delivery board (default: full-screen). | `shipd board text` |
| `metrics [summary\|record-flow\|forecast\|rollup]` | Delivery metrics (default: summary). | `shipd metrics` |
| `lint [change] [--epic EPIC] [--initiative INITIATIVE] [--workspace] [--wiki]` | Structurally validate specs and change deltas. | `shipd lint` |
| `doctor` | Preflight this environment for shipd. | `shipd doctor` |
| `statusline [install] [--settings FILE] [--force]` | Report or register the shipd statusline. | `shipd statusline` |
| `copilot [add\|remove] [--force]` | Maintain the Copilot code-review skill — the `/s:gate` merge gate — in a repo. | `shipd copilot` |
| `vendor [add\|remove] [--force]` | Maintain a vendored per-repo shipd install. | `shipd vendor` |
| `harness [list\|show\|add\|remove\|status] [ids...] [--all] [--user] [--force]` | The harness registry, and the generated `/s:` command files in a repo or in your home; `--all` acts on every harness in it. | `shipd harness list` |
| `install` | Pick your harnesses and install their commands. | `shipd install` |
