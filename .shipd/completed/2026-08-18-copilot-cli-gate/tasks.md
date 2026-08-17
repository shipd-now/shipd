## 1. The CLI reviewer path

- [x] 1.1 [req: gate-workflow-template] In
      `plugins/s/skills/build/tests/test_copilot_verb.py`, add failing
      tests for the CLI reviewer path in
      `plugins/s/integrations/copilot/copilot-review-gate.yml`: the
      `permissions` block gains `pull-requests: write`; the only secret
      references are `github.token` and
      `${{ secrets.COPILOT_GITHUB_TOKEN }}`, the latter reaching only the
      Copilot CLI's env and never a `gh` call; the `pull_request` path
      branches on the secret's emptiness; the CLI branch checks out the
      head with full history, installs difftastic, ripgrep, and
      `@github/copilot`, invokes `copilot` non-interactively
      (`-p`, `--allow-all-tools`) under a bounded `timeout` with a prompt
      naming the target repository's installed skill file (the SKILL.md
      that `shipd copilot add` writes under its skills directory) and
      forbidding self-posting, captures stdout to a workspace file, and posts the
      review text as a PR comment. Behavioral cases run the extracted
      script with stubbed `copilot`, `timeout`, `npm`, and `gh` binaries:
      marker-ending output → pending then strict terminal status plus the
      comment; `fix-required` last line → `failure`; output without a
      marker → fail-open `success`; CLI nonzero exit and simulated
      timeout → `pending` only; empty secret → the poll path behaves
      byte-for-byte as today (reuse the existing poll cases).
- [x] 1.2 [req: gate-workflow-template] Implement the CLI reviewer branch
      in `plugins/s/integrations/copilot/copilot-review-gate.yml` per the
      delta requirement and `plan.md`'s workflow contract, keeping the
      poll branch and the `pull_request_review` bridge untouched, reusing
      the existing windowed last-line classification for the captured
      output (workspace file + `$(<file)`, no pipes, no env-passed text),
      and updating the file-header commentary (two reviewer modes, secret
      scoping, timeout-leaves-pending). Make the 1.1 tests pass.

## 2. SKILL.md — one contract, two surfaces

- [x] 2.1 [req: skill-template] In `test_copilot_verb.py`, add failing
      `SkillTemplateTest` cases: the marker instruction states the marker
      is read from the body's last non-empty line by exact equality and no
      longer claims a substring match; the template names both consuming
      surfaces (GitHub's Copilot code-review runs and the gate workflow's
      headless Copilot CLI reviewer).
- [x] 2.2 [req: skill-template] Edit
      `plugins/s/integrations/copilot/SKILL.md`: replace the "exact
      substring match" sentence with the last-non-empty-line equality
      statement, and add the two-surfaces contract sentence to the scope
      section. Make the 2.1 tests pass.

## 3. Docs

- [x] 3.1 [req: copilot-review-guide] In `docs/copilot-review.md`, rework
      the merge-gate section into the two reviewer modes per the delta
      requirement: the CLI reviewer mode (secret setup with the "Copilot
      Requests" PAT permission, SKILL.md-driven headless run, strict
      status, review comment, private-repo support, ~10-credit cost,
      pending on failure/timeout) and the poll fallback (with the CCR
      surface's engine/marker limits stated as the reason its guarantee is
      fail-open); re-scope the private-repository note to poll mode.

## 4. Release

- [x] 4.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      `0.6.132` -> `0.6.133`.
- [x] 4.2 [req: *] Run the full engine suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) from
      the worktree root and confirm it passes without `textual` or
      `pydantic` installed.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 75 | 70.1k |
| Edit | 29 | 23.1k |
| Write | 8 | 20.2k |
| (no tool) | 0 | 6.6k |
| SendMessage | 5 | 5.0k |
| Read | 22 | 3.3k |
| Agent | 2 | 1.0k |
| ToolSearch | 1 | 364 |
| TaskList | 1 | 27 |
| **Total** | 143 | 129.6k |
