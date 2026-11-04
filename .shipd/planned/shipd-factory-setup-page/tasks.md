# shipd-factory-setup-page tasks

Author both pages through `/s:document`. The facts, names, placeholders and section order are binding in `plan.md` ## Implementation. No file this change writes may spell the codename; match it only as `a[x]el` (regex) or `a?el` (glob).

## 1. Concept page

- [ ] 1.1 [req: shipd-factory-page] In `docs/shipd-factory.md`, insert line 3 `> **Beta, invite only:** [Run your own factory host](shipd-factory-setup.md).` followed by a blank line.
- [ ] 1.2 [req: shipd-factory-page] In `docs/shipd-factory.md`, rewrite the "What it is for" host sentence to the plan's wording and relabel the diagram's `LHost` subgraph `factory host`.
- [ ] 1.3 [req: shipd-factory-page] In `docs/shipd-factory.md`, change the key path to `~/.config/shipd-factory/`, drop the password-manager source, and change the ruleset check to the room check named in `plan.md` (the shipd-factory-reviewer room-review check).
- [ ] 1.4 [req: shipd-factory-page] Trim prose in `docs/shipd-factory.md` until `wc -l` prints at most 100, keeping every fact the master scenarios name.
- [ ] 1.5 [req: shipd-factory-page] Run `python3 -B plugins/s/skills/document/scripts/docs_lint.py docs/shipd-factory.md` until it exits 0.

## 2. Setup page

- [ ] 2.1 [req: shipd-factory-setup-page] Create `docs/shipd-factory-setup.md` with `<!-- doc-type: how-to -->`, the title `# Run your own shipd-factory host`, and the Beta, invite only line from `plan.md`.
- [ ] 2.2 [req: shipd-factory-setup-page] Add the seven numbered sections to `docs/shipd-factory-setup.md` in the plan's order, with the plan's commands, names and placeholders.
- [ ] 2.3 [req: shipd-factory-setup-page] Run `python3 -B plugins/s/skills/document/scripts/docs_lint.py docs/shipd-factory-setup.md` until it exits 0, and confirm `wc -l` prints at most 170.
- [ ] 2.4 [req: shipd-factory-setup-page] Run `grep -n -i -E 'a[x]el|[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+|mikkel-bergmann|1password|vault' docs/shipd-factory-setup.md` and confirm it prints nothing.

## 3. Archived records and comments

- [ ] 3.1 [req: shipd-factory-setup-page] Run `git mv .shipd/completed/2026-11-03-shipd-a?el-docs .shipd/completed/2026-11-03-factory-app-docs`, then set its `plan.md` title line to `# factory-app-docs`.
- [ ] 3.2 [req: shipd-factory-setup-page] Run `git mv .shipd/completed/2026-11-03-factory-app-docs/specs/shipd-a?el-docs .shipd/completed/2026-11-03-factory-app-docs/specs/factory-app-docs`.
- [ ] 3.3 [req: shipd-factory-setup-page] Run `git mv .shipd/completed/2026-11-03-shipd-factory-docs/specs/shipd-a?el-docs .shipd/completed/2026-11-03-shipd-factory-docs/specs/factory-app-docs`.
- [ ] 3.4 [req: shipd-factory-setup-page] Run `git grep -n -i -E 'a[x]el|100\.121\.|mikkel-bergmann/(shipd-factory|css-animation)'`. Reword every printed line in `.shipd/completed/`, `.shipd/research/shipd-addons/report.md` and `tools/container/Dockerfile` with the plan's archive mapping. Re-run until only `.shipd/verified/shipd-factory-docs/spec.md` remains, which the merge rewrites.
- [ ] 3.5 [req: *] Run `python3 plugins/s/skills/build/scripts/spec_lint.py` and `python3 -m unittest discover -s plugins/s/skills/build/tests`, and confirm both exit 0.

## 4. Merge and guard

- [ ] 4.1 [req: *] Merge and archive the change with the engine's `spec_merge.py`, as `/s:build` does.
- [ ] 4.2 [req: *] Run the guard: `git grep -n -i -E 'a[x]el|100\.121\.|mikkel-bergmann/(shipd-factory|css-animation)'` and `git ls-files | grep -i 'a[x]el'`. Confirm both print nothing. The plan lists no exceptions.

## 5. Push, after the factory rename is live

- [ ] 5.1 [req: *] USER PAUSE. Print `Waiting for the signal: factory rename deployed` and stop until the user sends exactly that signal. Do not push before it.
- [ ] 5.2 [req: shipd-factory-setup-page] On the renamed factory repo's main, confirm each command, path, unit name, env name and output line on `docs/shipd-factory-setup.md`. Fix any that differ, then re-run tasks 2.3, 2.4 and 4.2.
- [ ] 5.3 [req: *] Re-run the guard from task 4.2, then run `git push -u origin change/shipd-factory-setup-page`, `/s:pr`, and `gh pr merge --auto --squash --delete-branch`. Re-run the guard before every later push.
- [ ] 5.4 [req: *] Run the `/s:review` post flow and disposition loop on the PR as `AGENTS.md` describes, re-posting after any push, then report the PR's full URL.

## 6. Website follow-up (repo shipd-now/shipd-now-website)

- [ ] 6.1 [req: shipd-factory-setup-page] USER PAUSE. After the shipd PR merges, print `gh workflow run docs-sync.yml -R shipd-now/shipd-now-website` and wait for the user to run it, or for the hourly sync, and to confirm the sync PR merged.
- [ ] 6.2 [req: shipd-factory-setup-page] In the website checkout, run `git fetch origin && git switch -c docs/shipd-factory-setup-visible origin/main`. Confirm the docs manifest (content/docs.manifest.json) holds a hidden entry for file shipd-factory-setup.md.
- [ ] 6.3 [req: shipd-factory-setup-page] In that entry, delete `"hidden": true`, add `"section": "Concepts"` (the shipd-factory section; no Guides section exists), and add the description "How an invited operator sets up an ax host for the shipd factory and points the skill at it." Keep the derived `file`, `slug` and `title`.
- [ ] 6.4 [req: shipd-factory-setup-page] Run `npm run test` and `npm run build` in the website checkout, confirm both exit 0, commit the manifest with a message ending `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`, and push the branch.
- [ ] 6.5 [req: shipd-factory-setup-page] USER PAUSE. Print `gh pr create -R shipd-now/shipd-now-website --head docs/shipd-factory-setup-visible --title "Show the shipd-factory setup page under Concepts"` and `gh pr merge --auto --squash --delete-branch -R shipd-now/shipd-now-website`, and wait for the user to run them and confirm the merge.
- [ ] 6.6 [req: shipd-factory-setup-page] After that merge, run `git grep -n -i 'a[x]el'` in the website checkout on origin/main and report its output to the user without editing.
