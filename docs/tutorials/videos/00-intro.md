<!-- doc-type: how-to -->

# Episode 0: Where shipd came from

## Introduction

You are about to learn shipd, but you may not know why it exists. In this episode, the author tells where it came from, speaking to camera, then names the core features. The story runs from one fast project in July 2025, through the spec-driven tools that followed, to shipd. It is for anyone who starts the series and wants the story and the big picture before the install.

## At a glance

| Item | Detail |
|---|---|
| Roadmap group | Introduction, ahead of the three groups |
| Runtime | 5 minutes |
| Prerequisites | None |
| Commands shown | None run; the author names `/s:build`, `/s:prd`, `/s:plan-deep`, and `/s:autopilot` |

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

### 2:10–2:50 Why shipd

**On screen:** The author, on camera, then the [shipd.now](https://shipd.now) home page in a browser.

**Narration:** But these systems stop working well beyond individual specs. Epics, and other larger pieces of work, are hard. And spec-driven development doesn't really deal with concerns that cross repositories. So I started working on a new system that handles all of that. I call it shipd, at shipd.now, and it is open source under the MIT license.

### 2:50–3:20 Specs and building

**On screen:** The author, on camera.

**Narration:** At its core, shipd is a spec system. Before any code exists, the agent writes a spec: the behavior you want, as scenarios you can test. Then `/s:build` hands the tasks to agents and checks the result against that spec. Each change ships as its own pull request.

### 3:20–4:00 Epics and PRDs

**On screen:** The author, on camera.

**Narration:** Some ideas are bigger than one change. An epic holds that bigger idea. It is not a spec yet: it records the decisions and lists the changes to come. That suits a product manager who wants to jot down a large idea before anyone plans the detail. Above epics sits the PRD, the Product Requirements Document. A PRD states the problem, who has it, and what success looks like, and it gives context to several epics.

### 4:00–4:25 As high or as deep as you want

**On screen:** The author, on camera.

**Narration:** You choose how high-level or how detailed to go. Stay at a PRD or an epic, and sketch the shape of the work. Or go deep: `/s:plan-deep` walks one spec's riskiest pieces, step by step.

### 4:25–5:00 Autopilot

**On screen:** The author, on camera.

**Narration:** Once you approve an epic, `/s:autopilot` delivers it unattended. It plans and builds each member change, and ships each one as a pull request. Start it in the evening, and wake up to fresh code with your coffee. That is why shipd's mark is a coffee cup. In the next episode, I install shipd and show you how it works.

## Takeaways

- shipd began in July 2025, with an AI writing tickets before it wrote code.
- shipd fills what spec-driven tools left out: epics, PRDs, and work across repositories.
- You plan as high-level or as deep as you want, and autopilot can deliver an approved epic overnight.

## Next

Episode 1 installs shipd and ships a change: [Install shipd and ship a change](01-install-and-build.md).

## Sources

- [Where shipd came from](../../history.md)
- [What is shipd?](../../what-is-shipd.md)
- [PRDs](../../prd.md)
- [Cheatsheet](../../cheatsheet.md)
