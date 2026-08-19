# copilot-skill

Status: verified

## Idea

Add a `/s:copilot` skill that sets up the shipd semantic review gate end to
end from within the harness — install the files, commit and push them,
protect the default branch, walk the strict-reviewer hand-off, and verify —
so a repo leaves the flow with PRs blocked on a fix-required verdict and
merging on ship-it.

### Motivation

Setting up the copilot gate today is a manual two-step with a seam in the
middle — run `shipd copilot add` by hand, commit, then `/s:doctor` — and
nothing guides a repo into the strict configuration the gate needs before a
PR carrying findings is actually blocked while a clean one merges.

### Details

- New `/s:copilot` skill: preflight (git repo, GitHub remote, `gh` auth) →
  `shipd copilot add` → consented commit/push of the four files → one batched
  consent round (branch protection via `review_gate.py protect`, auto-merge
  enable, optional strictness knob) → strict-reviewer hand-off → `shipd
  doctor` verification report.
- `review_gate.py protect` learns to create protection on an unprotected
  default branch (today its protection GET 404s and the verb fails), so the
  fresh-repo case works.
- New harness body template `plugins/s/harness/bodies/copilot.md` — the
  bodies/skills id-set equality is test-enforced, so it lands with the skill.
- Registration: README skills table, AGENTS.md enumeration,
  `docs/copilot-review.md` mention, plugin version bump.

Affected capabilities: `shipd-copilot` (added), `semantic-review` (modified).
Impact: `plugins/s/skills/copilot/SKILL.md`,
`plugins/s/harness/bodies/copilot.md`,
`plugins/s/skills/review/scripts/review_gate.py`,
`plugins/s/skills/review/tests/test_review_gate.py`, `README.md`,
`AGENTS.md`, `docs/copilot-review.md`, `plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No automation of the PAT mint or `gh secret set` — both stay interactive
  hand-offs, exactly as `docs/copilot-review.md` documents them.
- No branch-ruleset creation for automatic Copilot review — that remains a
  Settings-UI hand-off note.
- No change to the `shipd copilot add` CLI verb or its no-network contract.
- No new doctor checks — the skill consumes the three shipped in
  `doctor-github-settings`, it does not extend them.

## Implementation

- **The skill orchestrates existing engines; it invents no mechanism.**
  Install is `shipd copilot add` (binary resolved as the doctor skill does:
  `shipd` on PATH, else `${CLAUDE_PLUGIN_ROOT}/bin/shipd`); protection is
  `review_gate.py protect`; verification is `shipd doctor`'s three
  GitHub-side checks. Rejected: doctor-style raw `gh api` protection calls in
  the skill — `protect` preserves every existing protection field, adds
  conversation resolution (which the disposition loop needs), and is
  idempotent, so it is strictly better where it works.
- **`protect` gains 404 tolerance instead of the skill special-casing.** A
  404 on the protection GET means "no protection yet": build the PUT from an
  empty current object, creating protection whose required status checks are
  `{strict: false, contexts: ["semantic-review"]}` with conversation
  resolution required and every other field null/absent. `strict: false` on
  fresh creation matches the doctor remedy's minimal body — `strict: true`
  would stall auto-merged PRs behind base until manually updated. An
  already-protected branch keeps today's preserve-everything behavior,
  including its existing `strict`. Any non-404 GET failure still fails the
  verb — only the known "unprotected" shape is tolerated.
- **Consent mirrors the doctor contract.** One batched selection over the
  runnable mutations (commit+push the four files, `protect`, auto-merge
  enable via `gh api -X PATCH repos/<nwo> -F allow_auto_merge=true`, optional
  `gh variable set SHIPD_GATE_FAIL_OPEN --body false`), honoring the
  dialog-prose separation rule; hand-offs (`! gh auth login`,
  `! gh secret set COPILOT_GITHUB_TOKEN`) are never dialog options; declining
  everything runs nothing.
- **The strict reviewer is the recommended path, stated honestly.** The
  user-facing goal — blocked on fix-required, through on ship-it — holds only
  with branch protection plus the CLI reviewer (`COPILOT_GITHUB_TOKEN`); the
  poll fallback is fail-open. The skill relays the minimal-PAT recipe from
  `docs/copilot-review.md` and hands off the secret set; when the user skips
  it, the skill states plainly that the gate is advisory until the secret
  exists. The `SHIPD_GATE_FAIL_OPEN=false` knob is offered as an option with
  its trade-off stated (a marker-less review leaves the check pending, which
  can stall PRs until a session posts the gate).
- **pr-mode aware.** When the layered config resolves `pr-mode: draft`, the
  auto-merge enable option is omitted with a note — that flow never arms
  auto-merge (same waiver the doctor `automerge` check applies).
- **Push fallback.** If pushing the four files to the current branch is
  rejected (an already-protected branch), the skill falls back to a
  `shipd-copilot-install` branch and an auto-merging PR, and says so.
- **Body template stays ungated.** `harness/bodies/copilot.md` is a distilled
  router with the required description marker and no `if:` gates, so no
  fallback reference file is required (gated-segments-only rule in
  `harness-command-bodies`).
- **Version bump.** `plugins/s/.claude-plugin/plugin.json` bumps from the
  version current at ship time (0.6.143 as of planning) to the next patch, in
  the same PR.

Risk: `protect` and the auto-merge PATCH need admin — an API denial is
reported as that step's failure with the manual hint, and the remaining
consented steps still run. Risk: a repo that never completes the PAT hand-off
believes it is gated — mitigated by the skill's closing `shipd doctor` report,
which shows `warn copilot-secret` naming the fail-open fallback.
