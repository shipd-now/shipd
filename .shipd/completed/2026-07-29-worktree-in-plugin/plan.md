# worktree-in-plugin
Status: verified

## Idea

The worktree helper — the entry point of the one-change-one-worktree
workflow — lives at `scripts/worktree.sh` in this repository only. Every
skill doc points at "the repo script", so any other repo using the am
plugin lacks the ceremony the skills instruct, and the upcoming autopilot
driver would have had to reimplement or push the script into target repos.
The plugin is installed at user scope and already ships bash engine
scripts (`claim_task.sh`), so there is no reason the helper is not one of
them.

This change moves it:

- `plugins/s/skills/build/scripts/worktree.sh` becomes the helper —
  behavior-identical (worktree at `.worktrees/<change>`, branch
  `change/<change>`, existing-branch refusal) with repo-neutral hint text,
  runnable in any git repository.
- The four skill docs (`plan`, `build`, `epic`, `initiative`), AGENTS.md,
  and ci.yml's `bash -n` check repoint to the plugin path.
- `scripts/worktree.sh` is deleted from this repository.

### Non-goals

- No behavior changes to worktree/branch naming or the refusal rule.
- No PR-shipping logic in the helper — it creates the worktree; shipping
  stays with the skills (and later the autopilot driver).
- No migration of existing worktrees — they are plain git state the script
  never touches after creation.

Affected capabilities: `build-spec-lifecycle` (modified). Impact:
`plugins/s/skills/build/scripts/worktree.sh` (new),
`plugins/s/skills/build/tests/test_worktree.py` (new),
`scripts/worktree.sh` (deleted), `plugins/s/skills/{plan,build,epic,
initiative}/SKILL.md`, `AGENTS.md`, `.github/workflows/ci.yml`, plugin
version bump.

## Implementation

- **Port, don't rewrite.** The existing 54 logic lines move verbatim where
  possible; only the printed next-steps text generalizes (drop
  repo-specific phrasing, keep the cd/lifecycle/PR hint). Rejected: a
  Python port — bash matches the original and the `claim_task.sh`
  precedent, and `bash -n` stays the ci syntax gate.
- **Any-git-repo contract.** The helper requires being run from a repo
  root (a `.git` directory) exactly as today; it makes no assumption about
  am layout, content dir, or this repository — a fresh repo with `git`
  and nothing else can use it.
- **Invocation convention.** Skill docs reference it by the plugin-root
  path exactly as they already reference `spec_status.py` and friends —
  one convention for every engine script.
- **Tests via subprocess** in `test_worktree.py`, mirroring
  `test_claim_task.py`: temp git repo fixtures (git init + one commit),
  assertions on worktree dir, branch name, refusal exit code, and the
  outside-a-repo error.
- **ci.yml** swaps the `bash -n scripts/worktree.sh` line for the plugin
  path — the deleted file must not linger in ci.

Risk: sessions mid-flight in other checkouts still calling the old path
after this merges; guarded by AGENTS.md documenting the new path in the
same PR, and the old path failing loudly (file gone) rather than
diverging silently.
