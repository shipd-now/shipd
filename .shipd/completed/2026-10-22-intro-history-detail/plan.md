# intro-history-detail
Status: verified
Planned-at: 9344244b20724db01de8dbf06af634c27b8b2963
Gated-hash: cbcb2957fc35

## Idea

Correct the early part of the shipd origin story in the history page and the intro script: before automikk had a repository, the skills were split between a private repository and the author's local Claude settings.

### Motivation

The history page and Episode 0 say the early tools had "no name and no repository". The author has clarified that some skills, such as the planning skill, lived in a private repository, others lived only in local Claude settings, and the name "automikk" came before its repository. The current text is wrong on that point, and it leaves the gap between July 2025 and automikk's first commit unexplained.

### Details

- `docs/history.md`: rewrite the "Skills with no name" section and the "automikk" section.
- `docs/tutorials/videos/00-intro.md`: rewrite the matching narration in the 0:40–1:20 and 1:20–2:15 beats.

Affected capabilities: `video-tutorials` (modified). Impact: two docs files; no code.

### Non-goals

- No change to the beat timings, the other episodes, the index, or the template.
- No history beyond the author's account below.

## Implementation

- **The corrected account (the author's own words, the only new claims allowed):**
  1. At first the tools had no name and no single home.
  2. Some skills, such as the planning skill, lived in a private repository. Others lived only in the author's local Claude settings.
  3. The set was not coherent: the author used each tool as they saw fit during development, and never published any of it.
  4. The author started to think of the set as "automikk" before it had a repository. Eventually the author put most of it into one repository, whose first commit is dated 2026-07-22.
- **`docs/history.md`, section `## Skills with no name`:** replace its paragraph with steps 1 to 3 in the first person. Keep the heading.
- **`docs/history.md`, section `## automikk`:** the first paragraph says the author started thinking of the set as "automikk", a way to replace their own work with automation, and that they eventually put most of it into one repository, whose first commit is 2026-07-22 (step 4). Keep the daily-use paragraph as it is.
- **`00-intro.md`, 0:40–1:20 narration:** keep the two template sentences. Replace "At that stage the tools had no name and no repository. I copied the skills between projects by hand, and I never published them." with steps 1 to 3, in at most three short spoken sentences.
- **`00-intro.md`, 1:20–2:15 narration:** replace "The set of tools grew into "automikk", a way for me to replace my own work with automation. The automikk repository dates its first commit 2026-07-22." with step 4, keeping the date. Keep the other sentences and the title cards.
- Narration stays first person with no links. Lint each edited file with `docs_lint.py` until it exits 0.

## Readiness attestation

### Problem and motivation

The early-history wording contradicts the author's clarified account.

Evidence:

- `docs/history.md:17` reads "At that stage the tools had no name and no repository."
- `docs/tutorials/videos/00-intro.md:30` carries the same sentence in narration.

### Scope and non-goals

Two docs files, one requirement.

Evidence:

- Requirement `video-intro` in capability `video-tutorials` governs both files.

### Affected capabilities and files

`video-tutorials`/`video-intro` (modified); `docs/history.md`, `docs/tutorials/videos/00-intro.md`.

Evidence:

- `spec_status.py base-hash video-tutorials video-intro` printed `75c7b87cc1ef`.

### No open task-shaping decision

The author settled the wording in this session.

Evidence:

- The author: some skills lived in a private repository (for example, the planning skill), some lived only locally, the name came first, and a repository for most of it came later.
