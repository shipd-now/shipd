# intro-video
Status: verified
Planned-at: aa3b0a8f7d00cbe7be74eabdf743a958aa11afda
Gated-hash: 4f107d9c5667

## Idea

Add a three-minute intro video script, Episode 0, in which the author tells where shipd came from, and a history page the script cites.

### Motivation

A viewer who starts the series at the install episode never learns why shipd exists or how it grew from one person's daily tools. No doc records that history, so a script cannot ground the story in a source.

### Details

- New `docs/tutorials/videos/00-intro.md`: Episode 0, about three minutes, the template's six sections, no commands.
- New `docs/history.md`: a concept page with the origin story in the author's account, plus the dated facts from the repositories.
- `docs/tutorials/videos/index.md`: link the intro ahead of the three groups and point new viewers at it.
- `docs/tutorials/videos/template.md`: name the intro as the one episode that runs three minutes.

Affected capabilities: `video-tutorials` (modified). Impact: four files under `docs/`; no code, no engine, no dependency.

### Non-goals

- No change to episodes 1 to 10.
- No website edit, and no recording of the video.
- No history beyond the story the author gave and the repositories' first commits.

## Implementation

- **The story, in order.** These are the author's own account and the only history claims the two files make:
  1. In late July 2025 the author began asking an AI coding agent for tickets that planned pieces of work, and it worked surprisingly well.
  2. The author then wrote a template for each ticket's structure. Only later did they learn the practice is called spec-driven development.
  3. At that stage the tools had no name and no repository. The author copied the skills between projects by hand and never published them.
  4. Next came a review and pull-request feature.
  5. The set of tools grew into "automikk", a way for the author to replace their own work with automation. The automikk repository's first commit is dated 2026-07-22.
  6. The author used the tools every day, kept improving them, and kept adding skills.
  7. The author published the tools as shipd, at shipd.now. The shipd repository's first commit is dated 2026-08-13, and shipd is open source under the MIT license, so anyone can use it.
- **`docs/history.md`.** A `concept` doc titled "Where shipd came from", within its 100-line cap. It tells the story above in the first person ("I"), because it is the author's account. It closes with a short "Where to go next" list linking `what-is-shipd.md` and `getting-started.md`. Rejected: third-person prose, which reads as a claim nobody owns.
- **`00-intro.md` header.** `# Episode 0: Where shipd came from`. In `At a glance`: Roadmap group `Introduction, ahead of the three groups`; Runtime `3 minutes`; Prerequisites `None`; Commands shown `None; the author speaks to camera`.
- **`00-intro.md` beats.** The narration is in the first person, from the author:
  - 0:00–0:40: the ticket phase (story step 1).
  - 0:40–1:20: the ticket template and spec-driven development (step 2), with the copied-around skills (step 3).
  - 1:20–2:15: review and PRs, then automikk and daily use (steps 4 to 6).
  - 2:15–3:00: publishing shipd as open source (step 7), ending on a pointer to Episode 1.
  - On screen: the author on camera, with a short title card per beat naming the stage and its date. The last beat shows the shipd.now home page and the repository's MIT `LICENSE`.
- **Behavior claims.** Any sentence about what shipd does today cites `docs/what-is-shipd.md` and keeps the glossary meaning of spec and change. Every history sentence cites `docs/history.md`.
- **Sources of `00-intro.md`:** `../../history.md` and `../../what-is-shipd.md`. `## Next` links `01-install-and-build.md`.
- **Index.** Under `## The episodes`, put the intro first as `0. [Where shipd came from](00-intro.md)` ahead of the three group headings. In `## Where to start`, tell new viewers to start with Episode 0. Keep the three groups as they are. In the opening paragraph, replace "ten episodes of five minutes each" with wording that names a three-minute intro and ten five-minute episodes.
- **Template.** Change "Each episode runs five minutes and holds four to six beats" to say that the intro, Episode 0, runs three minutes and every other episode runs five.
- **Authoring.** Write and revise every file with `/s:document` and run `docs_lint.py` on each until it exits 0.

Risk: the narration overstates history the author did not give. Guard: the two files carry only the seven story steps above.

## Readiness attestation

### Problem and motivation

The series opens on installing shipd and no doc records its origin.

Evidence:

- `docs/tutorials/videos/index.md` lists Episode 1, `01-install-and-build.md`, as the first episode.
- `grep -ri automikk docs/` finds nothing; the origin appears only in archived change plans such as `.shipd/completed/2026-08-15-video-cursor-grounding/plan.md:7`.

### Scope and non-goals

Four files under `docs/` and one capability; the other episodes, the website, and the recording stay out.

Evidence:

- Capability `video-tutorials` holds the series rules; `video-episode-scripts` fixes the ten numbered episodes, which stay unchanged.
- Settled with the user: Episode 0 numbering, three minutes, the author's account as source, and a new history page.

### Affected capabilities and files

One capability with one added and one modified requirement, and four files.

Evidence:

- `video-tutorials`: `video-intro` (added), `video-series-overview` (modified).
- Files: `docs/tutorials/videos/00-intro.md` (new), `docs/history.md` (new), `docs/tutorials/videos/index.md`, `docs/tutorials/videos/template.md:10`.
- Runnable premise: `git log --reverse --format='%ad %s' --date=short` in the automikk repository printed `2026-07-22 Scaffold automikk plugin marketplace with am plugin` first; in the shipd repository it printed `2026-08-13 Initial commit` first.
- Runnable premise: `head -1 LICENSE` printed `MIT License`.
- `plugins/s/skills/document/references/standard.md:69` caps a concept doc at 100 lines.

### No open task-shaping decision

Every decision is settled; none remain.

Evidence:

- Start year, numbering, runtime, and sources: the user, in this session's typed round.
- Beats, group label, first-person voice, and index placement: investigation of the template, the index, and the documentation standard.
