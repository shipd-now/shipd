<!-- doc-type: how-to -->

# Episode 0: Where shipd came from

## Introduction

You are about to learn shipd, but you may not know why it exists. In this episode, the author tells where it came from, speaking to camera. The story runs from one fast project in July 2025, through the spec-driven tools that followed, to shipd. It is for anyone who starts the series and wants the story before the install.

## At a glance

| Item | Detail |
|---|---|
| Roadmap group | Introduction, ahead of the three groups |
| Runtime | 3 minutes |
| Prerequisites | None |
| Commands shown | None; the author speaks to camera |

## Script

### 0:00–0:45 A project that needed speed

**On screen:** The author, on camera.

**Narration:** In July 2025, I worked on a project where we needed to deliver a lot of code, quickly. So I dug up an old idea, and I really tested it. The idea was simple. Get the AI to write up a user story, complete with tickets, instead of writing code straight away.

### 0:45–1:30 Why tickets worked

**On screen:** The author, on camera.

**Narration:** This made the development loop durable. If the agent ran out of context, it could resume from the tickets. Tickets also split the work into several pieces, so the pieces could run in parallel. It worked well for a while.

### 1:30–2:10 Spec-driven development

**On screen:** The author, on camera.

**Narration:** At the end of that project, I was keen to scale this to my team. Around that time, others had similar ideas, and spec-driven development became popular. I paused my ticket system for a while. We started experimenting with these spec-driven systems, with some success.

### 2:10–3:00 Why shipd

**On screen:** The author, on camera, then the [shipd.now](https://shipd.now) home page in a browser.

**Narration:** But these systems stop working well beyond individual specs. Epics, and other larger pieces of work, are hard. And spec-driven development doesn't really deal with concerns that cross repositories. So I started working on a new system that handles all of that. I call it shipd, at shipd.now, and it is open source under the MIT license. In the next episode, I install it and show you how it works.

## Takeaways

- The story began in July 2025, with an AI writing tickets before it wrote code.
- Tickets made the loop durable and let the work run in parallel.
- shipd grew from what spec-driven tools left out: epics and work across repositories.

## Next

Episode 1 installs shipd and ships a change: [Install shipd and ship a change](01-install-and-build.md).

## Sources

- [Where shipd came from](../../history.md)
- [What is shipd?](../../what-is-shipd.md)
