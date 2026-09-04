# Capture durability rubric — what the oracle auto-learns

When a user's typed answer resolves an oracle-queued question (a pending
`## q-<slug>` block), classify it into exactly one tier **before** any queue
write. The classification decides whether the answer becomes standing oracle
knowledge, and with what authority.

## The three tiers

### 1. Include — binding capture

Durable engineering positions that shape future work and are not evidenced by
any single repo artifact. Capture immediately via `wiki-queue-answer` (no
flag). The oracle later relays these as binding `ANSWER` verdicts that settle
the decision without re-asking the user.

### 2. Exclude — discard

Answers whose durable record already lives (or will live) somewhere better,
or that are explicitly scoped to one change. Do **not** capture: remove the
pending block via `wiki-queue-discard <slug> --reason "<why>"` so the queue
stays a pending-only worklist. The plan ledger still records the resolution
for the change itself.

### 3. Consent-gated — advisory capture, express instruction only

Workflow shortcuts, process habits, and personal preferences. **Never capture
these by inference** — a vented annoyance is not a standing instruction. Ask
the user one explicit record-this question; only an express affirmative
captures, and always via `wiki-queue-answer --advisory`. Anything else —
declined, deferred, or unaddressed — discards the block.

Advisory knowledge is recommended, never forced: when the oracle later
answers from an advisory source, its `ANSWER` carries `Authority: advisory`,
and the consulting skill still puts the decision to the user with the
oracle's position as the recommended-first option, cited.

## Calibrated examples

| Example answer | Tier | Why |
|---|---|---|
| "Use Zod over Valibot" — a clean choice between packages | Include | The preference between packages is itself durable, beyond what package.json evidences. |
| "Never hard-delete; soft-delete flags plus an audit log" | Include | Cross-cutting data-modeling position no single artifact records. |
| "Async data accessors are `fetch*`, never `get*`" | Include | Convention governing code not yet written. |
| "Fail fast with typed exceptions; no Result wrappers" | Include | Durable architectural stance. |
| "Prefer integration tests against the real engine over mocks" | Include | Standing test-strategy position. |
| "Ship this migration without a rollback script, just this once" | Exclude | Explicitly one-off; the change's plan ledger is its record. |
| "Pin Node 22 in .nvmrc" | Exclude | Self-evidencing configuration; a wiki copy goes stale on the next bump. |
| "Stop asking — always run the PR unlock instead of fixing the tool" | Consent-gated | A workaround stated in annoyance; record only on express instruction. |
| "Always squash-merge with imperative one-line subjects" | Consent-gated | Partly tooling-enforced process etiquette; capture the rest only on request. |
| "Digests use ASCII diagrams, never mermaid" | Consent-gated | Personal presentation preference; the personal memory store (`/s:remember`) is often the better destination — suggest it in the record-this question. |

## Tie-breakers

- When a candidate sits between tiers, lean toward **consent-gated** over
  include, and toward **exclude** over consent-gated — an un-captured answer
  costs one future question; a wrongly captured one silently steers work.
- Existing context can promote: a standing wiki page, an epic decision, or
  tooling already encoding a related position tips a borderline case toward
  include (the answer refines knowledge the oracle already holds).
- A preference about the user personally (tone, presentation, editor habits)
  rather than the workspace's engineering belongs in the personal memory
  store; recommend `/s:remember` instead of an advisory wiki capture.
