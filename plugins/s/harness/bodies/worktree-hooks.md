<!-- description: Author and register the setup scripts a fresh worktree runs, through the engine's worktree hooks verbs. -->
# /s:worktree-hooks — set up what a fresh worktree needs

Turn a described setup need — a `.env` copied in, a database seeded,
dependencies installed — into an entry on the repo's `post-worktree-scripts`,
the list the engine's worktree create path runs right after it creates a
worktree. You author the script and register it; the engine owns the config
file. Never hand-edit `.shipd-config.json` — the verbs own its format, the
duplicate refusal, the shadowing warning, and every unrelated key in it.

<!-- include:preamble -->

The hook verbs run as `shipd worktree hooks <verb …>` from the repo root, using
the binary on PATH or `"$S/../../../bin/shipd"` when it is not installed there.
An argument carries what the user wants — a setup step to add, a request to see
what is registered, or one to remove; without one, ask which and wait.

1. **Resolve the content directory.** Run `python3 "$S/spec_status.py" --root
   <repo-root> config-show` and take the directory name from its `dir =
   "<name>"` line — it is configurable, so never assume `.shipd`. Hooks live at
   `<repo-root>/<name>/hooks/`, **in the checkout**, even where `config-show`
   reports a `store_root` relocating the rest of the content directory: a hook
   in an external store would not travel with a clone, and the create path
   would find nothing to run.
2. **Decide whether it needs a file.** A plain one-line command — `npm
   install`, `cp .env.example .env` — registers as that command line, with no
   file authored; go straight to step 4. Anything with several steps, a
   conditional, or a re-run guard is authored as a script.
3. **Author the script** at `<name>/hooks/<slug>.sh`, `<slug>` kebab-case for
   the step (`copy-env`, `seed-db`). Open it with `#!/usr/bin/env bash` and
   `set -e`. It runs with the **new worktree as its working directory**, and
   may read `SHIPD_WORKTREE` (the worktree's absolute path), `SHIPD_ROOT` (the
   repo root) and `SHIPD_CHANGE` (the change name) from the environment — the
   create path exports all three. Make it idempotent where it can be: `shipd
   worktree hooks run` re-runs the whole list inside an existing worktree. Make
   it **exit non-zero on failure** — the create path stops the chain at the
   first failure and exits `3`, leaving the worktree in place, so a swallowed
   error is a setup that silently did not happen. Then `chmod +x` it and show
   the user what you wrote before registering it.
4. **Register it** by its repo-relative path (never an absolute one — the
   config is checked in and has to work in every clone):
   ```sh
   shipd worktree hooks add "<name>/hooks/<slug>.sh"
   ```
   Two outcomes are not silent. A non-zero exit naming a duplicate means the
   item is already registered: report that and register nothing further. A
   `WARNING:` line about shadowing means an outer config layer declared its own
   list and this repo's new list now wins the key *wholesale* rather than
   extending it — relay it verbatim, naming the outer file, so the user can
   decide whether that layer's items need re-adding here.
5. **Verify, never assume.** Run `shipd worktree hooks list` and confirm the
   item appears, at which index and from which config file. If it does not,
   report that the registration did not take and stop — never declare success
   off the `add` command's own output alone. Close by saying the hook takes
   effect for everyone once the script and `.shipd-config.json` are committed,
   and runs on the next `shipd worktree <change>`.

**Asked what is registered**, run `shipd worktree hooks list` and report each
item with its index and declaring config file, then flag every **dangling
script**: for each item that reads as a path into `<name>/hooks/` rather than a
shell command line, check whether the file exists in the checkout and mark the
ones that do not — a registered hook whose script was deleted fails the next
create path with exit `3`. Offer to remove a dangling entry; never remove one
unprompted.

**Asked to remove a hook**, locate it first: run `shipd worktree hooks list`
and match the description against the items. No match is reported as such with
the listing shown, removing nothing; several matches are presented for the user
to pick one. Then name the matched item, its index, and its declaring config
file, and get the user's answer to two separate questions — whether to remove
the registration, and, where the entry points at a script under
`<name>/hooks/`, whether to delete that file too. Only on an affirmative run
`shipd worktree hooks remove "<item>"` (an index works too). On a non-zero
exit, surface the error and report that nothing was removed. Delete the script
file **only** when the user chose that, never as a side effect. Then read the
list back and show what remains.

You never create or remove a worktree here — `shipd worktree <change>` and
`"$S/worktree.sh" remove <change>` belong to the build flows; you only
configure what runs after a creation. To exercise a registered list, tell the
user to run `shipd worktree hooks run` from inside an existing worktree rather
than creating a throwaway worktree yourself. Report in a line or two what you
registered, browsed, or removed, the config file it lives in, and the files
still to commit. Then stop.
