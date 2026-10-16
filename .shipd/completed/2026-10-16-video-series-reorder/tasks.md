# video-series-reorder tasks

Author every file with `/s:document`: read `plugins/s/skills/document/references/standard.md` first, lint each file with `python3 plugins/s/skills/document/scripts/docs_lint.py <file>` until it exits 0, and report the self-review checklist. Follow `template.md` and the beats, renumber rule, and sources in `plan.md`'s `## Implementation`. Every file lives in the directory docs/tutorials/videos; the tasks name each by its basename.

## 1. Renumber the existing episodes

- [x] 1.1 [P1] [req: video-episode-scripts] With `git mv`, rename `09-management-plane.md` to `10-management-plane.md`, then each of `08-` down to `02-` to the next number with the same slug, highest first.
- [x] 1.2 [P2] [req: video-episode-scripts] In each renamed file, apply the renumber rule to its `# Episode <N>` heading, its `Prerequisites` row, its `## Next` sentence and link, and any episode number in its body.
- [x] 1.3 [P2] [req: video-scripts-grounded] In `10-management-plane.md`, state that episodes 1 to 9 are open source and episode 10 is commercial, in the introduction, the opening beat, and the takeaways.

## 2. Write the two new episodes

- [x] 2.1 [P2] [req: video-episode-scripts] Write `01-install-and-build.md` on the episode 1 beats in `plan.md`, with the kanban demo and its real card; `## Next` links `02-plan-and-specs.md`.
- [x] 2.2 [P2] [req: video-episode-scripts] Write `02-plan-and-specs.md` on the episode 2 beats in `plan.md`, reusing the plan and artifact narration of `01-core-loop.md` where it still fits; `## Next` links `03-worktrees-and-small-prs.md`.
- [x] 2.3 [P3] [req: video-episode-scripts] Delete `01-core-loop.md` with `git rm`.

## 3. Overview and template

- [x] 3.1 [P3] [req: video-series-overview] Update `index.md`: ten episodes, the groups Tactical execution 1–3, Spec authoring and pressure testing 4–5, Verification and governance 6–10, one linked line per episode, and the boundary of episodes 1–9 open source and episode 10 commercial.
- [x] 3.2 [P3] [req: video-episode-scripts] In `template.md` step 7, name episode 10 as the episode whose `## Next` links `index.md`.

## 4. Verify

- [x] 4.1 [P4] [req: video-episode-scripts] Run the docs lint over every `.md` file in docs/tutorials/videos and confirm exit 0.
- [x] 4.2 [P4] [req: video-series-overview] Grep docs/tutorials/videos and the rest of `docs/` for `01-core-loop`, each old `0N-<slug>.md` file name, and `Episode 9` outside `09-ci-and-copilot-review.md`; confirm no stale reference remains.
