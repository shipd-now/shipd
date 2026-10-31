---
name: init
description: >-
  Set up shipd in a project — a guided first-run wizard, or one section on
  demand — through the engine's init and config verbs. Trigger phrases: "set up
  shipd", "initialise shipd", "shipd setup wizard", "/s:init".
---

# /s:init — set up shipd in a project

You are the **front door to shipd setup**. A new project has no layout, and
every choice (where files live, how changes ship, where personal stores sit)
would otherwise be a hand edit of JSON. You ask one question per key and write
each answer through `shipd config set`.

**You never hand-edit `.shipd-config.json`.** The `config set` verb owns the
file's format, validation, and layer choice. Editing it directly bypasses all
of that.

**Announce the version first.** Read the running plugin version from
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and include
`shipd:init v<version>` in your first user-visible status sentence (e.g.
"shipd:init v0.6.174 — checking the project"), so the user can always see which
plugin snapshot the session is running.

An **invocation argument** names one section to run alone: `layout`, `config`,
`workspace`, `wiki`, `memory`, `hooks`, or `gate`. With no argument, run the
full wizard.

## Harness plan mode

**Harness plan mode never replaces this skill's output.** When the session
is in the harness's plan mode, run only this skill's read-only steps. Stop
before the first write and ask the user to exit plan mode and re-invoke.
Never write the harness plan file, call `ExitPlanMode`, or mix in plan
mode's outputs. Details:
`${CLAUDE_PLUGIN_ROOT}/skills/document/references/harness-plan-mode.md`.

## 1. Resolve the binary and check the project

Resolve the `shipd` binary in this order and use the first that exists:

1. `shipd` on `PATH` (`command -v shipd`).
2. `${CLAUDE_PLUGIN_ROOT}/bin/shipd`.

If neither resolves, report that the binary cannot be found, name both
locations you tried, and stop. Do not fall back to editing the config by hand.

Path notation: literal `.shipd/` paths in this skill denote the repo's resolved
content directory (default `.shipd`) — resolve the actual name with
`spec_status.py config-show` (its `content-dir:` line) and substitute it when
the repo configures another.

Check the project:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" init-status --json
```

Read `unattended` and `content_dir` from the JSON. **While `unattended` is
true, open no dialog**: run
`python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" init`,
report what it created, and stop.

## 2. Parse the section

With no argument, run the wizard (step 3). If the argument is not one of the
seven sections (`layout`, `config`, `workspace`, `wiki`, `memory`, `hooks`,
`gate`), list the seven and stop without writing anything.

## 3. The wizard

Ask one key per AskUserQuestion, in the order below, listing the key's current
value (else its default) first. Pass each value to `shipd config set <key>
<value>` unquoted, with no `--layer`: the engine picks the file.

| Step | Section | Key | Options (default first) | Writes on default |
| --- | --- | --- | --- | --- |
| 1 Where files live | `layout` | `dir` | `.shipd`; Other (a relative path) | yes, `.shipd` |
| 1 Where files live | `layout` | `store_root` | keep files in the repo; Other (a store path) | no |
| 2 How changes ship | `config` | `pr-mode` | `auto`; `draft` | yes, `auto` |
| 2 How changes ship | `config` | `autonomous-pipeline` | `default`; `eco`; `basic` | yes, `default` |
| 3 Personal stores | `config` | `memory_dir` | `$HOME/.shipd-memory` expanded; Other (an absolute path) | yes |
| 3 Personal stores | `config` | `wiki_base` | no base wiki; Other (an absolute path) | no |
| 4 Session behaviour | `config` | `voice` | `true`; `false` | yes, `true` |
| 4 Session behaviour | `config` | `guardrails` | keep every rule on; `false` (all off) | no |
| 5 Constitution | wizard only | `constitution.md` | add the starter; skip | n/a (a file, not config) |

Step 1 ends by running `spec_status.py init`:
`python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" init`,
which creates the folders the chosen `dir` and `store_root` resolve to. The
value is the option's literal (`false`, `auto`, a path); `shipd config set`
parses JSON first and falls back to a plain string, so no quoting is needed.

**Detect what is set.** Run `shipd config`. A key is set when its line ends in
a file path in brackets, and unset when it is absent or marked `[default]`. The
bare wizard skips every set key; when none is left, say "nothing left to set
up" (the constitution step may still remain). A section run asks every key in
that section, set or not, with the current value listed first.

**Write each answer** with `shipd config set <key> <value>`. An accepted
default is written too, so the step counts as set next time, except where the
default is the key's absence (`store_root`, `wiki_base`, `guardrails` left on):
that writes nothing. When `config set` exits 1, relay its `error:` and
`hint:` lines.

- Where every `error:` line names the key you set, ask that key once more, then
  skip it with a note.
- Where an `error:` line names a different key, offer to fix that key first
  through its own dialog and `config set`, then retry the original key once.
  Never re-ask the original key in a loop.

**The constitution (step 5).** In the full wizard only, and only when
`<content_dir>/constitution.md` is absent, offer the starter. On acceptance:

```
cp -n "${CLAUDE_PLUGIN_ROOT}/skills/init/references/constitution-starter.md" \
  <content_dir>/constitution.md
```

`cp -n` cannot overwrite. No section run writes a constitution, and an existing
one is never touched.

**Brief every question.** Open each question with the brief that
`${CLAUDE_PLUGIN_ROOT}/skills/document/references/question-brief.md` defines,
and follow its rule on dialogs and typed rounds: one key per dialog, the brief
in the question text and option descriptions, current value first.

## 4. On-demand sections

These never run in the bare wizard. Relay each verb's output and do not restate
a handed-off skill's steps.

| Section | What it runs |
| --- | --- |
| `workspace` | `shipd workspace`; when none resolves, one path dialog, then `spec_status.py workspace-init <path>` |
| `wiki` | `spec_status.py wiki-init` |
| `memory` | `spec_status.py wiki-init --personal` |
| `hooks` | hands off to `/s:worktree-hooks` |
| `gate` | hands off to `/s:gate` |

`spec_status.py` lives at
`${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py`.

## End

Report in a few lines what was set and where, then list the on-demand sections
(`workspace`, `wiki`, `memory`, `hooks`, `gate`) the user can still run with
`/s:init <section>`. Then stop.
