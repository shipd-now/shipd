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
   and read `unattended` and `content_dir`. When `unattended` is true, open no
   dialog: run `spec_status.py init` (`python3 "$S/spec_status.py" init`), report what
   it created, and stop.
2. **Parse the section.** With no argument, run the wizard in step 3. Any
   argument that is not one of the seven sections: list the seven and stop,
   writing nothing.
3. **Run the wizard.** Ask one key per question, in this order, current value
   (else the default) first:
   - Step 1, section `layout`: `dir` (`.shipd`, or Other for a relative path);
     `store_root` (keep files in the repo, or Other for a store path). Then run
     `spec_status.py init` to create the chosen folders.
   - Step 2, section `config`: `pr-mode` (`auto`, `draft`);
     `autonomous-pipeline` (`default`, `eco`, `basic`).
   - Step 3, section `config`: `memory_dir` (`$HOME/.shipd-memory` expanded, or
     Other for an absolute path); `wiki_base` (no base wiki, or Other for an
     absolute path).
   - Step 4, section `config`: `voice` (`true`, `false`); `guardrails` (keep
     every rule on, or `false` for all off).
   - Step 5, the wizard only: the constitution (step 6).
4. **Detect what is set.** Run `shipd config`. A key is set when its line ends
   in a file path in brackets, unset when absent or `[default]`. The bare
   wizard skips every set key; when none is left, say "nothing left to set up"
   (the constitution may still remain). A section run asks every key in that
   section.
5. **Write each answer** with `shipd config set <key> <value>`. An accepted
   default is written too, except where the default is the key's absence
   (`store_root`, `wiki_base`, `guardrails` left on), which writes nothing. On
   exit 1, relay the `error:` and `hint:` lines. If every `error:` names the
   key you set, ask it once more, then skip it with a note. If an `error:`
   names another key, offer to fix that key first through its own dialog, then
   retry the original once; never loop.
6. **Offer the constitution** only in the full wizard and only when
   `<content_dir>/constitution.md` is absent. On acceptance run
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

**Brief every question.** Open each question with the brief that
`skills/document/references/question-brief.md` defines, and follow its rule on
dialogs and typed rounds: one key per dialog, its brief in the question text
and option descriptions.
