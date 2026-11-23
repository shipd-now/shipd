<!-- doc-type: how-to -->

# Epics

An epic decomposes a feature too large for one change into member changes.
The members share one set of decisions, which the epic records once. The
epic lives at `.shipd/epics/<slug>/epic.md`, and each member inherits its
decisions. `/s:epic` writes the epic, and `/s:explain` explains one.

An epic sits above changes, and an initiative sits above epics.
The [PRDs](prd.md) page owns the diagram of that hierarchy.

## When to use it

Use an epic when one feature needs more than one change. Typical signs:

- the feature crosses several capabilities;
- the work splits along clear seams into separate pull requests;
- several changes must obey the same architectural choice.

A feature that fits in one change needs no epic. Plan it with [`/s:plan`](plan.md).

### The epic artifact

The epic file holds four required sections:

- **Introduction** — the problem, the feature, and the intended outcome. It
  closes with a `### Non-goals` subsection.
- **Decisions** — the cross-cutting choices that every member inherits.
- **Design** — the shape of the whole feature and the seams it splits along.
- **Changes** — the stub table, one row for each member.

The stub table rates each member on four columns: Code, Integration,
Unknowns, and Risk. Each rating is `low`, `medium`, or `high`. The optional
`After` column lists the sibling members that a member must follow.

An epic carries one of four statuses:

| status | meaning |
| --- | --- |
| `draft` | The author is still writing the epic. |
| `ready` | The epic is approved and lint-clean. |
| `active` | Delivery of its members is under way. |
| `complete` | Every member has shipped. |

## How to run it

### Write an epic

1. Run `/s:epic` and describe the feature.
2. The skill creates the `epic-<slug>` worktree and works inside it.
3. The skill reads the repository before it asks you anything.
4. Answer its one batched round of questions. The recommended option comes
   first in each question.
5. The skill writes the epic at `draft` and lints it until it is clean.
6. Approve the epic. The skill promotes it to `ready`.
7. The skill ships the epic as a pull request and prints its URL.

`/s:epic` never plans a member. Plan each member with `/s:plan <member>`, or
plan every member in one pass with [`/s:epic-grill <epic>`](epic-grill.md). See
[Epic grill](epic-grill.md).

### Amend a live epic

Run `/s:epic <slug> amend` to change an epic that is already `ready` or
`active`.

1. The skill reads the epic. It refuses a `draft` epic, which you edit in its
   authoring worktree instead.
2. The skill creates a fresh `epic-amend-<slug>` worktree.
3. The skill edits the Decisions section and the reference shelves only.
4. The skill rewrites each touched decision as the current fact. Git history
   holds the old wording.
5. The skill lints the epic and checks that no protected section changed.
6. The skill ships the amendment as a pull request.

Amend mode protects the Introduction, Design, Changes, and header sections.
An edit to one of them is a new decomposition, not an amendment.

### Explain an epic

Run `/s:explain <epic>` to read what an epic is for. The skill prints a short
explanation of the epic and of its delivery state. It is read-only: it writes
no file and changes no status.

### Deliver the members

After you plan the members, deliver them with [Autopilot](autopilot.md).
Check that the plans still hold against `main` with [Drift](drift.md).
Attach the epic to an outcome brief with [Initiatives](initiatives.md).

## Reference

| command | what it does |
| --- | --- |
| `/s:epic` | Writes a new epic and ships it as a pull request. |
| `/s:epic <slug> amend` | Changes a live epic's Decisions and shelves. |
| `/s:explain <epic>` | Prints a read-only explanation of an epic. |
| `shipd epic <slug>` | Prints an epic's status, metadata, and member states. |
| `shipd list epics` | Lists every epic across the root and its worktrees. |
| `shipd lint --epic <slug>` | Checks the structure of one epic. |
| [`shipd board --epic <slug>`](build.md) | Shows the delivery board for one epic. |

See also:

- [Epic grill](epic-grill.md) — plan every member in one pass.
- [Autopilot](autopilot.md) — drive the members to shipped pull requests.
- [Drift](drift.md) — judge whether gated plans still hold.
- [Initiatives](initiatives.md) — the outcomes an epic delivers against.
- [PRDs](prd.md) — the discover phase and the hierarchy diagram.
