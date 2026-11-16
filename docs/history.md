<!-- doc-type: concept -->

# Where shipd came from

This page is my account of how shipd began. I wrote it in the first person because the story is mine. It holds two kinds of fact. The stages come from my memory. The two dates for the repositories come from their first commits.

## Tickets before code

In July 2025, I worked on a project that needed a lot of code, delivered quickly. I dug up an old idea and tested it hard. The idea was simple: ask an AI coding agent to write a user story, complete with tickets, before it writes any code. Each ticket planned one piece of work, and a template set the structure of each ticket.

## Why tickets worked

Tickets made the development loop durable. When an agent ran out of context, a new session resumed from the tickets. Tickets also split the work into pieces, so several agents could work in parallel. The approach worked well for the rest of that project.

## Spec-driven development

At the end of that project, I wanted to scale the approach to my team. Around that time, other people had similar ideas, and spec-driven development became popular. I paused my ticket system, and my team experimented with the new spec-driven tools. They worked, with some success. In shipd terms, each piece of planned work is a [change](what-is-shipd.md), and its requirements live in a spec.

## Where the tools stopped

Those tools worked well for one spec at a time, and less well beyond it. An epic, or any larger piece of work, was hard to run through them. They also had no answer for concerns that span several repositories. So I started a new system to handle those jobs.

## Skills with no name

At first the new tools had no name and no single home. Some skills, such as the planning skill, lived in a private repository. Others lived only in my local Claude settings. The set was not coherent: I used each tool as I saw fit during development, and I never published any of it. Next came a review feature and a pull-request feature.

## automikk

I started to think of the set as "automikk", a way for me to replace my own work with automation, before it had a repository. Eventually I put most of it into one repository. The automikk repository dates its first commit 2026-07-22.

I used the tools every day. I kept improving them, and I kept adding skills.

## shipd

I published the tools as shipd, at shipd.now. The shipd repository dates its first commit 2026-08-13. shipd is open source under the MIT license, so anyone can use it.

## Where to go next

- [What is shipd?](what-is-shipd.md) explains what shipd does today.
- [Getting started](getting-started.md) walks you through the install.
