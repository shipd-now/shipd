<!-- doc-type: how-to -->

# Episode 0: Where shipd came from

## Introduction

You are about to learn shipd, but you may not know why it exists. This episode is the author's own account of where it came from. It follows the tools from a first request to an agent, through a private set of skills, to an open-source release. It is for anyone who starts the series and wants the story before the install.

## At a glance

| Item | Detail |
|---|---|
| Roadmap group | Introduction, ahead of the three groups |
| Runtime | 3 minutes |
| Prerequisites | None |
| Commands shown | None; the author speaks to camera |

## Script

### 0:00–0:40 The ticket phase

**On screen:** The author on camera. A title card reads "Late July 2025: tickets".

**Narration:** In late July 2025, I began asking an AI coding agent for tickets. Each ticket planned one piece of work. It worked surprisingly well.

### 0:40–1:20 A template and copied skills

**On screen:** The author on camera. A title card reads "The ticket template".

**Narration:** Next I wrote a template for the structure of each ticket. Only later did I learn that the practice has a name: spec-driven development. At first the tools had no name and no single home. Some skills, such as the planning skill, lived in a private repository, and others lived only in my local Claude settings. The set was not coherent, I used each tool as I saw fit, and I never published any of it.

### 1:20–2:15 Review, pull requests, and automikk

**On screen:** The author on camera. Title cards read "A review and pull-request feature", then "automikk, first commit 2026-07-22".

**Narration:** Then came a review feature and a pull-request feature. I started to think of the set as "automikk", a way for me to replace my own work with automation, before it had a repository. Eventually I put most of it into one repository, and its first commit dates 2026-07-22. I used the tools every day, kept improving them, and kept adding skills.

### 2:15–3:00 Publishing shipd

**On screen:** The author on camera. A title card reads "shipd, first commit 2026-08-13". The [shipd.now](https://shipd.now) home page appears, then the repository's MIT `LICENSE`.

**Narration:** I published the tools as shipd, at shipd.now. The shipd repository dates its first commit 2026-08-13. shipd is open source under the MIT license, so anyone can use it. Today shipd is a spec-driven delivery system for AI coding agents, as [What is shipd?](../../what-is-shipd.md) explains. In Episode 1, you install it.

## Takeaways

- The author began with tickets that an AI coding agent wrote, in late July 2025.
- The tools grew into automikk, whose first commit dates from 2026-07-22.
- shipd is open source under the MIT license, with its first commit on 2026-08-13.

## Next

Episode 1 installs shipd and ships a change: [Install shipd and ship a change](01-install-and-build.md).

## Sources

- [Where shipd came from](../../history.md)
- [What is shipd?](../../what-is-shipd.md)
