# pr-workflow — tasks

## 1. Workflow scaffolding and docs

- [x] 1.1 [P1] Create `scripts/worktree.sh` (executable, bash 3.2-safe): usage
      `scripts/worktree.sh <change-name>`; refuse when not run from the repo
      root (no `.git` dir), when the name is not kebab-case, or when
      `.worktrees/<name>` or branch `change/<name>` already exists; then run
      `git worktree add .worktrees/<name> -b change/<name>` and print a
      next-steps hint (cd path; run the am lifecycle there; ship with
      `git push -u origin change/<name>` + `gh pr create --fill` +
      `gh pr merge --auto --squash --delete-branch`). Verify with `bash -n`
      and a throwaway invocation (create + `git worktree remove`).
- [x] 1.2 [P1] Create `.github/workflows/ci.yml`: single job named `ci` on
      `pull_request` and on `push` to `main`; steps — checkout,
      `actions/setup-python` (3.x), `python3 -m unittest discover -s
      plugins/s/skills/build/tests -v` (from repo root), `python3
      plugins/s/skills/build/scripts/spec_lint.py` (master library), a loop
      linting every directory under `am/planned/` except none exist →
      `for d in am/planned/*/; do python3
      plugins/s/skills/build/scripts/spec_lint.py "$(basename "$d")"; done`
      guarded so an empty/missing `am/planned/` passes, and `bash -n` on
      `plugins/s/integrations/statusline.sh`,
      `plugins/s/skills/build/scripts/claim_task.sh`, and
      `scripts/worktree.sh`.
- [x] 1.3 [P1] Rewrite the `## Spec workflow` section of `AGENTS.md` into a
      `## Workflow` section adopting the model: one change = one worktree =
      one branch = one PR (`scripts/worktree.sh <change>` →
      `.worktrees/<change>` on `change/<change>`); the whole am lifecycle
      (`/s:plan` → `/s:build`, including merge/archive) runs in the
      worktree so artifacts and implementation travel in one PR; ship via
      `git push -u origin` + `gh pr create --fill` + `gh pr merge --auto
      --squash --delete-branch`; the `ci` check gates the merge and branch
      protection blocks direct pushes to `main` — including yours; always
      report PRs with the full clickable URL; after merge, remove the
      worktree, pull main, and refresh the plugin snapshot from the main
      checkout; conventions live in this file (or the specs), never only in
      an assistant's private memory. Keep the existing layout/lifecycle
      pointers (`/s:plan`, `/s:build`, `/s:status`).
- [x] 1.4 [P1] In `am/constitution.md`, extend `## Workflow discipline`:
      never commit or push to `main` directly — every change ships as an
      auto-merging PR from `change/<name>` gated by `ci`; one change = one
      worktree = one branch = one PR; PR references in reports are full
      URLs; durable conventions are checked into `AGENTS.md`/specs, not
      recorded only in assistant memory. Reword the existing snapshot-refresh
      rule to say the refresh runs from the main checkout after the PR
      merges.

## 2. Skill updates

- [x] 2.1 [P2] In `plugins/s/skills/build/SKILL.md`: (a) Phase 0 gains a
      "workflow gate" bullet — confirm you are in a `.worktrees/<change>`
      worktree on branch `change/<change>` (create one with
      `scripts/worktree.sh` if not) before any artifact or code edit; (b)
      Phase 3's sub-agent prompt substitution names the worktree root as the
      working directory; (c) Phase 6 replaces the direct-commit block: after
      `spec_merge.py`, commit on the branch, `git push -u origin
      change/<change-name>`, `gh pr create --fill`, `gh pr merge --auto
      --squash --delete-branch`, capture `PR_URL=$(gh pr view --json url -q
      .url)`; never push `main`; (d) Phase 7's report includes the full PR
      URL as a link, and the post-merge steps (remove worktree, pull main,
      refresh the plugin snapshot from the main checkout when `plugins/s/`
      changed) close the build; (e) the Operating rules add "ship via PR;
      never commit to main directly".
- [x] 2.2 [P2] In `plugins/s/skills/plan/SKILL.md`, add a short "where to
      run" note: planning for a change that will be built runs inside that
      change's worktree (`scripts/worktree.sh <change>` first), so the
      emitted `am/planned/<change>/` artifacts are born on the
      `change/<change>` branch.
- [x] 2.3 [P2] Bump `plugins/s/.claude-plugin/plugin.json` `"version"` to
      `"0.1.5"`. Do NOT run the snapshot refresh — under the new workflow it
      happens from the main checkout after the PR merges (the Orchestrator
      does it).

## 3. Verification

- [x] 3.1 Verify in the worktree: `python3 -m unittest discover -s
      plugins/s/skills/build/tests -q` all green; `python3
      plugins/s/skills/build/scripts/spec_lint.py` (master) and
      `python3 plugins/s/skills/build/scripts/spec_lint.py pr-workflow`
      both exit 0; `bash -n` passes on `scripts/worktree.sh`. For
      `.github/workflows/ci.yml`, read the file and confirm it has the job
      named `ci`, the pull_request + push-to-main triggers, and the four
      steps (tests, master lint, planned-changes lint loop, bash -n) — the
      authoritative YAML/actions validation is CI's own run on this
      change's PR.
