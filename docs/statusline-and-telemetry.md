<!-- doc-type: how-to -->

# Statusline and telemetry

Three surfaces report on shipd's work. The statusline shows the live change
in Claude Code's status bar. The build report sums up one finished build. The
delivery metrics sum up every finished delivery in a repository.

The statusline renders one live change: its name, its lifecycle status, and
its task progress.

```
☕ <name> · <status> · <done>/<total> tasks
```

## When to use it

- **Watch a build from the status bar.** Register the statusline once, and
  every later session shows the live change.
- **Check what a build cost.** Read the build report that [`/s:build`](build.md) prints
  at the end of a build.
- **Track delivery over time.** Read the delivery metrics for throughput,
  lead time, and cycle time.

## How to run it

### Register the statusline

1. Report the current registration and the one this install would write:

   ```
   shipd statusline
   ```

2. Write the registration:

   ```
   shipd statusline install
   ```

3. Start a new Claude Code session. The statusline appears at its start.

Bare `shipd statusline` reports and changes nothing. `install` writes the
`statusLine` entry into `~/.claude/settings.json` and keeps every other
setting. Pass `--force` to replace a different existing registration.

To change the segments on each line, show or set the layout:

```
shipd statusline layout
shipd statusline layout spec,context directory
```

Each word declares one line, and commas separate its segments. Setting a
layout also rewrites the registration in the settings file, when that file
already registers shipd's statusline. With `--config` and without `--settings`,
`layout` saves the layout in the named config file and leaves the settings
file untouched.

The statusline reads the root's planned changes, plus one level of
worktrees. So a change built inside a worktree still shows up. An `active`
change owns the line wherever it lives. When more than one change is live,
the name gains a position bracket, and the counts gain the total over
every live change:

```
☕ <name> (1 of X) · <status> · <done>/<total> tasks (<total> of <Y>)
```

A project with no live change shows `☕ no active specs`. The `statusline`
check of [`shipd doctor`](doctor.md) reports the registration.

### Read the build report

`/s:build` prints the report at the end of a build. The report holds:

- a summary line;
- the change and its task counts;
- any merge warnings;
- a table of per-model and total elapsed time.

Each build writes one file under the configured `log_dir`, and appends one
record to `builds.jsonl` in that directory.

### Read the delivery metrics

`shipd metrics` prints the team-level delivery board as text. The board
covers throughput, deployment frequency, lead time, cycle time, rework rate,
change-fail rate, work in progress, and cost. Four subverbs cover the rest:

- `summary` derives and prints the delivery-metrics summary.
- `record-flow` appends a lifecycle snapshot to the root's flow time series.
- `forecast` runs a Monte-Carlo delivery forecast from observed throughput.
- `rollup` writes a delivery rollup for an audience as self-contained
  markdown.

## Reference

### Statusline segments

| Segment | Renders |
| --- | --- |
| `spec` | The live change line, or the `no active specs` text. |
| `directory` | The workspace directory, with a leading `$HOME` shown as `~`. |
| `context` | The session's context-window use, as a four-cell bar and a percentage. |

The default layout is one line, `spec,context`.

### Statusline flags

| Flag | Effect |
| --- | --- |
| `--settings PATH` | Names the settings file. The default is `~/.claude/settings.json`. `layout` with `--config` skips the settings file unless this flag is given. |
| `--config PATH` | Names the shipd config file that holds the layout. The default is `~/.shipd-config.json`. |
| `--force` | Replaces a different existing registration. |
| `--show SEG` | With `install`, adds a segment to the layout. |
| `--hide SEG` | With `install`, removes a segment from the layout. |

### Report settings

The `build` config key holds the report settings. Every setting is optional.

| Setting | Default | Effect |
| --- | --- | --- |
| `logging_enabled` | `true` | Appends a record for each build. |
| `log_dir` | `~/.shipd/builds` | Names the directory for the per-build files and `builds.jsonl`. |
| `number_format` | `short` | Sets how the report renders counts. |
| `parallelism` | `3` | Sets the default fan-out of execution sub-agents. |

[Customising shipd](customise.md) owns the `statusline` and `build` config
keys and their layering.
