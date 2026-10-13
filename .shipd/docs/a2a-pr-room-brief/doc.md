# A2A-aligned PR room brief

Verbatim brief supplied at epic authoring: align shipd's PR room on the A2A
data model while keeping GitHub as the transport.

Yes — **A2A (Agent2Agent Protocol)** is the standard to align with. It hit **v1.0 in March 2026**, is Linux Foundation-governed, and has 150+ orgs behind it. But you don't need to run a full A2A server — you can borrow its data model while keeping GitHub as your transport.

## The mapping

| A2A concept | Your PR Room equivalent |
|---|---|
| **Agent Card** (discovery, capabilities, skills) | A `[pr-room]` comment or a field in your shipd config listing which agents are on a PR |
| **Message** (`role`, `parts`, `contextId`, `taskId`) | Your `[agent:...] [type:...] [status:...]` comment prefix |
| **Task** (lifecycle: `submitted → working → completed`) | The PR itself — or a specific review thread |
| **Context** (`contextId` groups messages) | The PR number / comment thread |
| **Transport** (JSON-RPC over HTTPS, SSE) | GitHub comments + webhooks (you already have this) |

## What to actually follow from the spec

The A2A spec at [a2a-protocol.org/latest/specification](https://a2a-protocol.org/latest/specification/) defines:

- **AgentCard** — `name`, `description`, `skills[]`, `capabilities`, `securitySchemes`. You can emit a minimal one per agent in the PR room so any harness can discover "who's here and what they do."
- **Message** — `role` (`"user"` | `"agent"`), `parts[]` (content), `contextId` (the PR), `taskId` (the thread), `metadata`. Your comment format is essentially a serialized Message.
- **Task states** — `submitted`, `working`, `input-required`, `completed`, `failed`, `canceled`. Maps naturally to your `status:open` / `status:closed`.

## Why not full A2A?

Full A2A means each agent runs an HTTP endpoint with JSON-RPC, Agent Card discovery at a well-known URL, SSE streaming, push notification configs. That's the right architecture for enterprise agent-to-agent delegation. For a PR comment thread, it's a sledgehammer.

**What you want is A2A's data model + GitHub's transport.** That's a valid subset — the spec explicitly says the data model is protocol-agnostic (Layer 1), and the transport is pluggable (Layer 3). You're just choosing "GitHub comments" as your binding instead of JSON-RPC/HTTPS.

## Concrete suggestion for shipd

Given shipd's architecture (spec-driven, multi-harness, already has `/s:review` posting to PRs, already has the GitHub Actions workflow for review gates):

1. **Define the comment schema** as a JSON Schema that mirrors A2A's `Message` object. Agents post it as a code block or structured prefix in the PR comment. Humans still read it as plain text; agents parse it.

2. **Agent Card as a PR label or header comment.** When an agent joins a PR room, it posts (or updates) a comment with its minimal Agent Card JSON. This is your discovery mechanism — any other agent reading the PR can see who's available and what they can do.

3. **Webhook → wake** stays as I described before. Your shipd GitHub Action (you already have one for the review gate) becomes the "A2A client" that receives the `pull_request_review_comment` event, parses the Message, and spawns the right agent with the `contextId` (PR) and `taskId` (thread) as context.

4. **The `shipd` CLI gets a `room` verb.** `shipd room join <pr>`, `shipd room list <pr>`, `shipd room message <pr> <thread> "..."`. This is the harness-agnostic surface — any harness that can run `shipd room message` participates, regardless of whether it's Claude Code, Codex, OpenCode, etc.

5. **Loop prevention** via A2A's task state machine: an agent only acts on `input-required` (your `status:open`) tasks, and transitions them to `completed` (your `status:closed`) when done. Max-rounds counter as a safety net.

## The one-sentence answer

Follow **A2A v1.0's data model** (Agent Card, Message, Task states) as your schema, use **GitHub comments + webhooks** as your transport binding, and expose it through **shipd's CLI** so any harness can participate. You get standard alignment (interoperability with anything else that speaks A2A later) without the operational overhead of running A2A endpoints.

The spec is at `a2a-protocol.org/latest/specification` and the reference SDKs are at `github.com/a2aproject/A2A` — the Python and TypeScript SDKs are the most mature for v1.0.
