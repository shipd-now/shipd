## 1. Hand-off build pointer on its own line

- [x] 1.1 [req: standalone-invocation] In `plugins/s/skills/plan/SKILL.md`,
      Ending step 3 ("Point at build"), rewrite the instruction so the
      summary's closing sentence ends with a colon and `/s:build` is placed
      alone on its own line after a blank line (e.g. "The change is ready to
      implement with:" — blank line — "/s:build"), instead of naming the
      command inline mid-sentence.
- [x] 1.2 [req: standalone-invocation] In `plugins/s/skills/plan/SKILL.md`,
      the enrichment re-gate exit bullet ("**Exit 0** — … point at
      `/s:build`"), state the same format for the motivation-led hand-off:
      colon-terminated closing sentence, blank line, `/s:build` alone on its
      own line.
- [x] 1.3 [req: standalone-invocation] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` one patch above the branch's
      current value (0.6.126 → 0.6.127 at planning time).

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 3 | 4.3k |
| **Total** | 3 | 4.3k |
