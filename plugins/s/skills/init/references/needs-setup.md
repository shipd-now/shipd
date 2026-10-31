<!-- doc-type: reference -->

# The needs-setup check

Every skill that writes into the content directory runs this check once, before
it investigates or writes anything. It asks the engine whether the project is
set up, then acts on the answer.

Run it from the root the skill writes into: the change's worktree for `plan`,
`research`, `epic`, and `build`; the repository root otherwise.

```sh
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" init-status [--unattended]
```

Add `--unattended` when your invocation says no human is available, or the run
is unattended (a sub-agent prompt, an autopilot run). A sub-agent cannot
inherit `SHIPD_UNATTENDED`, so say it with the flag.

Act on the `action:` line of the output:

- `action: none` — the project is ready. Print nothing about setup and continue.
- `action: scaffold` — only the content directory is missing, and the config
  already says how to lay it out. Run
  `python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" init`,
  print the one line `shipd: created the <content-dir> layout` (naming the
  directory it created), and continue. Ask nothing.
- `action: wizard` — a human is present and the project has never been set up.
  Run the `/s:init` wizard by reference (load the `init` skill; do not restate
  its steps), then run `init-status` again. Continue only once it prints
  `action: none`. If the user stops the wizard, stop the calling skill too.

If `init-status` exits non-zero, relay its `Error:` line and stop. Do not
scaffold, and do not continue as though the layout existed.

Under harness plan mode, report the verdict and stop before scaffolding or
opening the wizard; the user exits plan mode and re-invokes.
