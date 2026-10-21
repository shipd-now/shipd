## MODIFIED Requirements

### Requirement: Intro episode
id: video-intro
base: 75c7b87cc1ef

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

#### Scenario: The early skills had no single home
- **WHEN** a reader opens `docs/history.md` or the intro's 0:40–1:20 narration
- **THEN** it says some early skills, such as the planning skill, lived in a private repository and others only in local Claude settings, and neither file says the early tools had no repository
