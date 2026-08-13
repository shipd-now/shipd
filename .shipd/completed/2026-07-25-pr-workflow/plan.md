# pr-workflow
Status: verified

## Idea

Every build so far has committed straight to `main` from the shared checkout —
which already produced its first collision: uncommitted work from a parallel
session sitting in the tree while another session commits and pushes around
it. There is no CI gate, no review surface, and no isolation between
concurrent sessions. The user has adopted the Platform One workflow rules as
the model to follow.

This change adopts that workflow, scaled to this repo:

- **One change = one worktree = one branch = one PR.** `scripts/worktree.sh
  <change>` creates `.worktrees/<change>` on branch `change/<change>`; the
  whole am lifecycle (plan → build → merge/archive) runs there, so artifacts,
  implementation, and spec promotion travel in the same PR. The main checkout
  is for launching sessions, reviewing, and pulling.
- **Ship via PR, never direct push.** `git push -u origin change/<name>` →
  `gh pr create --fill` → `gh pr merge --auto --squash --delete-branch`.
  Reports always give the full clickable PR URL, never just a number.
- **A `ci` check gates the merge**: new GitHub Actions workflow running the
  engine test suite, the master-library lint, a lint of every in-flight
  change under `am/planned/`, and shell syntax checks. Branch protection on
  `main` requires it and blocks direct pushes — including the orchestrator's.
- **Conventions live in AGENTS.md, not assistant memory** — adopted verbatim
  as a rule; AGENTS.md and the constitution gain the workflow section.

### Non-goals

- No review-pause gate by default: this repo has no UI surface, and its
  changes are covered by the test suite, so every change auto-merges on
  green — the Platform One "backend ships straight through" rule. The owner
  can still gate any change on request.
- No dev-port / database / simulator machinery — nothing here needs it.
- No change to the spec engine, grammar, or lint (workflow only).
- No retroactive rewriting of already-pushed history or archived changes.

Affected capabilities: `build-spec-lifecycle` (modified — two ADDED
requirements: worktree isolation, PR shipping). Impact: new
`scripts/worktree.sh`, new `.github/workflows/ci.yml`, `AGENTS.md`,
`am/constitution.md`, `plugins/s/skills/build/SKILL.md` (Phases 0/6/7),
`plugins/s/skills/plan/SKILL.md` (hand-off note), plugin bump to 0.1.5.

## Implementation

- **The lifecycle runs in the worktree; the merge engine too.** `spec_merge`
  archives within the branch, so the PR carries plan, deltas, tasks, the
  applied master-library edits, and the archived change together — the
  Platform One "artifacts travel in the same PR" property. Rejected: merging
  specs post-PR from main — splits the audit trail across commits.
- **CI is stdlib-only and DB-free**: `actions/setup-python`, `python3 -m
  unittest discover -s plugins/s/skills/build/tests`, `spec_lint.py`
  (master), `spec_lint.py <change>` for each dir under `am/planned/`, and
  `bash -n` on the shell scripts. The job name is `ci` to match the required
  status context. Rejected: pytest (not installed; the suite already runs
  under unittest).
- **Branch protection via `gh api`** (admin confirmed): require the `ci`
  status check and PRs before merging on `main`, enforce for admins. Set
  once by the orchestrator in this build, documented in AGENTS.md rather
  than automated — protection is repo state, not repo content.
- **Snapshot refresh moves post-merge.** The marketplace's directory source
  points at the main checkout, so `claude plugin update` must run *after*
  the PR merges and main is pulled — the build flow's final step, no longer
  a pre-merge task. The version bump itself still rides the PR.
- **`worktree.sh` is minimal by design**: `git worktree add
  .worktrees/<name> -b change/<name>` plus guardrails (repo-root check,
  collision check) and a printed next-steps hint. No port allocation, no
  env seeding — those solve problems this repo doesn't have. Bash 3.2-safe,
  matching the constitution's shell rule.
- **Sub-agents inherit the worktree cwd** — the build skill's Phase 3 prompt
  substitution now names the worktree root as the working directory, so
  claim/complete and all edits stay inside the branch.
- Risk: `gh pr merge --auto` requires the repo to allow auto-merge; if the
  API rejects it, the orchestrator merges manually once `ci` is green and
  notes it in the report.
