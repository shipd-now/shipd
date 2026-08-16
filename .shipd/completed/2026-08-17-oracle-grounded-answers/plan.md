# oracle-grounded-answers
Status: verified

## Idea

Make the ask-mikk oracle answer only from definitive, cited evidence, defer
everything else to the interactive user, and capture the user's answer so the
next oracle spawn can cite it.

### Motivation

The oracle's answering bar is soft — `ANSWER` "when the wiki or a repo surface
holds the answer" — so it can dress model-knowledge opinions in loosely related
citations, which reads as an LLM answering everything without data. Answers a
user supplies interactively also never compound: `/s:ask` stops at "queued" and
plan-round resolutions stay in the session ledger while the queue block sits
pending.

### Details

- Tighten `plugins/s/agents/oracle.md`: default verdict `INSUFFICIENT`, no
  model-knowledge answers, verbatim `Evidence:` quotes required under `ANSWER`,
  and a new read of answered-but-undrained queue entries.
- New engine verb `wiki-queue-answer` in `spec_status.py` writing a distilled
  answer into a queued block's `Answer:` line, auto-committed like
  `wiki-queue-add`.
- `/s:ask`: on `INSUFFICIENT`, put the compact question to the user
  (AskUserQuestion, recommendation first), distill the reply, capture it via
  `wiki-queue-answer`.
- `/s:plan`: demote malformed `ANSWER` verdicts; capture typed-round
  resolutions of `INSUFFICIENT` decisions the same way.
- New `docs/oracle.md` user guide with the ladder and capture-loop diagram.

Affected capabilities: `shipd-ask`, `shipd-wiki`, `shipd-plan` (all modified).
Impact: `plugins/s/agents/oracle.md`, `plugins/s/skills/ask/SKILL.md`,
`plugins/s/skills/plan/SKILL.md`,
`plugins/s/skills/build/scripts/spec_status.py`,
`plugins/s/skills/build/tests/test_spec_status.py`, `docs/oracle.md` (new),
`plugins/s/.claude-plugin/plugin.json` (version bump). No new dependencies.

### Non-goals

- No change to autopilot's unattended behavior: `INSUFFICIENT` still parks on
  the asker's recommended default with the question queued.
- No personal-store fallback: where no workspace is discoverable
  (`Queued: none`), the answer is relayed for the session only and nothing
  durable is written.
- No change to `/s:teach`: it stays the sole distiller of queue entries into
  wiki pages.
- No embeddings or search service — retrieval stays index- and grep-based over
  markdown.

## Implementation

- **Verb shape.** `wiki-queue-answer <slug> --answer "<text>"` (plus the global
  `--root`), resolving the workspace store exactly like `wiki-queue-add` and
  accepting the bare slug (the verb prefixes `q-` itself). It replaces the
  matching block's `- Answer: pending` line with `- Answer: <text>`, prints the
  `q-<slug>`, and exits 0; it writes nothing and exits non-zero when the store
  or block is missing or the block's answer is no longer `pending` — an
  answered block belongs to the teach drain. Rejected: a `--force` overwrite
  flag — correcting an answer is `/s:teach`'s job, not the capture path's.
- **Observed premises.** `wiki-queue-add retention …` prints `q-retention` and
  writes a block whose last line is `- Answer: pending` (exit 0, observed in a
  scratch workspace); `cat wiki queue` prints that block; both exit 1 with
  "no workspace found" outside a workspace (observed). The new verb mirrors
  this resolution and error behavior.
- **Auto-commit.** The verb routes through the same scoped auto-commit path as
  `wiki-queue-add`, committing exactly `queue.md` (delta modifies
  `wiki-autocommit` to enumerate it).
- **Ladder placement.** Answered queue entries are read inside the job-store
  rung after the store's pages — a distilled page is the canonical durable
  position; the raw answer is only the bridge until `/s:teach` drains it.
  Citation form: `Cited: queue q-<slug>`. Rejected: a separate rung above
  pages — it would outrank pages distilled from the same answers.
- **Grounding bar.** `oracle.md` states: the default verdict is
  `INSUFFICIENT`; never answer from model knowledge; `ANSWER` requires at
  least one verbatim `Evidence:` quote from a cited source that states a
  position on the specific decision (topical relevance is not enough). Because
  prompt-only compliance is exactly the failure being fixed, callers also
  demote an `ANSWER` missing `Cited:` or `Evidence:` to `INSUFFICIENT` — a
  false demotion only degrades to today's safe fallback paths.
- **Interactivity split.** The oracle stays non-interactive by contract;
  asking lives in the interactive callers. `/s:ask` uses a single
  self-contained AskUserQuestion dialog (recommendation listed first);
  `/s:plan` keeps its typed rounds per its own contract and captures after the
  round. Where the verdict reports `Queued: none`, capture is skipped and the
  caller states that nothing durable was written.
- **Docs.** `docs/oracle.md` follows the existing `docs/` voice (short
  sections, user-facing): what the oracle is, one ASCII diagram of the
  read → ask-mikk → human ladder with the capture loop, a worked `ANSWER` and
  `INSUFFICIENT` example, and the correction path via `/s:teach`.
- **Release.** Bump `plugins/s/.claude-plugin/plugin.json` to `0.6.125` in this
  change — the plugin cache snapshot is keyed by version (AGENTS.md).

## Questions and answers

### Q1: How is a user-supplied answer captured for future oracle reads?
- **Question:** When a user interactively answers a question the oracle queued,
  how should that answer be captured? Options: (a) new engine verb
  `wiki-queue-answer` writing the block's `Answer:` line, plus an oracle ladder
  read of answered-but-undrained queue entries; (b) emit a full wiki page at
  answer time; (c) capture into the personal memory store.
  Recommendation: (a).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option (a). The queue grammar already anticipates the
  answered-but-undrained state (`Answer:` is "pending until the user supplies
  an answer"); teach is contractually the sole page distiller, so answer-time
  page emission would bypass its bounded runs and duplicate-avoidance; engine
  mediation is a binding epic decision; and without the ladder read an answered
  entry stays invisible until a teach run, so knowledge would not compound.
  Option (c) is a category error — queued questions are workspace knowledge,
  not personal preferences.
- **Cited:** verified/shipd-wiki, verified/shipd-teach, verified/shipd-ask,
  epic/mikk-knowledge

### Q2: Which callers adopt the ask-then-capture loop?
- **Question:** Should both interactive callers (`/s:ask` with a dialog,
  `/s:plan` capturing after its typed rounds) adopt the loop, or `/s:ask`
  alone? Options: (a) both, autopilot keeps queue-and-park; (b) `/s:ask` only.
  Recommendation: (a).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option (a). The epic rejected insufficient-only handling because
  knowledge never compounds; leaving a plan-round answer stranded in the
  session ledger while the same question sits pending in the queue is that
  exact failure. The caller split matches the epic's ladder decision: typed
  rounds in plan, a recommendation-first dialog in `/s:ask`, and unattended
  runs keep parking semantics.
- **Cited:** epic/mikk-knowledge, verified/shipd-plan, verified/shipd-interaction

### Q3: Where does capture go when no workspace is discoverable?
- **Question:** With `Queued: none`, should the answer be captured anywhere?
  Options: (a) relay-only, suggest workspace setup; (b) fall back to the
  personal memory store. Recommendation: (a).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Relay-only. The personal store's contract is user preferences —
  a project decision there would break `/s:memory` and `/s:forget`'s
  assumptions — and the engine already treats a missing workspace as a
  deliberate hard stop, not an invitation to fall back. The durable fix is
  creating the workspace; a genuinely personal preference still has
  `/s:remember` as its sanctioned route.
- **Cited:** verified/shipd-memory, verified/shipd-wiki, verified/shipd-ask

### Q4: How is the stricter answering bar enforced?
- **Question:** Prompt-level tightening only, or prompt plus caller-side
  demotion of a malformed `ANSWER` to `INSUFFICIENT`? Options: (a) both;
  (b) prompt only. Recommendation: (a).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Both. The verdict contract is machine-branchable by design and
  an uncited `ANSWER` is already contract-malformed, so demotion is
  enforcement of the existing contract; prompt-only would make this the one
  seam guaranteed solely by agent good behavior — the failure being fixed. A
  false demotion degrades safely to the `INSUFFICIENT` path.
- **Cited:** verified/shipd-ask, epic/mikk-knowledge
