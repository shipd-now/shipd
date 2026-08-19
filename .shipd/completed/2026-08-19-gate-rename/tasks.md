## 1. Move the skill surfaces

- [x] 1.1 [req: gate-skill-flow, gate-skill-registration] `git mv
      plugins/s/skills/copilot plugins/s/skills/gate`, then update
      `plugins/s/skills/gate/SKILL.md`: frontmatter `name: gate`, description
      trigger phrases per the plan ("set up the gate", "install the review
      gate", "block PRs on review", "/s:gate"), title heading and every
      self-reference `/s:copilot` → `/s:gate`, including the push-fallback
      branch name `shipd-copilot-install` → `shipd-gate-install`. Leave every `shipd copilot
      add`, Copilot CLI/code review, and `COPILOT_GITHUB_TOKEN` mention
      unchanged (backend naming, per the plan).
- [x] 1.2 [req: gate-skill-registration] `git mv
      plugins/s/harness/bodies/copilot.md plugins/s/harness/bodies/gate.md`,
      update its title and self-references the same way (description marker
      text may stay if it does not name the skill handle; update it where it
      does). Verify with
      `python3 -c "import sys; sys.path.insert(0,'plugins/s/skills/build/scripts'); import harness_bodies as hb; hb.render('gate', frozenset()); hb.render('gate', frozenset(hb.harness_registry.FEATURES)); print('render ok')"`
      and run the engine suite (`python3 -m unittest discover -s
      plugins/s/skills/build/tests -q`) — the bodies/skills id-set equality
      test must pass with `gate` in both sets.

## 2. Registration listings and docs

- [x] 2.1 [req: gate-skill-registration] Update the `README.md` skills-table
      row and `AGENTS.md`'s skill enumeration sentence from `/s:copilot` to
      `/s:gate` (keep each line's description, adjusting only the handle).
- [x] 2.2 [req: *] In `docs/copilot-review.md`, update the guided-path
      mentions from `/s:copilot` to `/s:gate` (the document's filename and
      its Copilot-integration content stay).

## 3. Sweep and version

- [x] 3.1 [req: *] Repo-wide grep for the strings "/s:copilot",
      "plugins/s/skills/copilot", "bodies/copilot.md", and
      "shipd-copilot-install": assert the only remaining occurrences are
      under the immutable archives in the completed tree and this change's
      own planned delta; fix any other stragglers.
- [x] 3.2 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` to the next
      patch version above the version current at ship time (0.6.145 if main
      is still at 0.6.144).

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 61 | 17.2k |
| (no tool) | 0 | 4.3k |
| Edit | 7 | 2.7k |
| Read | 15 | 1.8k |
| Agent | 2 | 562 |
| **Total** | 85 | 26.5k |
