## 1. Go-ahead dialog

- [x] 1.1 [req: investigation-findings-digest] In
      `plugins/s/skills/plan/SKILL.md`, rewrite Flow step 2's ending: after
      printing the digest (+ requested diagram), issue exactly one go-ahead
      AskUserQuestion — "Is this clear enough to proceed?" with options
      proceed (recommended, first), adjust scope first, stop — and end the
      turn on it. Keep the bans explicit: the dialog only follows the
      printed digest, carries no planning decisions, and no other
      AskUserQuestion or depth-gate verdict appears in the investigation
      turn. Note the follow-ups: on adjust-scope, fold the notes in and show
      a one-line delta; on stop, end politely.

## 2. Version

- [x] 2.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version from
      0.2.12 to 0.2.13 (plugin content changed: plan skill edited).
