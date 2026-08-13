## 1. Mutually exclusive turn endings

- [x] 1.1 [req: investigation-findings-digest] In
      `plugins/s/skills/plan/SKILL.md` Flow step 2, make the two endings
      mutually exclusive: with open task-shaping questions, end the turn on
      the **OPEN QUESTIONS** list — no go-ahead prompt, no
      clear-enough-to-proceed phrasing; the user's next message (answers,
      corrections, or a bare go-ahead) is folded in and remaining questions
      carry into the post-gate rounds. Without open questions, end on the
      typed go-ahead prompt exactly as today. Update step 3's parenthetical
      to cover both reply shapes.

## 2. Version

- [x] 2.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version from
      0.3.1 to 0.3.2 (plugin content changed: plan skill edited).
