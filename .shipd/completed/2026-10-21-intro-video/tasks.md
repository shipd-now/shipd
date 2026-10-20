# intro-video tasks

Author every file with `/s:document`: read `plugins/s/skills/document/references/standard.md` first, lint each file with `python3 -B plugins/s/skills/document/scripts/docs_lint.py <file>` until it exits 0, and report the self-review checklist. The story, the beats, and the header values are fixed in `plan.md`'s `## Implementation`; carry no history beyond its seven story steps.

## 1. History page

- [x] 1.1 [P1] [req: video-intro] Write `docs/history.md` (concept, 100-line cap) titled "Where shipd came from": the seven story steps in the first person, with the dated facts, then a "Where to go next" list linking `what-is-shipd.md` and `getting-started.md`.

## 2. Intro script, overview, and template

- [x] 2.1 [P2] [req: video-intro] Write `docs/tutorials/videos/00-intro.md` from `template.md` with the header values and the four beats in `plan.md`; Sources link `../../history.md` and `../../what-is-shipd.md`; `## Next` links `01-install-and-build.md`.
- [x] 2.2 [P2] [req: video-series-overview] In `docs/tutorials/videos/index.md`, add `0. [Where shipd came from](00-intro.md)` under `## The episodes` ahead of the group headings, and make `## Where to start` tell new viewers to start with Episode 0.
- [x] 2.3 [P2] [req: video-intro] In `docs/tutorials/videos/template.md`, change the runtime sentence so the intro, Episode 0, runs three minutes and every other episode runs five.

## 3. Verify

- [x] 3.1 [P3] [req: video-intro] Run the docs lint over `docs/history.md` and every `.md` file in docs/tutorials/videos and confirm exit 0; confirm `00-intro.md`'s last beat ends at `3:00`.
