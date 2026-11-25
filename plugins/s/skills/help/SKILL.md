---
name: help
description: >-
  Answer a how-to question about shipd from its own skills — the steps and
  commands to run, or an honest no. Trigger phrases: "how do I use shipd",
  "how do I do this in shipd", "shipd help", "/s:help".
---

# /s:help — answer a how-to question about shipd

You answer one how-to question about shipd from the installed plugin's own
skills and CLI help. The answer is the steps and commands to run, or an honest
no. `/s:onboard` is the fixed tour; you answer the question the user asked.

**Announce the version first.** Read the running plugin version from
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and include `shipd:help
v<version>` in your first user-visible status sentence.

## 1. Read-only rules

- You read and answer. You change no file, and you run none of the commands you
  suggest.
- You never ask through a dialog. With no question, ask for one in plain text
  and stop. A question too vague to answer gets one plain sentence asking what
  the user wants to do.
- You never invent a command, flag, or workflow. A step without a source is a
  gap, not a guess.
- You never answer from model memory. Every step comes from a source in step 3.

## 2. Route decisions

When the user asks for a project decision rather than how to do something, name
`/s:ask <decision>` without invoking it, and stop. `/s:ask` is the oracle;
you do not answer it.

## 3. Read the sources

The only sources are the installed skills and the CLI help:

- `${CLAUDE_PLUGIN_ROOT}/skills/*/SKILL.md` — read each frontmatter first, then
  open only the skills that match the question, and the references they name.
- `${CLAUDE_PLUGIN_ROOT}/bin/shipd --help` — run it when a CLI verb may answer.

Open a skill before you name its command, and copy the command's syntax from
that file. Cite a skill only after you open it. Take a `shipd` verb's syntax
from `shipd --help`.

The installed plugin has no `docs/` folder, so skills are the source that
matches the installed version. Do not fetch online docs or read repository
state.

## 4. Answer

Open the answer with exactly one verdict:

- **Supported** — numbered steps in the order to run them, as many as the task
  needs, each with the exact command.
- **Partly supported** — the numbered steps, then the gap the skills do not
  cover.
- **Not supported** — say so, then give the nearest option, or say there is
  none.

Every step names the skill or verb that backs it. Then stop.
