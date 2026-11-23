<!-- doc-type: how-to -->

# Guided tour

`/s:onboard` runs a nine-step tour of shipd. It teaches spec-driven
development over one worked example, a small kanban app. You drive it
yourself, one step at a time.

The tour runs in a throwaway sandbox at `~/.shipd/onboarding/sandbox/`. It
creates and changes no file in your own repositories.

## When to use it

- **Learn how shipd works before you use it.** The tour explains the
  artifacts of a change, then builds the example for real.
- **Show shipd to a teammate.** The sandbox makes the tour safe to run on
  any machine.

Skip it when you already know the loop. Follow
[Your first change](getting-started.md) to plan and build in your own
repository.

## How to run it

1. Start the tour in a Claude Code session:

   ```
   /s:onboard
   ```

2. Move one step forward:

   ```
   /s:onboard next
   ```

3. Return one step:

   ```
   /s:onboard back
   ```

The tour never advances by itself. Each step ends by naming the command that
continues. Progress saves to `~/.shipd/onboarding/state.json`, so a bare
`/s:onboard` in a later session resumes at the saved step.

The last step offers to delete or keep `~/.shipd/onboarding/`.

## Reference

### The nine steps

| step | what it covers |
| --- | --- |
| 1 | What spec-driven development is. |
| 2 | How shipd works: artifacts, and builds inside worktrees. |
| 3 | The three artifacts of a change. |
| 4 | The example `plan.md`. |
| 5 | The example delta spec. |
| 6 | The example `tasks.md`, and model tiering. |
| 7 | A summary of the first six steps. |
| 8 | The real build of the example, and how to try the result. |
| 9 | A small enhancement to plan next, with the exact command. |

`back` works on steps 1 to 7. Step 8 never builds twice: a second visit
shows the summary of the finished build.

### Related pages

- [Plan a change](plan.md) — how `/s:plan` plans a change in your own
  repository
- [Build a change](build.md) — how `/s:build` builds it
- [Cheatsheet](cheatsheet.md) — every command
