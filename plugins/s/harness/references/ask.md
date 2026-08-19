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

The block lands with `Answer: pending`. Capture the user's reply against it:

```
python3 "$S/spec_status.py" --root <repo-root> wiki-queue-answer <slug> \
  --answer "<the distilled answer>"
```

Pass the bare `<slug>`; the verb prefixes `q-` itself.

Edge cases:

- **No store** — `wiki-init` scaffolds one, but only where a workspace is
  discoverable. With no workspace, skip the queue entirely.
- **Already answered** — the verb refuses to overwrite an answered block.
  Correcting a captured answer is `/s:teach <change> Q<n>`'s job.
- **Non-zero exit** — report the failure and relay the answer anyway.
  Capture never blocks the reply.
- **Nothing queued** — relay for this session only and say plainly that
  nothing durable was captured.

## What a distilled answer looks like

One or two sentences that still make sense to a reader with none of this
session's context: the position chosen and the reason given. Strip the
session chatter; keep the decision.
