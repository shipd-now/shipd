<!-- doc-type: how-to -->

# Episode 0: Where shipd came from

## Introduction

You are about to learn shipd, but you may not know why it exists. This episode is the author's own account of where it came from. It follows one idea from a fast-moving project in July 2025, through the spec-driven tools that followed, to an open-source release. It is for anyone who starts the series and wants the story before the install.

## At a glance

| Item | Detail |
|---|---|
| Roadmap group | Introduction, ahead of the three groups |
| Runtime | 3 minutes |
| Prerequisites | None |
| Commands shown | None; the author speaks to camera |

## Script

### 0:00–0:40 Tickets before code

**On screen:** The author on camera. A title card reads "July 2025: tickets before code".

**Narration:** In July 2025, I worked on a project that needed a lot of code, fast. I dug up an old idea and tested it hard. The idea was simple. Before the AI writes any code, it writes a user story, complete with tickets.

### 0:40–1:15 Why tickets worked

**On screen:** The author on camera. Two title cards appear in turn: "Resume after context runs out", then "Split the work, run it in parallel".

**Narration:** Tickets made the development loop durable. When an agent ran out of context, a new session picked up from the tickets. Tickets also split the work into pieces, so several agents could work in parallel. It worked well for the rest of that project.

### 1:15–1:55 Spec-driven development arrives

**On screen:** The author on camera. A title card reads "Spec-driven development".

**Narration:** At the end of that project, I wanted to scale this to my team. Around that time, other people had similar ideas, and spec-driven development became popular. I paused my ticket system, and we experimented with the new spec-driven tools. They worked, with some success.

### 1:55–2:25 Where the tools stopped

**On screen:** The author on camera. Three title cards appear in turn: "One spec at a time", "Epics and larger work", "Several repositories".

**Narration:** Those tools worked well for one spec at a time, and less well beyond it. An epic, or any larger piece of work, was hard. And they had no answer for work that spans several repositories. So I started a new system to handle all of that.

### 2:25–3:00 shipd

**On screen:** The author on camera. Title cards read "automikk, first commit 2026-07-22", then "shipd, first commit 2026-08-13". The [shipd.now](https://shipd.now) home page appears, then the repository's MIT `LICENSE`.

**Narration:** I first called it automikk, and its repository dates its first commit 2026-07-22. I published it as shipd, at shipd.now, with a first commit on 2026-08-13. shipd is open source under the MIT license, so anyone can use it. In Episode 1, you install it.

## Takeaways

- The story began in July 2025, with an agent writing tickets before it wrote code.
- Tickets made the loop durable and let the work run in parallel.
- Spec-driven tools handled one spec well, but not epics or several repositories.
- shipd grew out of that gap, and it is open source under the MIT license.

## Next

Episode 1 installs shipd and ships a change: [Install shipd and ship a change](01-install-and-build.md).

## Sources

- [Where shipd came from](../../history.md)
- [What is shipd?](../../what-is-shipd.md)
