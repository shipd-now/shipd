## ADDED Requirements

### Requirement: Intro episode
id: video-intro

The repository SHALL carry `docs/tutorials/videos/00-intro.md`, an Episode 0 script of about three minutes that declares `how-to`, carries the template's six sections in order, and tells where shipd came from in the author's own account. The repository SHALL also carry `docs/history.md`, a `concept` doc holding that account, and every history claim in the intro SHALL cite it.

#### Scenario: The intro follows the template and runs three minutes
- **WHEN** a reader opens `00-intro.md`
- **THEN** its level-2 headings read `Introduction`, `At a glance`, `Script`, `Takeaways`, `Next`, `Sources`, its first beat starts at `0:00` and its last beat ends at `3:00`, and `docs_lint.py` exits 0 on it

#### Scenario: The intro cites the history page
- **WHEN** a reader opens the intro's `## Sources`
- **THEN** it links `docs/history.md`, and `docs_lint.py` exits 0 on `docs/history.md`

#### Scenario: The history names the dated stages
- **WHEN** a reader opens `docs/history.md`
- **THEN** it places the start in late July 2025, names automikk with its first commit on 2026-07-22, and names shipd as open source under the MIT license with its first commit on 2026-08-13

## MODIFIED Requirements

### Requirement: Series overview
id: video-series-overview
base: 8635634a0a53

The repository SHALL carry `docs/tutorials/videos/index.md`, a `concept` doc that links the intro, Episode 0, ahead of the groups, lists the ten episodes in the roadmap's three groups, links each episode file, and states that episodes 1–9 cover open-source shipd while episode 10 covers the commercial management plane.

#### Scenario: Overview links every episode
- **WHEN** a reader opens `index.md`
- **THEN** it links `00-intro.md` and all ten episode files, and `docs_lint.py` exits 0 on it
