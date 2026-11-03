<!-- description: Set up shipd in a project — a guided first-run wizard, or one section on demand — through the engine's init and config verbs. -->
# /s:init — set up shipd in a project

Walk a user through first-run setup: where the files live, how changes ship,
the personal stores, session behaviour, and an optional constitution. Every
choice is written through `shipd config set`; never hand-edit
`.shipd-config.json`. An argument names one section to run alone: `layout`,
`config`, `workspace`, `wiki`, `memory`, `hooks`, or `gate`. Bare `/s:init`
runs the full wizard.

<!-- include:preamble -->

The config verb runs as `shipd config set <key> <value>` using the binary on
PATH or `"$S/../../../bin/shipd"`. Pass the value unquoted, with no `--layer`,
so the engine picks the file.

1. **Check the project.** Run `python3 "$S/spec_status.py" init-status --json`
   and read `unattended` and `content_dir`. When `unattended` is true, print no
   sheet and open no dialog: run `spec_status.py init` (`python3 "$S/spec_status.py" init`), report what
   it created, and stop.
2. **Parse the section.** With no argument, run the wizard in step 3. Any
   argument that is not one of the seven sections: list the seven and stop,
   writing nothing.
3. **Print the settings sheet.** Show every key on one settings sheet as plain
   response text, open no dialog, and end the turn. Each line has a number, the
   key, its current value (else the default), and a short gloss. The keys, in
   order:
   - Step 1, section `layout`: `dir` (`.shipd`, a relative path); `store_root`
     (in the repo, or a store path).
   - Step 2, section `config`: `pr-mode` (`auto`, `draft`);
     `autonomous-pipeline` (`default`, `eco`, `basic`).
   - Step 3, section `config`: `memory_dir` (`$HOME/.shipd-memory` expanded, an
     absolute path); `wiki_base` (none, or an absolute path).
   - Step 4, section `config`: `voice` (`true`, `false`); `guardrails` (`on`,
     or `false` for all off).
   - Step 5, the wizard only: the `constitution` line (`add`, `skip`).

   The sheet ends with: Reply "ok" to accept every line, or give the line
   number and the new value, e.g. "3 draft, 7 false". `ok`, `yes`, `accept`,
   or an empty reply accepts every line; `<n> <value>` changes line `n`, pairs
   separated by commas or new lines (a value holding a comma goes on its own
   line). An out-of-range line or unparseable reply re-prints the sheet once
   with a note; a second bad reply stops with nothing written.
4. **Detect what is set.** Run `shipd config`. A key is set when its line ends
   in a file path in brackets, unset when absent or `[default]`. The bare
   wizard moves every set key into an unnumbered `Already set (kept):` block
   with its value and file, numbers the unset lines only, and prints "nothing
   left to set up" when no numbered line remains. A section run numbers every
   key in that section, with no `Already set (kept):` block and no constitution
   line.
5. **Write each answer** with `shipd config set <key> <value>`, in this order:
   `dir` and `store_root` first, then `spec_status.py init` to create the
   chosen folders, then the config keys in sheet order, then the constitution.
   An accepted default is written too, except where the default is the key's
   absence (`store_root`, `wiki_base`, `guardrails` left on), which writes
   nothing. Collect exit-1 failures, relay each `error:` and `hint:` line, and
   print one retry sheet holding only the failed lines plus any other key an
   `error:` line names, writing that other key first. Skip a second failure
   with a note; never print a second retry sheet.
6. **Offer the constitution** as the sheet's last line, only in the full wizard
   and only when `<content_dir>/constitution.md` is absent. On `add` run
   `cp -n "${CLAUDE_PLUGIN_ROOT}/skills/init/references/constitution-starter.md"
   <content_dir>/constitution.md`. A section run never writes one, and nothing
   overwrites an existing file.
7. **Hand-off sections** run only on demand, relaying each verb's output
   without restating a handed-off skill: `workspace` runs `shipd workspace`
   and, when none resolves, asks one path dialog then runs
   `python3 "$S/spec_status.py" workspace-init <path>`; `wiki` runs
   `python3 "$S/spec_status.py" wiki-init`; `memory` runs
   `python3 "$S/spec_status.py" wiki-init --personal`; `hooks` hands off to
   `/s:worktree-hooks`; `gate` hands off to `/s:gate`.
8. **Close** with a short summary of what was set and a line listing the
   on-demand sections: `workspace`, `wiki`, `memory`, `hooks`, `gate`.

**Brief.** The sheet's gloss column is the brief for each key. The `workspace`
section's single path dialog still follows
`skills/document/references/question-brief.md`.
