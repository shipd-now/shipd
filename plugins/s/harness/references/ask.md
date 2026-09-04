# /s:ask — reference

The fuller protocol behind the ask command's workflow. Read it when the
compact question is hard to shape, when a verdict looks borderline, or when
a capture fails.

## The compact question

Three parts, always, and nothing else:

- **Decision** — the one thing to be decided, stated as a question.
- **Options** — the concrete choices actually under consideration.
- **Recommendation** — the lean inferred from the request and the repo, for
  the durable sources to confirm or overturn.

Infer all three; do not interview. A request too thin to shape into a
decision is refused, not guessed at — ask the user to restate it as a
decision and stop there.

## Verdict grammar

A verdict's first non-blank line is exactly `ANSWER` or `INSUFFICIENT`.

An `ANSWER` carries:

- `Cited:` — one or more sources: a wiki page as `[[slug]]`, an answered
  queue block as `q-<slug>`, or a repo artifact by name (`epic/<slug>`,
  `verified/<capability>`, `change/<slug>`).
- `Evidence:` — the cited text quoted **verbatim**. A paraphrase is not
  evidence.
- the recommendation itself, stated as a position rather than a menu.
- `Authority: advisory` — present only when the position rests on an advisory
  source: a queue block whose `Answer:` value begins `advisory: `, or a wiki
  page carrying an `Authority: advisory` line. Such knowledge was recorded on
  the user's express instruction as guidance, so it **recommends, it never
  settles**: relay the position, keep the line, and still put the decision to
  the user with that position as the recommended first option and its citation
  named. An `ANSWER` with no `Authority:` line is binding, and settles the
  decision without asking.

## Demotion

The bar is a cited source that states a position on **this** decision,
quoted verbatim. An `ANSWER` missing a `Cited:` line or missing an
`Evidence:` line is an ungrounded opinion, so demote it to `INSUFFICIENT`,
say plainly that you demoted it, and take the insufficient branch.

A source that answers a *neighbouring* decision is likewise not an answer
to this one — prefer queueing over stretching a citation.

## Queue and capture

Queue with the compact question's own three parts:

```
python3 "$S/spec_status.py" --root <repo-root> wiki-queue-add <slug> \
  --question "<decision>" --options "<options>" \
  --recommendation "<lean>" --origin "ask"
```

The block lands with `Answer: pending`. What happens to it next is decided by
the **capture rubric**, applied to the distilled reply before any queue write.

## The capture rubric

Three tiers, exactly one per answer:

1. **Include — binding capture.** Durable engineering positions that shape
   future work and are not evidenced by any single repo artifact: a clean
   preference between packages, a data-modeling pattern ("never hard-delete;
   soft-delete flags plus an audit log"), a naming convention ("async
   accessors are `fetch*`, never `get*`"), an error-handling philosophy, a
   testing-depth position. Capture immediately:

   ```
   python3 "$S/spec_status.py" --root <repo-root> wiki-queue-answer <slug> \
     --answer "<the distilled answer>"
   ```

2. **Exclude — discard.** Answers whose durable record already lives somewhere
   better, or that are explicitly scoped to one change: "pin Node 22 in
   .nvmrc" (self-evidencing configuration; a copy goes stale on the next
   bump), "ship this migration without a rollback, just this once". Capture
   nothing and remove the pending block, so the queue stays a pending-only
   worklist:

   ```
   python3 "$S/spec_status.py" --root <repo-root> wiki-queue-discard <slug> \
     --reason "<why this answer is not durable>"
   ```

   The reason is echoed to you, not stored.

3. **Consent-gated — advisory capture, express instruction only.** Workflow
   shortcuts ("stop asking — always run the PR unlock"), process habits
   ("always squash-merge with imperative subjects"), and personal
   presentation preferences. **Never capture these by inference** — a vented
   annoyance is not a standing instruction. Ask one explicit record-this
   question; only an express affirmative captures, and always advisory:

   ```
   python3 "$S/spec_status.py" --root <repo-root> wiki-queue-answer <slug> \
     --advisory --answer "<the distilled answer>"
   ```

   Anything else — declined, deferred, or unaddressed — discards the block.
   The flag stores the answer as `advisory: <text>`, which is what makes a
   later run relay it as a recommendation rather than a rule.

Tie-breakers: a candidate between tiers leans toward consent-gated over
include, and toward exclude over consent-gated — an un-captured answer costs
one future question, a wrongly captured one silently steers work. Existing
context can promote: a standing wiki page or an epic decision already
encoding a related position tips a borderline case toward include. A
preference about the user personally rather than the workspace's engineering
belongs in their personal memory store, not the workspace wiki.

Pass the bare `<slug>`; the verbs prefix `q-` themselves.

Edge cases:

- **No store** — `wiki-init` scaffolds one, but only where a workspace is
  discoverable. With no workspace, skip the queue entirely.
- **Already answered** — both verbs refuse a block that is no longer pending;
  an answered block belongs to the teach drain. Correcting a captured answer
  is `/s:teach <change> Q<n>`'s job.
- **Non-zero exit** — report the failure and relay the answer anyway. Neither
  capture nor discard ever blocks the reply.
- **Nothing queued** — relay for this session only and say plainly that
  nothing durable was captured.

## What a distilled answer looks like

One or two sentences that still make sense to a reader with none of this
session's context: the position chosen and the reason given. Strip the
session chatter; keep the decision.
