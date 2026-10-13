# Tasks

- [x] 1.1 [P1] [req: copilot-review-guide] Verify every premise before applying
      anything, against the real files. For each of the six requirements check
      **both** sides: what its owner says, **and** what the surface the
      requirement governs currently says. The second half is the one that
      matters — an earlier attempt checked only the owner side, strengthened
      two count requirements past their own docs, and shipped them unmet.
      Specifically: `docs/copilot-review-reference.md` describes the backwards
      scan and contains no "last non-empty"; `difft-required-docs` forbids both
      calling `difft` optional and claiming a review degrades;
      `docs/semantic-review.md` says the review stops;
      `plugins/s/skills/review/SKILL.md` step 5b carries six risk-lens
      triggers while `docs/semantic-review.md` carries five; both payload
      surfaces carry eleven `category` values while
      `docs/semantic-review-reference.md` carries ten; `README.md` carries
      Pipeline, Orchestration and Memory; `spec_common.CONFIG_FILENAME` is
      `.shipd-config.json` with no script reading `.shipd/config.json`; and
      `docs/workspaces/teams.md` documents the exclusive lock and the
      session-boundary push.
- [x] 1.2 [P1] [req: copilot-review-guide] Verify every requirement id named as
      an owner exists, sits in the capability the text implies, and actually
      owns what is deferred to it — `gate-workflow-template`,
      `difft-required-docs`, `review-risk-lenses`, `review-taxonomy-parity`,
      `readme-catalogs-the-plugin-s-skills`, `theme-vocabulary-config`,
      `workspaces-doc-store-sync`, `doctor-provisioning` and
      `reference-context`. Earlier drafts named an id that did not exist and
      misdescribed what another owned, so check subject as well as existence.
- [x] 2.1 [P2] [req: copilot-review-guide] Apply the MODIFIED `project-readme`
      delta covering all four of its requirements, prose and scenarios
      together. Confirm the capability then contains no "last non-empty", no
      "optional difftastic", no "all five", no "five triggers", no "all ten"
      and no "the core loop, bigger than one change".
- [x] 2.2 [P2] [req: epic-header-metadata] Apply the MODIFIED
      `shipd-spec-format` delta. Confirm `epic-header-metadata` names no
      configuration path and names `theme-vocabulary-config`.
- [x] 2.3 [P2] [req: workspaces-doc] Apply the MODIFIED `shipd-workspace`
      delta, prose and scenario together. Confirm the requirement carries no
      "no locks" and no "no-locks/no-networked-git", and names
      `workspaces-doc-store-sync`.
- [x] 2.4 [P2] [req: semantic-review-doc] Update `docs/semantic-review.md` so
      its risk-lens bullet names **six** triggers including packaging and
      dependency manifests, and `docs/semantic-review-reference.md` so its
      `category` table cell and its prose list both name **eleven** values
      including `description-drift`. Both are required for the strengthened
      count requirements to be met. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py` over both and
      confirm each stays within its doc-type cap.
- [x] 2.5 [P2] [req: semantic-review-doc] Add the guard whose absence let both
      count requirements ship unmet: assert in
      `plugins/s/skills/review/tests/test_skill_references.py` that
      `docs/semantic-review.md` names every risk-lens trigger and states no
      stale trigger count, and that `docs/semantic-review-reference.md` names
      every `category` value and states no stale count — its table cell and
      its prose list are separate places and both need covering. Prove it
      non-vacuous by reverting both docs to the main branch's content and
      watching every assertion fail, recording the byte counts so a truncating
      probe cannot be mistaken for a result. Correct the two docstrings in that
      file still saying "five triggers" where the code they document checks
      six. Bump `plugins/s/.claude-plugin/plugin.json` from 0.6.278 to 0.6.279.
- [x] 3.1 [P3] [req: copilot-review-guide] Confirm nothing on the `/s:review`
      prompt path changed — not `plugins/s/skills/review/SKILL.md`, nothing
      under `plugins/s/skills/review/references/`, and nothing under
      `plugins/s/harness/` or `plugins/s/integrations/` — so a ReviewBench
      measurement calibrated on v0.6.276's prompt is unaffected. The tests
      directory, `plugin.json` and the two `docs/` files are expected. Any
      other plugin file is a finding, not a check.
- [x] 3.2 [P3] [req: copilot-review-guide] Run the whole-library lint, the
      documentation lint over both edited docs, the review suite and the build
      suite, reading each suite verdict with
      `grep -E "^(OK|FAILED|ERROR)|^Ran [0-9]+ tests"` over a captured log
      rather than tailing it, and never running a suite concurrently with a
      probe that mutates a file.
