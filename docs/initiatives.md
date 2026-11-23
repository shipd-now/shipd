<!-- doc-type: how-to -->

# Initiatives

An initiative is a workspace brief that states the outcomes an epic delivers
against. It sits above epics: an initiative holds epics, and an epic holds
member changes. The [PRDs](prd.md) page owns the diagram of that hierarchy.

`/s:initiative` writes, lists, and reviews briefs, and attaches a brief to an
epic.

## When to use it

Use an initiative when several epics, or one large epic, serve a goal that a
team tracks over time. The brief records what success looks like. Each epic
then names the brief it delivers against.

A brief lives in the workspace, not in the repository. Its path is
`initiatives/<slug>/brief.md` under the workspace's content directory. Every
verb needs a discoverable workspace. When no workspace exists, the verb
writes nothing. Set one up first with `/s:workspace init`, as
[Workspaces](workspaces.md) describes.

A brief has this shape:

```
# checkout-speed
Status: open
Project: web-store

Cut checkout time so that most orders finish in under a minute.

## Requirements

- [ ] Median checkout time is under 60 seconds.
- [ ] Abandoned checkouts fall by a quarter.
```

The `Project:` line is optional. It names a project that the workspace
declares. Each requirement is an outcome, never a task: it says what is
true when the initiative succeeds, not what work to run.

A brief carries one of three statuses:

| status | meaning |
| --- | --- |
| `open` | At least one requirement is still unticked. |
| `achieved` | Every requirement carries a tick. The engine derives this status. |
| `dropped` | The team dropped the initiative. A sync never changes it. |

## How to run it

1. **Create a brief.** Run `/s:initiative new <slug>`. The skill reads the
   workspace, asks one batched round, and installs the brief at
   `Status: open`.
2. **Attach it to an epic.** Run `/s:initiative set <epic> <initiative>`.
   The skill writes the `Initiative:` line into the epic's header. It ships
   the edit as a pull request and prints its URL.
3. **Tick outcomes.** Run `/s:initiative review <slug>`. The skill walks
   each open requirement with you and ticks the ones you confirm. Then it
   syncs the status, which becomes `achieved` once you tick every
   requirement.

Run `/s:initiative list` at any time to see every brief's status and
progress.

`new` and `review` write only to the workspace, so they open no pull
request. `set` edits the epic in the repository, so it ships as a pull
request.

### Attachment rules

- An epic carries exactly one initiative. A second `set` replaces the first.
- A member change derives its initiative through its epic.
- `set` refuses a member change. It names the epic to attach instead.
- A standalone change carries its own `Initiative:` line, which `/s:plan`
  writes.

To write the epic itself, see [Epics](epics.md).

## Reference

| verb | arguments | what it writes |
| --- | --- | --- |
| `new` | `<slug>` | A new brief at `Status: open`, in the workspace. |
| `list` | none | Nothing. It reports each brief's status and progress. |
| `review` | `<slug>` | Ticked requirements and the synced status, in the workspace. |
| `set` | `<epic> <initiative>` | The epic's `Initiative:` line, through a pull request. |

Two `shipd` verbs support the skill:

- `shipd workspace` prints the roster: the workspace root, its projects, and
  its initiatives.
- `shipd lint --initiative <slug>` checks the structure of one brief.

See also:

- [Epics](epics.md) — the epics an initiative holds.
- [Workspaces](workspaces.md) — the workspace that holds the briefs.
- [PRDs](prd.md) — the discover phase and the hierarchy diagram.
