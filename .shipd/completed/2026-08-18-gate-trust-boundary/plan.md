# gate-trust-boundary
Status: verified

## Idea

Harden the CLI reviewer's trust boundary: the Copilot CLI step runs with no
credential but its own minimal token, its instructions come from the base
ref rather than the ref under review, its version is pinned, and the
boundary is documented — closing the security finding the reviewer raised
against its own upgrade pull request.

### Motivation

The first strict CLI review in production blocked its own upgrade PR with
a medium security finding: the CLI runs `--allow-all-tools` in a step
whose environment also holds the write-scoped `github.token`, following
instructions sourced from the ref under review — so adversarial content
in a reviewed change could steer the agent into forging the required
status, posting comments, or exfiltrating credentials. Three lows rode
along: the fail-open description is reused imprecisely on the CLI path,
SKILL.md's gate bullet omits the strictness knob, and the CLI install is
unpinned.

### Details

- `integrations/copilot/copilot-review-gate.yml`: split the CLI run into
  its own step whose environment carries only `COPILOT_GITHUB_TOKEN`
  (never `github.token`); classify and post from a separate step holding
  only `github.token`; materialize the reviewer instructions from the
  base ref's installed skill (head fallback for first installs); pin
  `@github/copilot` to an exact version; give the CLI path's fail-open
  outcome its own description.
- `integrations/copilot/SKILL.md`: the merge-gate bullet names
  `SHIPD_GATE_FAIL_OPEN` and both behaviors.
- `docs/copilot-review.md`: a trust-boundary section.
- Version bump `0.6.134` -> `0.6.135`.

Affected capabilities: `copilot-review-skill` (modified),
`project-readme` (modified). Impact:
`plugins/s/integrations/copilot/copilot-review-gate.yml`,
`plugins/s/integrations/copilot/SKILL.md`,
`plugins/s/skills/build/tests/test_copilot_verb.py`,
`docs/copilot-review.md`, `plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No narrowing of `--allow-all-tools` — the reviewer needs the shell for
  the engine, and the effective boundary is credential isolation, not
  tool lists.
- No change to the poll or review-event paths, the knob, or the verb.
- No claim of eliminating content injection against an LLM reviewer — the
  residual risk is documented, with the session flow
  (`review_gate.py post`) named for high-assurance review.

## Implementation

- **Credential isolation is the security fix, ADR-style.** The CLI
  invocation moves to its own step whose `env:` binds exactly
  `COPILOT_GITHUB_TOKEN` — `github.token` is absent from the CLI's
  process environment, so a steered agent cannot post statuses or
  comments; its only credential is the documented minimal PAT (no
  repository access, Copilot Requests only), bounding the worst case at
  quota burn plus a misleading review body. Classification, status
  posting, and the comment move to a following step whose `env:` binds
  `GH_TOKEN: github.token` and not the secret; the body travels between
  steps as the existing workspace file. Rejected: narrowing the tool
  allowlist — the engine needs the shell, and an allowlist cannot remove
  credentials from the environment.
- **Same-repo baseline, stated honestly.** A same-repo branch PR already
  runs its own edited workflow file with repository secrets — that is
  GitHub's model, not this template's doing — so the marginal threat is
  adversarial *content* steering the reviewer without push rights, and
  blast radius once steered. The docs section states both.
- **Instructions pin to the base ref.** Before invoking the CLI, the
  workflow materializes the skill file from the base ref
  (`git show origin/<base>:.github/skills/code-review/SKILL.md`) into a
  workspace file the prompt names; where the base lacks the file (the
  pull request that first installs the integration), the head's copy is
  used and the run says so in the log. The ref under review can then no
  longer swap the reviewer's instructions. Verified premise: the CLI
  reads a cwd-materialized file headlessly.
- **Pinned CLI.** `npm install -g @github/copilot@<exact version>` — the
  version proven live in this arc — with a comment naming the upgrade
  path (bump deliberately, in a template change). An unpinned install
  silently changes gate behavior on the CLI vendor's schedule.
- **Distinct fail-open description on the CLI path** (e.g. "the gate's
  Copilot CLI review produced no verdict marker"), so a status reader
  can tell which reviewer produced the outcome; poll and bridge keep the
  existing wording.
- **SKILL.md** gate bullet gains the knob: fail-open by default,
  `SHIPD_GATE_FAIL_OPEN=false` leaves marker-less outcomes pending.
- **Version bump** `plugins/s/.claude-plugin/plugin.json` `0.6.134` ->
  `0.6.135`, per the cache-snapshot rule in `AGENTS.md`.
