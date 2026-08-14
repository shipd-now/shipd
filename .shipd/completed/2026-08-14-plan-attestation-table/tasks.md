## 1. Attestation table format

- [x] 1.1 [req: readiness-attestation] In
      `plugins/s/skills/plan/references/readiness.md`, rewrite the
      "Attestation — evidence, printed, before emission" section: the
      attestation is printed as a markdown table with one cited row per
      checklist item (columns `#`, `Item`, `Evidence`). Keep every per-item
      evidence standard unchanged (items 1–3 cite a capability name,
      `file:line`, or requirement id; item 4 names each task-shaping decision
      and its settling rung or states none remain; verified runnable premises
      appear in item 3's evidence cell with their observations), and replace
      the closing "one cited line per checklist item" instruction with the
      table contract.
- [x] 1.2 [req: readiness-attestation] In
      `plugins/s/skills/plan/SKILL.md` step 5 ("Check readiness"), replace
      "one cited line per checklist item" with "a markdown table with one
      cited row per checklist item", leaving the rest of the step unchanged.
- [x] 1.3 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.97` to `0.6.98`.
