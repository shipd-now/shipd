## 1. Trim the concept doc

- [x] 1.1 [req: room-skill-docs] Replace `docs/multi-agent-pr.md` with the
      exact text of `artefacts/multi-agent-pr.md`.
- [x] 1.2 [req: room-skill-docs] Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/multi-agent-pr.md`
      and confirm exit 0 with no warnings.
- [x] 1.3 [req: room-skill-docs] Confirm `docs/multi-agent-pr.md` is 100 lines
      or fewer, names all six task states, `room.max_rounds`, `/s:room`, and
      `shipd copilot add --room`, and holds no `input_required` or `hyphen`
      outside its Mermaid block.
- [x] 1.4 [req: room-skill-docs] Render the Mermaid block with
      `npx -y @mermaid-js/mermaid-cli -i <file>` (or the GitHub preview), and
      confirm the diagram shows the label `input-required`.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 15 | 4.9k |
| SubagentHandback | 2 | 1.3k |
| Agent | 2 | 969 |
| (no tool) | 0 | 76 |
| **Total** | 19 | 7.2k |
