# gate-update-flow
Status: verified
Theme: developer-experience

## Idea

Give `/s:gate` an `update` argument that refreshes a consumer repository's
installed gate files to the running plugin version and ships the refresh —
so a redesigned gate reaches the repositories that already installed it
without a manual re-setup.

### Motivation

The gate's four managed files are vendored into each consumer repository, so
a plugin release changes nothing there until someone re-runs the install:
cai-api's PR #26 reviewed on `shipd-copilot v0.6.147` files two versions
after the plugin shipped v0.6.149's redesigned review output. The engine
already detects the drift — the bare `shipd copilot` report classifies each
managed file (`installed`/`stale`/`foreign`/`absent`) against the running
plugin version, and `shipd copilot add` refreshes idempotently — but no
skill flow drives the refresh: bare `/s:gate` is a full setup with a
repository-settings consent round and a reviewer-token hand-off that an
already-gated repository does not need again.

### Details

- `/s:gate update` runs a refresh-only flow in the current repository: the
  same three preflight checks as setup, a read of the per-file states, a
  refresh with `shipd copilot add` when anything is stale or absent, a
  commit and push of the four managed paths, and a closing relay of the
  post-refresh states.
- An already-current repository (all four files `installed` at the running
  version) writes, commits, and pushes nothing.
- A rejected push falls back to a `shipd-gate-update` branch shipped as a
  pull request with auto-merge attempted, mirroring setup's protected-branch
  fallback.
- The settings consent round, the token hand-off, and the doctor
  verification stay setup-only; the update flow touches no GitHub setting.

Affected capabilities: `shipd-gate` (modified). Impact:
`plugins/s/skills/gate/SKILL.md`, `plugins/s/harness/bodies/gate.md`,
`README.md`, `AGENTS.md`, `plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No engine change: `shipd copilot` keeps exactly its bare/`add`/`remove`
  verbs; no `update` verb is added to the binary, whose `add` already
  refreshes.
- No change to the bare `/s:gate` setup flow, its consent round, or its
  token hand-off.
- No GitHub-settings mutation on the update path: no branch-protection
  write, no auto-merge PATCH, no Actions variable, no secret.
- No cross-repo targeting: update operates on the current working
  repository, like every other gate step.

## Implementation

**Skill-level dispatch, engine untouched.** The engine already carries the
whole mechanism: `copilot_states` classifies each managed file against the
running plugin version and `_copilot_add` refreshes idempotently
(`plugins/s/bin/shipd:1104-1197`), with the bare report rendering one
`<state> <path> — <detail>` line per file. The update flow only sequences
existing verbs, honoring the gate skill's "invent no mechanism" rule; the
`update` argument branches near the top of
`plugins/s/skills/gate/SKILL.md`, and the bare invocation keeps today's
setup flow unchanged.

**The invocation is the consent.** Bare `/s:gate` proposes its commit
because setup also mutates repository settings and hands off credentials.
`/s:gate update` names its entire scope in the invocation — refresh the four
managed files — so the flow commits and pushes without a further
confirmation round. Foreign files keep the setup rule: refuse, name the
file, and never pass `--force` on the skill's own judgment.

**Fallback mirrors setup, plus auto-merge.** On a rejected push the flow
branches to `shipd-gate-update` and opens a pull request. Unlike setup —
which cannot assume the auto-merge setting exists before its own consent
round has offered it — update targets a repository that already completed
setup, so it attempts `gh pr merge --auto --squash --delete-branch`; where
GitHub rejects arming, the flow reports the full PR URL as awaiting a human
merge. Rejected: stopping at the open PR as setup does — an update invoked
to "do it for us" should finish unattended where the repository allows it.

**Already-current is a first-class exit.** When the bare report shows all
four files `installed` at the running version, the flow reports that and
stops: no write, no commit, no push. The state is read from the verb's own
report lines — the skill never re-derives versions from file contents.

**Body-template parity.** `plugins/s/harness/bodies/gate.md` carries the
same update section so non-Claude harnesses render the same flow. It gains
no `if:` gates, so no fallback reference file is needed, and no skill
directory is added, so the harness-command-bodies id-set equality is
unaffected.
