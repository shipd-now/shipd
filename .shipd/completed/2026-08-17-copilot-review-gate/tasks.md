## 1. Gate workflow template

- [x] 1.1 [req: gate-workflow-template] In
      `plugins/s/skills/build/tests/test_copilot_verb.py`, add a failing
      `GateWorkflowTemplateTest` over
      `plugins/s/integrations/copilot/copilot-review-gate.yml`: the marker
      line `# shipd-copilot v{version}`; triggers `pull_request` with types
      `opened`/`synchronize`/`reopened` and `pull_request_review` with type
      `submitted`; a `permissions` block granting `statuses: write`; the
      `pending` post on pull-request events; the reviewer-login guard
      `copilot-pull-request-reviewer[bot]` and the head-SHA (`commit_id`)
      guard; the mapping `<!-- shipd-verdict: fix-required -->` → `failure`,
      `<!-- shipd-verdict: ship-it -->` → `success`, neither marker →
      `success` with a no-verdict description; no `secrets.` reference; and
      no `requested_reviewers` request step.
- [x] 1.2 [req: gate-workflow-template] Add
      `plugins/s/integrations/copilot/copilot-review-gate.yml` satisfying
      the 1.1 contract: two `if`-gated jobs (one per trigger) posting the
      `semantic-review` status via
      `gh api repos/${{ github.repository }}/statuses/<head-sha>` with
      `GH_TOKEN: ${{ github.token }}`. Make the 1.1 tests pass.

## 2. Skill template verdict marker

- [x] 2.1 [req: skill-template] In `test_copilot_verb.py`, extend
      `SkillTemplateTest` with failing tests: the report instructions
      require ending the review body with a verdict line plus the matching
      `<!-- shipd-verdict: ship-it -->` or
      `<!-- shipd-verdict: fix-required -->` marker, and the scope section
      describes the gate workflow's fail-open bridging into the
      `semantic-review` status (advisory only where no gate workflow is
      installed).
- [x] 2.2 [req: skill-template] Edit
      `plugins/s/integrations/copilot/SKILL.md`: add the verdict-marker
      instruction to the report step and rewrite the `## Scope of this
      review` section per the delta requirement. Make the 2.1 tests pass.

## 3. Verb wiring — four managed files

- [x] 3.1 [req: copilot-verb] In `test_copilot_verb.py`, update
      `CopilotVerbTest` to a failing four-file contract: the bare report
      prints four state lines (all `absent` on an empty root); `add`
      installs all four files with version-substituted markers; `remove`
      deletes all four; a marker-less
      `.github/workflows/copilot-review-gate.yml` is `foreign`, refusing
      `add`/`remove` at exit `1` without `--force`.
- [x] 3.2 [req: copilot-verb] In `plugins/s/bin/shipd`, add the
      `COPILOT_GATE_WORKFLOW` path
      (`.github/workflows/copilot-review-gate.yml`) to `COPILOT_MANAGED`
      and a `COPILOT_TEMPLATED` entry
      (`copilot-review-gate.yml`, the `# shipd-copilot v(\S+)` pattern), and
      include its rendered payload in `_copilot_add`. Make the 3.1 tests
      pass.

## 4. Docs

- [x] 4.1 [req: copilot-review-guide] In `docs/copilot-review.md`, name the
      fourth managed file in the install section and add a merge-gate
      section after enablement covering: `pending` on pull-request
      open/update; `failure` on a `fix-required` marker; `success` on a
      `ship-it` marker or a marker-less review (fail-open); the session
      review flow as a coexisting poster of the same `semantic-review`
      context; and the fork read-only-token limit.

## 5. Release

- [x] 5.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      `0.6.126` -> `0.6.127`.
- [x] 5.2 [req: *] Run the full engine suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) from
      the worktree root and confirm it passes without `textual` or
      `pydantic` installed.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 90 | 32.4k |
| Edit | 34 | 21.7k |
| (no tool) | 0 | 9.0k |
| Write | 2 | 4.9k |
| Read | 28 | 4.2k |
| SendMessage | 2 | 1.2k |
| ToolSearch | 2 | 1.1k |
| Agent | 2 | 967 |
| WebSearch | 1 | 70 |
| **Total** | 161 | 75.5k |
