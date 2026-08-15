## 1. Port the remaining tracked docs

- [x] 1.1 [req: brand-agents-doc] In `/Users/mikkelbergmann/projects/shipd`, run
      `python3 tools/port.py apply --source
      /Users/mikkelbergmann/projects/shipd --ref <sha> --dest . --include docs/
      --include AGENTS.md --include CLAUDE.md --include README.md --include
      .gitignore` using the same shipd sha the earlier ports used, and confirm
      it exits `0`.

## 2. README

- [x] 2.1 [req: brand-readme] Replace the banner at the top of
      `/Users/mikkelbergmann/projects/shipd/README.md` with new ASCII art
      spelling `shipd` — the ported art still spells the old name because it is
      drawn from slashes and underscores, not letters the token map can rewrite.
- [x] 2.2 [req: brand-readme] In `/Users/mikkelbergmann/projects/shipd/README.md`,
      state the `shipd.now` domain in the opening description, and confirm every
      skill invocation in the skill table is written as `/s:<name>`.
- [x] 2.3 [req: brand-readme] Grep
      `/Users/mikkelbergmann/projects/shipd/README.md` for `shipd` and for
      `/s:` and confirm neither appears.

## 3. Agent instructions

- [x] 3.1 [req: brand-agents-doc] Rewrite
      `/Users/mikkelbergmann/projects/shipd/AGENTS.md` from its ported version so
      it describes shipd's own setup: the `shipd` marketplace, the `s@shipd`
      plugin and its cache-snapshot refresh command, the `.shipd` content
      directory, and the `/s:` skills. Keep the existing structure and rules
      (worktree-per-change, PR-only, the review gate, snapshot refresh after
      merge); remove narration that only made sense as shipd's history.
- [x] 3.2 [req: brand-agents-doc] Confirm
      `/Users/mikkelbergmann/projects/shipd/CLAUDE.md` includes `AGENTS.md` and
      carries no separate stale content.
- [x] 3.3 [req: brand-agents-doc] Check every repository path named in
      `/Users/mikkelbergmann/projects/shipd/AGENTS.md` against the shipd tree and
      confirm each one exists; correct any that does not.

## 4. Hygiene and tool-rewritten strings

- [x] 4.1 [req: brand-repo-hygiene] Replace
      `/Users/mikkelbergmann/projects/shipd/.gitignore` with the ported
      equivalent of shipd's — covering `.DS_Store`, `node_modules/`,
      `__pycache__/`, `.venv/`, `.worktrees/`, and the content directory's
      runtime state and autopilot output under their `.shipd` paths —
      discarding the clone's stock Node template entries. shipd excludes
      `.worktrees/` through its untracked `.git/info/exclude`, which does not
      travel with the port, so shipd names it in the tracked ignore file.
- [x] 4.2 [req: brand-ui-strings] In
      `/Users/mikkelbergmann/projects/shipd/plugins/s/skills/build/scripts/dashboard.py`,
      confirm the header brand block string renders `shipd` beside the muted
      `delivery board` label. Do not otherwise edit the file.
- [x] 4.3 [req: brand-ui-strings] In
      `/Users/mikkelbergmann/projects/shipd/plugins/s/integrations/statusline.sh`,
      confirm the opening comment names shipd rather than shipd. Do not
      otherwise edit the file.

## 5. Verification

- [x] 5.1 [req: *] In `/Users/mikkelbergmann/projects/shipd`, re-run the four
      ported unittest suites and the master-library lint, and confirm all still
      pass.
- [x] 5.2 [req: *] Commit the brand changes in
      `/Users/mikkelbergmann/projects/shipd` on a branch and push it. Opening
      the PR is deferred: `gh` on this machine authenticates as
      `mikkel-bergmann` and 404s on `shipd-now/shipd`, while the push succeeds
      only through the `github-shipd` SSH alias. Per the epic's Design and the
      unanswered queue entry `q-shipd-pr-authoring`, shipd's real PR and
      branch-protection loop belong to the `shipd-selfhost` member; a human
      opens this one from the pushed branch.
