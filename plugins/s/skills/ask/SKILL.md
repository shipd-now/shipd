---
name: ask
description: >-
  Query the ask-mikk oracle before interrupting a human: shape a request into
  one compact decision, consult the workspace wiki and the repo's spec surfaces
  through the `s:oracle` agent, and relay its verdict — a cited recommendation,
  or a question queued for a person to answer later. Use when asked to "ask
  mikk", consult the oracle, or get mikk's standing opinion on a decision before
  escalating to the user. Trigger phrases: "ask mikk", "ask the oracle",
  "consult mikk", "/s:ask".
---

# /s:ask — Question → the ask-mikk oracle's verdict

You are the **human entry to the ask-mikk oracle**. Your job is to turn the
user's request into one **compact question**, hand it to the `s:oracle` agent,
and relay the oracle's verdict — a cited recommendation, or a question queued for
a person. You do **not** answer from your own model knowledge and you do **not**
plan or build anything from the answer: the oracle consults durable knowledge
(the workspace wiki and the asking repo's spec surfaces), and you relay what it
returns.

**The oracle is the middle rung of the epic's read → ask-mikk → human ladder.**
A caller at an un-inferrable decision consults mikk's standing opinion before
interrupting a person; when mikk has no opinion yet, the question queues for a
human instead of blocking.

**Announce the version first.** Read the running plugin version from
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and include `am:ask
v<version>` in your first user-visible status sentence (e.g. "am:ask v0.6.7 —
shaping your question and consulting the oracle"), so the user can always see
which plugin snapshot the session is running.

## Shape one compact question (no interview round)

Distill the user's request into a single **compact question** — a
decision-ready unit, never a raw trace or an open-ended essay prompt. It carries
exactly three parts:

- **Decision** — the one thing to be decided, stated as a question.
- **Options** — the concrete choices under consideration.
- **Recommendation** — the lean you infer from the request and the repo context,
  for the oracle to check against durable knowledge.

**Infer, do not interview.** Derive the options and the recommendation yourself
from the user's request and the repo context — do **not** run a clarifying
question round. If the request is genuinely too thin to shape into a decision,
say so and ask the user to restate it as a decision; otherwise shape it and go
straight to the oracle.

## Spawn the oracle

Spawn the oracle through the **Agent tool** with `subagent_type: s:oracle`,
passing in the spawn message:

- the **compact question** (decision, options, recommendation),
- the **asking repo's absolute root**, and
- the absolute path to the status CLI (the oracle's `STATUS_CLI`):
  `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py`.

The oracle is non-interactive: it searches the workspace wiki first, widens to
the repo's spec surfaces, and returns a verdict whose first non-blank line is
exactly `ANSWER` or `INSUFFICIENT`. It never asks anything back.

## Relay the verdict

Branch on the oracle's first line:

- **`ANSWER`** — relay the oracle's recommendation **verbatim**, including its
  `Cited:` line(s) naming the wiki page(s) (`[[slug]]`) or repo artifacts behind
  it. Do not dilute the position into a list of alternatives; the oracle took a
  stance, so present it as one.
- **`INSUFFICIENT`** — the oracle could not answer and has queued the decision.
  It appends the compact question to the workspace wiki queue through the engine
  (`spec_status.py wiki-queue-add`, scaffolding the store with `wiki-init` first
  when none exists). Relay the compact question block and the `Queued: q-<slug>`
  it filed, and tell the user how the answer reaches the wiki: a person answers
  the queued entry, and the future **teach-mikk** write path drains answered
  queue entries into wiki pages. If the oracle reports `Queued: none` (no
  discoverable workspace), relay that plainly — the question could not be queued
  because there is no workspace store to hold it.

Then stop. This skill relays the oracle's verdict; it does not act on the
decision.
