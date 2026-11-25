<!-- description: Answer a how-to question about shipd from its own skills — the steps and commands to run, or an honest no. -->
# /s:help — answer a how-to question about shipd

Answer one how-to question from the installed skills and CLI help. You are
**read-only**: you change no file, run none of the suggested commands, and ask
through no dialog. With no question, ask for one in plain text and stop.
Never invent a command, flag, or workflow.

<!-- include:preamble -->

1. **Route decisions.** When the user asks for a project decision rather than
   how to do something, name `/s:ask <decision>` without invoking it, and stop.
2. **Read the sources.** Read each `"$S/../../"*/SKILL.md` frontmatter (the
   installed `skills/` folder), then open only the matching skills and the
   references they name. Run `"$S/../../../bin/shipd" --help` — `shipd --help`
   — when a CLI verb may answer. Open a skill before you name its command, and
   copy the command's syntax from that file. Cite a skill only after you open it. Take a
   `shipd` verb's syntax from `shipd --help`. Never answer from model memory,
   online docs, or repository state.
3. **Answer.** Open with exactly one verdict: `Supported` (numbered steps in
   the order to run them, as many as the task needs, with exact commands),
   `Partly supported` (the steps, then the gap), or `Not supported` (say so,
   then the nearest option or that there is none). Every step names the skill or
   verb that backs it. Then stop.
