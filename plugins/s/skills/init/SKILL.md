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
would otherwise be a hand edit of JSON. You show every key on one settings sheet, take one typed reply, and
write each answer through `shipd config set`.

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
true, print no sheet and open no dialog**: run
`python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" init`,
report what it created, and stop.

## 2. Parse the section

With no argument, run the wizard (step 3). If the argument is not one of the
seven sections (`layout`, `config`, `workspace`, `wiki`, `memory`, `hooks`,
`gate`), list the seven and stop without writing anything.

## 3. The wizard

Print one **settings sheet** as plain response text, open no AskUserQuestion,
and end the turn. The user replies with `ok` or with line numbers and new
values. Each value column shows the key's current value, else its default.
Pass each value to `shipd config set <key> <value>` unquoted, with no
`--layer`: the engine picks the file.

| Step | Section | Key | Sheet default | Gloss | Writes on default |
| --- | --- | --- | --- | --- | --- |
| 1 Where files live | `layout` | `dir` | `.shipd` | where shipd files live (a relative path) | yes, `.shipd` |
| 1 Where files live | `layout` | `store_root` | in the repo | or a store path, to keep files outside the repo | no |
| 2 How changes ship | `config` | `pr-mode` | `auto` | auto \| draft (draft stops at an open draft PR) | yes, `auto` |
| 2 How changes ship | `config` | `autonomous-pipeline` | `default` | default \| eco \| basic | yes, `default` |
| 3 Personal stores | `config` | `memory_dir` | `$HOME/.shipd-memory` expanded | your personal memory store (an absolute path) | yes |
| 3 Personal stores | `config` | `wiki_base` | none | or an absolute path to a base wiki | no |
| 4 Session behaviour | `config` | `voice` | `true` | true \| false (the shipd writing voice in replies) | yes, `true` |
| 4 Session behaviour | `config` | `guardrails` | `on` | on \| false (false turns every rule off) | no |
| 5 Constitution | wizard only | `constitution` | add the starter | add \| skip | n/a (a file, not config) |

The bare wizard on a fresh project prints this sheet:

```text
shipd setup: 9 settings. Each line shows the default.

  1  dir                  .shipd                   where shipd files live (a relative path)
  2  store_root           in the repo              or a store path, to keep files outside the repo
  3  pr-mode              auto                     auto | draft (draft stops at an open draft PR)
  4  autonomous-pipeline  default                  default | eco | basic
  5  memory_dir           /Users/me/.shipd-memory  your personal memory store (an absolute path)
  6  wiki_base            none                     or an absolute path to a base wiki
  7  voice                true                     true | false (the shipd writing voice in replies)
  8  guardrails           on                       on | false (false turns every rule off)
  9  constitution         add the starter          add | skip

Reply "ok" to accept every line.
To change lines, give the line number and the new value, e.g. "3 draft, 7 false".
```

The reply grammar:

- `ok`, `yes`, `accept`, or an empty reply accepts every line as shown.
- `<n> <value>` changes line `n`. Separate several pairs with commas or new
  lines. Lines the reply does not name keep the shown value. A value holding a
  comma (a path) goes on its own line.
- A line number outside the sheet, or a reply that fits none of the forms
  above, re-prints the sheet once with a one-line note naming the problem. A
  second unparseable reply stops the wizard with nothing written.
- A section run (`layout` or `config`) numbers every key in that section, set
  or not, with the current value shown. It has no `Already set (kept):` block
  and no constitution line.

**Detect what is set.** Run `shipd config`. A key is set when its line ends in
a file path in brackets, and unset when it is absent or marked `[default]`. The
bare wizard moves every set key into an unnumbered `Already set (kept):` block
above the numbered lines, with its value and the file that sets it; a set key
takes no line number, and the numbering covers the unset lines only, from 1.
When no numbered line remains, print "nothing left to set up" instead of a
sheet.

**Write each answer** with `shipd config set <key> <value>`, in this order:
write `dir` and `store_root` first, then run `spec_status.py init`:
`python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" init`,
which creates the folders the chosen `dir` and `store_root` resolve to; then
the config keys in sheet order; then the constitution. The value is the
literal (`false`, `auto`, a path); `shipd config set` parses JSON first and
falls back to a plain string, so no quoting is needed. An accepted default is
written too, so the line counts as set next time, except where the default is
the key's absence (`store_root`, `wiki_base`, `guardrails` left on): that
writes nothing.

Collect every `config set` exit-1 failure while writing the other lines, then
relay each `error:` and `hint:` line and print one retry sheet holding only
the failed lines plus any other key an `error:` line names. Write that other
key first, then retry the failed lines. Skip a second failure with a note and
never print a second retry sheet.

**The constitution (step 5).** The starter is the sheet's `constitution` line
(`add` | `skip`), present only in the bare wizard and only when
`<content_dir>/constitution.md` is absent. On `add`:

```
cp -n "${CLAUDE_PLUGIN_ROOT}/skills/init/references/constitution-starter.md" \
  <content_dir>/constitution.md
```

`cp -n` cannot overwrite. No section run writes a constitution, and an existing
one is never touched.

**Brief.** The sheet's gloss column is the brief for each key. The `workspace`
section's single path dialog still follows
`${CLAUDE_PLUGIN_ROOT}/skills/document/references/question-brief.md`.

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
