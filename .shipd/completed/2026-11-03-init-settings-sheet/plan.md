# init-settings-sheet
Status: verified
Theme: developer-experience
Planned-at: fe3877fb27077c0ea1322feb4568ba95129cb37e
Gated-hash: c83f805e1ec2

## Idea

Replace the `/s:init` wizard's nine one-key dialogs with one numbered settings
sheet that the user accepts with `ok` or edits by line number.

### Motivation

A new user running `/s:init` (or a first `/s:plan`) has to answer up to nine
dialogs in a row, even when they want every default. They cannot see all the
settings at once, and accepting the defaults costs one click per key.

### Details

- The wizard prints one sheet: line number, key, current value or default, and
  a short gloss. It ends the turn and opens no AskUserQuestion.
- The user replies `ok` to accept all, or `3 draft, 7 false` to change lines.
- Keys a config layer already sets show in an unnumbered
  `Already set (kept):` block.
- A failed `config set` gets one retry sheet holding only the failed lines.
- The constitution offer becomes the sheet's last line.

Affected capabilities: `shipd-init` (modified: `init-wizard-steps`,
`init-constitution-starter`). Impact: `plugins/s/skills/init/SKILL.md`,
`plugins/s/harness/bodies/init.md`,
`plugins/s/skills/build/tests/test_init_skill_contract.py`, `README.md`,
`plugins/s/.claude-plugin/plugin.json`. No engine script changes.

### Non-goals

- No change to `shipd config set`, `shipd config`, `init-status`, or the
  needs-setup reference.
- No change to the on-demand sections (`workspace`, `wiki`, `memory`,
  `hooks`, `gate`); the `workspace` path dialog stays.
- No editable config file for the user to fill in.

## Implementation

- **One sheet, one typed reply.** The sheet layout, glosses, and reply
  grammar are fixed in `artefacts/settings-sheet.md`; the skill embeds them
  verbatim. Rejected: one AskUserQuestion with several questions, because
  AskUserQuestion caps at four questions and the wizard has nine keys.
  Rejected: writing a draft config file for the user to edit, because the
  `config set` verb owns the file's format and layer choice.
- **Line numbers, not key names, in the reply.** `3 draft` is shorter than
  `pr-mode draft` and matches what the user asked for. Numbering covers the
  unset lines only, so a set key never takes a number.
- **Write order.** Layout lines (`dir`, `store_root`) write first, then
  `spec_status.py init` runs, then the config keys in sheet order, then the
  constitution. This keeps the existing rule that the layout step ends with
  `init`.
- **Absence defaults write nothing.** Accepting `store_root`, `wiki_base`, or
  `guardrails` at their default runs no `config set`, as today.
- **Error handling.** The skill collects exit-1 failures while writing the
  other lines, then prints one retry sheet. That sheet holds the failed lines
  plus any other key an `error:` line names, and the skill writes the other
  key first. A second failure is skipped with a note. This replaces the
  per-dialog re-ask and keeps the no-loop rule.
- **Bad reply.** An out-of-range line or unparseable reply re-prints the
  sheet once with a note. A second bad reply stops with nothing written, so
  the wizard never half-applies a reply it could not read.
- **Brief.** The sheet's gloss column is each key's brief. The
  question-brief reference still governs the `workspace` path dialog.
- **Test.** The contract test drops its `AskUserQuestion` assertion and pins
  `settings sheet`, `Already set (kept):`, and the `3 draft, 7 false` example.
  It also asserts that `one key per` is gone from both texts.
- **Version.** `plugins/s/` changes, so the plugin version bumps one patch
  (AGENTS.md).

Risk: a reply value with a comma (a path) could split wrongly. The grammar
splits pairs on commas and new lines, so a path holding a comma must go on
its own line. The artefact's examples use plain paths.

## Readiness attestation

### Problem and motivation

The first-run wizard opens nine dialogs in a row; the user wants every default
shown at once and to change only a few.

Evidence:

- `plugins/s/skills/init/SKILL.md:73` — "Ask one key per AskUserQuestion".
- Requirement `init-wizard-steps` — "It SHALL ask one AskUserQuestion per
  key".
- The user's request: "kept asking questions after question".

### Scope and non-goals

How the bare wizard and section runs ask changes; config verbs, on-demand
sections, and needs-setup do not.

Evidence:

- In scope: `plugins/s/skills/init/SKILL.md:71-127`,
  `plugins/s/harness/bodies/init.md:24-66`.
- Out of scope: `plugins/s/skills/init/references/needs-setup.md`,
  requirement `init-handoff-sections`.

### Affected capabilities and files

One capability, two of its requirements, and five files.

Evidence:

- Capability `shipd-init`: `init-wizard-steps` (base ddd1967528f6),
  `init-constitution-starter` (base 7dd8667d3ec0), from
  `spec_status.py base-hash`.
- Files: `plugins/s/skills/init/SKILL.md:9-127`,
  `plugins/s/harness/bodies/init.md:24-67`,
  `plugins/s/skills/build/tests/test_init_skill_contract.py:68`,
  `README.md:263`, `plugins/s/.claude-plugin/plugin.json:3`.
- Runnable premise: `plugins/s/bin/shipd config` → exit 0; set keys end in a
  bracketed file path (`valid_themes … [/…/.shipd-config.json]`), unset ones
  in `[default]`.

### No open task-shaping decision

Every decision is settled.

Evidence:

- Sheet instead of dialogs, edit by line number: settled by the user's
  request.
- Reply grammar, set-key block, write order, retry rule: settled by
  investigation against the existing spec's rules.
- Personal memory store: no `memory-*` pages, none applied.
