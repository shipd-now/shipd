# video-series-scripts tasks

Author every file with `/s:document`: read `plugins/s/skills/document/references/standard.md` first, lint each file with `python3 plugins/s/skills/document/scripts/docs_lint.py <file>` until it exits 0, and report the self-review checklist. Follow the episode template and the source map in `plan.md`'s `## Implementation`; read each episode's sources before writing its beats.

Every file below is new and lives in the new directory docs/tutorials/videos (create both `tutorials` and `videos`); the tasks name each file by its basename.

## 1. Template and overview

- [x] 1.1 [P1] [req: video-episode-template] Write `template.md` (how-to): a numbered fill-in step per template section, and the skeleton in one fenced `markdown` block.
- [x] 1.2 [P2] [req: video-series-overview] Write `index.md` (concept): the three roadmap groups (Tactical execution 1–2; Spec authoring and pressure testing 3–4; Verification and governance 5–9), one linked line per episode, and the open-source/commercial boundary.

## 2. Episode scripts

- [x] 2.1 [P2] [req: video-episode-scripts] Write `01-core-loop.md` — The core loop: `/s:plan` then `/s:build`.
- [x] 2.2 [P2] [req: video-episode-scripts] Write `02-worktrees-and-small-prs.md` — Git worktrees and small PRs.
- [x] 2.3 [P2] [req: video-episode-scripts] Write `03-prds-and-guardrails.md` — PRDs and guardrails.
- [x] 2.4 [P2] [req: video-scripts-grounded] Write `04-epics-and-epic-grill.md` — Epics and `/s:epic-grill`, on the four spotlight beats.
- [x] 2.5 [P2] [req: video-scripts-grounded] Write `05-oracle-and-supersession-gate.md` — The oracle and the supersession gate.
- [x] 2.6 [P2] [req: video-scripts-grounded] Write `06-workspaces-101.md` — Workspaces 101.
- [x] 2.7 [P2] [req: video-scripts-grounded] Write `07-advanced-workspaces.md` — Member maps and headless runs.
- [x] 2.8 [P2] [req: video-episode-scripts] Write `08-ci-and-copilot-review.md` — CI and Copilot review.
- [x] 2.9 [P2] [req: video-episode-scripts] Write `09-management-plane.md` — The management plane (commercial).

## 3. Verify

- [x] 3.1 [P3] [req: video-episode-scripts] From the repository root run the docs lint over every `.md` file in docs/tutorials/videos and confirm exit 0.
- [x] 3.2 [P3] [req: video-episode-scripts] For each episode run `grep '^## ' <file>` and confirm the six headings in template order; confirm each `## Next` link resolves to an existing file.

## 4. Review fixes

- [x] 4.1 [P4] [req: video-episode-scripts] Rewrite the four beats of `04-epics-and-epic-grill.md` to carry the "Episode 4 beats" content in `plan.md`, keeping the timestamps, and align its Introduction and Takeaways.
- [x] 4.2 [P4] [req: video-episode-scripts] In `05-oracle-and-supersession-gate.md`, set the `Roadmap group` row to Verification and governance.
- [x] 4.3 [P4] [req: video-series-overview] In `09-management-plane.md`, fill the 4:20–5:00 beat's "Direction" column and narration with the four roadmap items `plan.md` names, stated as direction, not as shipped features.
- [x] 4.4 [P5] [req: video-episode-scripts] Re-run the docs lint over every `.md` file in docs/tutorials/videos and confirm exit 0.
