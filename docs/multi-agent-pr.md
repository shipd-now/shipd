<!-- doc-type: concept -->

# Multi-agent PR

A multi-agent PR is a pull request whose comment thread is a room. Agents and people take turns on
tasks in that room. The PR room is the mechanism: a protocol over ordinary pull request comments.

## Why a room

Without a protocol, two agents on one pull request talk over each other, and replies get lost. The
room gives every task a state and an owner, so each turn has one agent.

## The model

Each agent posts an Agent Card once. The card names the agent and lists its skills: the kinds of
task it answers.

Every later comment carries a Message. A Message names a task id and the state it moves that task
to:

```mermaid
stateDiagram-v2
    state "input-required" as input
    [*] --> submitted
    [*] --> input
    submitted --> working
    submitted --> input
    working --> input
    input --> working
    submitted --> done
    working --> done
    input --> done
    state done {
        completed
        failed
        canceled
    }
    done --> [*]
```

A terminal task accepts no further Message.

Each comment holds one hidden marker with the JSON for its card or Message. Prose follows the
marker. People read the prose, and the [`shipd room`](room-run.md) verbs read the JSON.

Room traffic uses issue comments, except a review finding's messages, which reply on its thread. A
`completed` reply resolves that thread for the merge.

## Who acts when

An agent acts on an `input-required` task in one of two cases:

- The task names that agent.
- The task names no agent and asks for a skill on the agent's card.

An agent never acts on its own last Message, so it never answers itself.

A round advances when a different agent posts. The `room.max_rounds` key caps a task's rounds, and
the default is 6. At the cap, the task posts `failed`.

## The review gate is the first member

The semantic review gate joins the room as its first agent and posts each review finding as a task.
Another agent, or a person, then fixes the finding, answers it, or asks a question back.

## When to use it

A pull request needs a room when more than one agent, or an agent and a person, take turns on it.

## How to run it

- **`/s:room` in a developer session.** The skill waits in the foreground for this agent's turn,
  then replies in prose.
- **The Actions wake.** [`shipd copilot add --room`](copilot-review.md) installs a workflow that wakes the CI agent on a
  task addressed to it.
- **`shipd room run` on a developer machine.** The runner joins once, then answers each task with
  a headless `/s:room` turn.

The wake acts only on an addressed task. An unaddressed task waits for a live `/s:room` session.

[Run agents in a pull request's room](room-run.md) walks the session turn and both listeners step
by step.

## Reference

- [Run agents in a pull request's room](room-run.md) — the turns and the listeners, step by step.
- [Room reference](room-wake-reference.md) — the room verbs and the Actions wake.
- [Review claims](room-review-claims.md) — one review per head.
- [Give an agent its own GitHub account](agent-identity.md) — the second account a reviewer needs.
- [Customising shipd](customise.md) — the `room` key and its members.
- [Semantic review](semantic-review.md) — the gate that posts review findings.
