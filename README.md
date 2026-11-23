<img src="icon.svg" align="right" width="240" alt="☕ shipd">

☕ **shipd** ([shipd.now](https://shipd.now)) is a spec-driven delivery system for
AI coding agents, distributed as a Claude Code plugin — everything is invoked as
`/s:<name>`. Instead of prompting an agent and hoping the result matches what you
meant, it makes the agent converge on a specification first — a plan, testable
requirement deltas, and a task checklist, all checked into your repository — and
only then build the change, validate it against those requirements, and ship it
as a pull request. For the longer version, see
[What is shipd?](docs/what-is-shipd.md), then [Workspaces](docs/workspaces.md)
— the guide to standing one job up across several repos.

## Install

One command, no checkout:

```bash
curl -fsSL https://shipd.now/install | sh
```

That URL redirects to this repo's [`install.sh`](install.sh). The raw form
works the same:

```bash
curl -fsSL https://raw.githubusercontent.com/shipd-now/shipd/main/install.sh | sh
```

The script needs `claude` and `python3` on your PATH. It registers the
marketplace and installs the plugin through the Claude Code CLI. You can run
those two steps by hand instead:

```bash
claude plugin marketplace add shipd-now/shipd
claude plugin install s@shipd
```

The installer then writes the `shipd` launcher to `~/.local/bin/shipd`. Check
the setup with:

```bash
shipd doctor
```

[Install](docs/install.md) covers updates, harness selection, vendoring shipd
into a repository, and working on shipd itself.

## Documentation

The docs are grouped by what you are doing. Each group opens on one page.

- **Start here** — install, run your first change, and learn the terms:
  [Your first change](docs/getting-started.md).
- **Plan** — turn an idea into a spec that is ready to build:
  [Plan a change](docs/plan.md).
- **Build** — build a planned change and ship it as a pull request:
  [Build a change](docs/build.md).
- **Epics** — split a feature into changes and deliver them together:
  [Epics](docs/epics.md).
- **Review and merge** — review a change and gate its merge:
  [Semantic review](docs/semantic-review.md).
- **Multi-agent PRs** — let several agents take turns on one pull request:
  [Multi-agent PR](docs/multi-agent-pr.md).
- **Knowledge** — keep a decision so nobody is asked twice:
  [The oracle](docs/oracle.md).
- **Workspaces** — run one job across several repositories:
  [Workspaces](docs/workspaces.md).
- **Configure** — change how shipd behaves in your project:
  [Customise shipd](docs/customise.md).

The [command cheatsheet](docs/cheatsheet.md) lists every `/s:` skill and every
`shipd` verb.

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
        ├── agents/               # sub-agent definitions (s:sub-agent, s:validator, s:teacher)
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
            └── …                 # every other skill
```

Slash commands, when the plugin ships any, live in a sibling `commands/`
directory (see [Adding a command](#adding-a-command)).

The `/s:` prefix comes from the **plugin** name (`s`), not the marketplace name.

The plugin is the engine's distribution vehicle for every harness, not only
Claude Code. A repository that vendors shipd holds a directly runnable
`.shipd/plugin/s/bin/shipd`. Non-Claude tooling in that repository reaches the
engine through it.

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

A Claude Code session can also register your checkout as the marketplace:

```
/plugin marketplace add <path-to-your-checkout>
/plugin install s@shipd
```
