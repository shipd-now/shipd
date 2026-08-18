## 1. Credential isolation and base-pinned instructions

- [x] 1.1 [req: gate-workflow-template] In
      `plugins/s/skills/build/tests/test_copilot_verb.py`, add failing
      tests: the step invoking `copilot` binds `COPILOT_GITHUB_TOKEN` in
      its `env` and carries no `GH_TOKEN`/`github.token`; the step that
      classifies and posts binds `GH_TOKEN: ${{ github.token }}` and not
      the secret; before the CLI runs, the script materializes the
      reviewer instructions from the base ref (`git show` of the base
      ref's skill path into a workspace file) with a head-copy fallback
      plus log line when the base lacks the file, and the prompt names
      the materialized file (not the head's live path); the npm install
      pins `@github/copilot` to an exact version; the CLI path's
      fail-open description names the CLI review while the poll and
      review-event descriptions are unchanged. Behavioral cases via the
      existing stub harness: verdict/strict/failure matrices still hold
      across the step split (output travels via the workspace file), and
      the base-vs-head instructions selection is exercised for both the
      present and absent base-file cases.
- [x] 1.2 [req: gate-workflow-template] Restructure the CLI branch of
      `plugins/s/integrations/copilot/copilot-review-gate.yml` per the
      delta requirement: dedicated CLI step (secret-only env, prompt
      naming the materialized instructions file, stdout capture),
      separate classify-and-post step (github.token-only env), base-ref
      instruction materialization with head fallback, pinned
      `@github/copilot` version (the version verified live in this arc),
      distinct CLI fail-open description, updated header commentary.
      Preserve the windowed trim, no-pipe/no-env text handling, the
      strict-mode comment posting, and the test overrides. Make the 1.1
      tests pass.

## 2. Skill knob sync

- [x] 2.1 [req: skill-template] In `test_copilot_verb.py`, add a failing
      `SkillTemplateTest` case: the merge-gate scope bullet names
      `SHIPD_GATE_FAIL_OPEN`, the fail-open default, and that `false`
      leaves the status pending.
- [x] 2.2 [req: skill-template] Update the scope bullet in
      `plugins/s/integrations/copilot/SKILL.md` accordingly. Make the 2.1
      test pass.

## 3. Docs

- [x] 3.1 [req: copilot-review-guide] In `docs/copilot-review.md`, add
      the trust-boundary section per the delta requirement (same-repo
      workflow-with-secrets baseline, LLM content-injection residual,
      credential-isolated CLI step, base-pinned instructions, pinned CLI
      version, `review_gate.py post` as high assurance) and update the
      CLI-mode section for the base-pinned instructions and pinned
      version.

## 4. Release

- [x] 4.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      `0.6.134` -> `0.6.135`.
- [x] 4.2 [req: *] Run the full engine suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) and
      the review engine's suite (`python3 -m unittest discover -s
      plugins/s/skills/review/tests`) from the worktree root, confirming
      both pass without `textual` or `pydantic` installed.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 107 | 73.1k |
| Edit | 79 | 66.5k |
| (no tool) | 0 | 13.9k |
| SendMessage | 5 | 6.4k |
| Write | 2 | 6.3k |
| Read | 19 | 3.5k |
| Agent | 2 | 1.1k |
| **Total** | 214 | 170.8k |
