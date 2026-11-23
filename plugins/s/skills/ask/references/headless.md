<!-- doc-type: reference -->

# The headless contract

A headless session has no human to ask. This file is the one source of how
such a session settles a decision. `/s:autopilot`, its driven stages, and
external harnesses load this file and follow it. Each part below has a stable
`##` heading, because external loaders read the file by heading.

## Codebase first

Answer what the repository settles. Read the code, the specs, and the epic
before you treat anything as open. Ask nothing about a decision they answer.

## Oracle next

Run `oracle-lookup` for each decision the repository leaves open. Judge its
output under `oracle-contract.md`, in the same directory as this file.

An authoritative `ANSWER` is final. Adopt it as given. Record a
`## Questions and answers` entry with `**Verdict:** ANSWER` and
`**Answered by:** ORACLE`, with its `**Cited:**` sources.

## Default last

Take this path when the oracle returns `INSUFFICIENT`, returns an advisory
answer, fails, or returns no verdict. Adopt the default you recommend. Record
a `## Questions and answers` entry with these fields:

- `**Verdict:** INSUFFICIENT`.
- `**Answered by:** ASSUMPTION`.
- `**Question:**` lists the options, with the default first.
- `**Answer:**` holds the adopted default. It is never empty.
- `**Queued:**` names the `q-<slug>` when the oracle filed one.

Record the entry only when you write or revise a plan. Otherwise, such as a
build coordinator answering a sub-agent `QUESTION:`, answer with the default
and record nothing.

`ASSUMPTION` marks a default that the session chose. It is not a person's
answer, so never record it as `USER`. The gate accepts a well-formed
`ASSUMPTION` entry, and rejects one with no verdict or an empty answer.

## Never a dialog

Open no question round. Call no `AskUserQuestion`. Never wait for a person.
Finish the work to its terminal state.

## Where a caller differs

A caller may override one part and must say so. `/s:epic-grill` records
`**Answered by:** PLANNER` instead of `ASSUMPTION`. Its final round then asks a
human, and the answer rewrites the entry to `USER`. The gate rejects a
`PLANNER` entry as provisional until that rewrite happens.
