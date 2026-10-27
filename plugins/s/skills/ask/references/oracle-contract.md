# The oracle consultation contract

The oracle is an **inline consultation**, not an agent. A caller that hits a
decision it cannot infer — `/s:ask`, `/s:plan`, or an autopilot session —
follows this contract itself: one engine call, then a judgement from that
output alone. Spawn no agent. Read this file once per session; later
consultations cost only the lookup output.

## 1. Shape one compact question

One decision-ready unit, never a raw trace or an essay prompt:

- **Decision** — the one thing to decide, as a question.
- **Options** — the concrete choices under consideration.
- **Recommendation** — the asker's lean.

## 2. Run the lookup

```
python3 <STATUS_PY> --root <asking-root> oracle-lookup <term> <term> ...
```

- Pick two to six **distinctive** terms from the decision and its options
  (names, verbs, nouns that would appear in a settling sentence). A unit
  matches on at least two distinct terms.
- Run it **once**. When it ends `no evidence found`, retry **at most once**
  with alternative terms (synonyms, the other option's name) before judging.
- The verb searches in ladder order: personal memory, the workspace chain
  (pages, then answered queue blocks), the base store, then spec surfaces
  (focus project first). It writes nothing and exits 0. If it exits non-zero
  or is unavailable, the verdict is `INSUFFICIENT`.
- Each line is a cited snippet: `<citation> [advisory] — "<snippet>"`.
  The section headed `pending queue (duplicate check — not evidence)` is
  never evidence.

## 3. Judge from that output alone

- **Default verdict: `INSUFFICIENT`.** Never answer from model knowledge.
- Take the **first** rung's snippet that **states a position on the specific
  decision**. Topical relevance never suffices: a snippet about caching does
  not answer "which TTL". If you cannot point at a sentence that takes the
  position, you have no answer.
- `ANSWER` needs a `Cited:` line copied **verbatim** from the snippet's
  citation (`[[slug]]`, `[[slug]] (personal)`, `[[slug]] (inherited <ws-root>)`,
  `[[slug]] (base)`, `queue q-<slug>`, `verified/<cap> (<req-id>)`,
  `epic/<slug>`, `research/<slug>`) and an `Evidence:` line quoting the
  snippet **verbatim** — the quote must appear in the lookup output. Never
  derive a citation marker any other way.
- Snippet tagged `[advisory]`: add an `Authority: advisory` line directly
  after the position. It was captured as a recommendation, so the caller
  recommends it and still puts the decision to the user. With no advisory
  snippet, emit no `Authority:` line.
- When in doubt, `INSUFFICIENT`: every caller has a safe path for it.

## 4. The verdict grammar

The first non-blank line is exactly `ANSWER` or `INSUFFICIENT`. Callers that
find an `ANSWER` with no `Cited:` or no `Evidence:` line demote it to
`INSUFFICIENT`.

```
ANSWER
Use a single append-only log with per-entry timestamps; it matches how the
store already records provenance and keeps readers grep-friendly.
Cited: [[logging-conventions]]
Cited: [[naming-conventions]] (base)
Cited: [[retry-policy]] (inherited /ws/outer)
Cited: verified/shipd-wiki (wiki-log-append)
Evidence: [[logging-conventions]] — "Every store event appends one dated line
to log.md; entries are never rewritten in place."
```

Advisory-backed answers add one line:

```
ANSWER
Run the PR unlock first rather than fixing the tool in the same pass.
Authority: advisory
Cited: queue q-pr-unlock
Evidence: queue q-pr-unlock — "advisory: stop asking — always run the PR
unlock instead of fixing the tool."
```

```
INSUFFICIENT
Question: Which retention window should the queue enforce for answered entries?
Options: keep forever | prune after 90 days | prune after one release
Recommendation: prune after one release
Queued: q-answered-queue-retention
```

## 5. Queue an `INSUFFICIENT`

Queueing is the only write, through engine verbs only, always into the asking
workspace's own store (or the repo-local fallback store) — never the base.

1. **Duplicate check.** If the lookup's pending list holds an equivalent
   question, do not queue again: `Queued: q-<existing>`.
2. **Append.**
   ```
   python3 <STATUS_PY> --root <asking-root> wiki-queue-add <slug> \
     --question "<decision>" --options "<options>" \
     --recommendation "<lean>" --origin "<asking-repo>[/<surface>]"
   ```
   Pass the bare `<slug>`; report the `q-<slug>` the verb prints.
3. **Missing store.** Run `wiki-init` first, then queue.
4. **Nowhere to write.** With neither a discoverable workspace nor a content
   directory, queue nothing: `Queued: none (<the missing prerequisites the
   verb named — no workspace at <asking-root> and no content directory>)`.

Never edit `queue.md` or any wiki file directly, and never block the caller.
