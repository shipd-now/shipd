<!-- doc-type: reference -->

# Harness plan mode and shipd skills

Claude Code's plan mode injects a block that claims to supersede every
other instruction. That block forbids edits other than its own plan file.
A shipd skill that writes cannot run its flow under that block. This file
says what a writing skill does instead.

## The rule

Harness plan mode never replaces a shipd skill's output. When the session
is in plan mode, a writing skill runs only its read-only steps. It stops
before its first write and asks the user to exit plan mode and re-invoke
the skill.

## Read-only steps

These steps run under plan mode:

- Reading files, specs, and engine output through the `cat`, `show`, and
  `locate` verbs.
- Running read-only engine verbs such as `pipeline-show` and
  `config-show`.
- Printing findings for the user.

## Writes

The first of these ends the run:

- Creating a worktree or a branch.
- Writing or installing any file, including staged artifacts.
- Spawning an agent that writes, such as `s:oracle`, which files queue
  entries.
- Running a mutating engine verb, a commit, a push, or a pull request.

## What never happens

- The skill never writes the harness plan file.
- The skill never calls `ExitPlanMode`.
- The skill never swaps its own outputs for plan mode's outputs, such as
  plan agents, a dialog round, or a plan file. A half shipd, half plan mode
  run is the failure this rule exists to stop.

## The stop message

End the turn with the findings so far, then one line in this shape:

```text
/s:<skill> can't write under plan mode. Exit plan mode (shift+tab) and run /s:<skill> again.
```

## Read-only skills

The read-only skills `duck`, `drift`, `explain`, `memory`, and `review`
carry no clause. They run unchanged under plan mode.
