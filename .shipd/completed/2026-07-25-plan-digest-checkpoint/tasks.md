## 1. Checkpoint flow

- [x] 1.1 [req: investigation-findings-digest] In
      `plugins/s/skills/plan/SKILL.md`, rewrite Flow step 2 as "Report
      findings and stop": the digest (plus the requested solution diagram
      when the user asked for one) is the final message of the investigation
      turn — end the turn there and wait for the user's go-ahead; the
      investigation turn must not contain an AskUserQuestion call or a
      depth-gate verdict. Update step 3 to run on the go-ahead turn, folding
      in whatever the user's response changed about scope.

## 2. Version

- [x] 2.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version from
      0.2.11 to 0.2.12 (plugin content changed: plan skill edited).
