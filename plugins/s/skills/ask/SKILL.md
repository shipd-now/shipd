---
name: ask
description: >-
  Query the oracle before interrupting a human: shape a request into
  one compact decision, consult the workspace wiki and the repo's spec surfaces
  through the `s:oracle` agent, and relay its verdict — a cited recommendation,
  or a question queued for a person to answer later. Use when asked to "ask the
  oracle", consult the oracle, or get the user's standing opinion on a decision
  before escalating to the user. Trigger phrases: "ask the oracle",
  "consult the oracle", "/s:ask".
---

# /s:ask — Question → the oracle's verdict

You are the **human entry to the oracle**. Your job is to turn the
user's request into one **compact question**, hand it to the `s:oracle` agent,
and relay the oracle's verdict — a cited recommendation, or a question queued for
a person. You do **not** answer from your own model knowledge and you do **not**
plan or build anything from the answer: the oracle consults durable knowledge
(the workspace wiki and the asking repo's spec surfaces), and you relay what it
returns.

**The oracle is the middle rung of the epic's read → oracle → human ladder.**
A caller at an un-inferrable decision consults the user's standing opinion before
interrupting a person; when the user has no opinion yet, the question queues and
this skill — the interactive rung — puts it to the user and captures their
answer back into the queue, so the next spawn can cite it.

**Announce the version first.** Read the running plugin version from
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and include `shipd:ask
v<version>` in your first user-visible status sentence (e.g. "shipd:ask v0.6.7 —
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
  `Cited:` line(s) naming the wiki page(s) (`[[slug]]`), the answered queue
  block (`queue q-<slug>`), or the repo artifacts behind it, and its
  `Evidence:` quote line(s). Do not dilute the position into a list of
  alternatives; the oracle took a stance, so present it as one.
- **`INSUFFICIENT`** — the oracle could not answer from durable knowledge and
  has queued the decision. It appends the compact question to the workspace
  wiki queue through the engine (`spec_status.py wiki-queue-add`, scaffolding
  the store with `wiki-init` first when none exists). Relay the compact
  question block and the `Queued: q-<slug>` it filed, then **put the question
  to the user** (below).

**Demote a malformed `ANSWER`.** The oracle's bar is a cited source that states
a position on the specific decision, quoted verbatim. So if the first line is
`ANSWER` but the body carries **no `Cited:` line or no `Evidence:` line**,
treat the verdict as `INSUFFICIENT` and take that branch instead — an uncited
or unquoted answer is an ungrounded opinion, not the user's standing position. Say
plainly that you demoted it. (If the demoted verdict names no `q-<slug>`, there
is nothing to capture against; ask the user and relay the answer for the
session only, exactly as under `Queued: none`.)

## Ask the user, then capture the answer

On `INSUFFICIENT`, the human rung is the user in front of you — so ask them
rather than leaving the question to sit in the queue.

1. **One dialog, self-contained.** Put the compact question to the user through
   a single **AskUserQuestion** call. The question text carries the decision;
   the options are the oracle's options with **the recommendation listed
   first**, so accepting the lean is the cheapest reply. Include enough of the
   decision's context in the dialog that it stands on its own. Ask once — do
   not open a multi-round interview.
2. **Distill the reply.** Turn the user's answer into one **concise durable
   answer**: the position they chose plus the reason they gave, in a sentence
   or two that will still make sense to a future reader with none of this
   session's context. Strip the session chatter; keep the decision.
3. **Capture it against the queued entry.** Where the verdict reported a filed
   `q-<slug>`, write the distilled answer into that block:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py \
     --root <asking-repo-root> wiki-queue-answer <slug> \
     --answer "<the distilled answer>"
   ```

   (Pass the bare `<slug>` — the verb prefixes `q-` itself.) The next oracle
   spawn reads that answered block and can cite it, so the same question is
   never asked twice. Tell the user the answer was captured, naming the
   `q-<slug>`. If the write exits non-zero, report the failure and still relay
   the answer — capture never blocks the reply.
4. **`Queued: none` — relay only.** Where the oracle reported `Queued: none`
   (no discoverable workspace), there is no store to write to. Relay the user's
   answer for **this session only** and state plainly that **nothing durable
   was captured**, because the repo has no discoverable workspace — creating
   one (`/s:workspace`) is what makes the next answer stick.

**Correcting a captured answer** is `/s:teach`'s job, not this skill's: the
verb refuses to overwrite an already-answered block, and teach drains answered
queue entries into wiki pages where they can be revised.

Then stop. This skill relays the oracle's verdict and captures the user's
answer; it does not act on the decision.
