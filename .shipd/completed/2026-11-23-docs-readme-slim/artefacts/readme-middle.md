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

