<!-- doc-type: how-to -->

# Rubber duck

The **rubber duck** is an adversarial critic for an idea that nobody has
planned or built yet. You generate the idea; `/s:duck` attacks it. A flawed
assumption caught here costs nothing. The same assumption caught after
`/s:build` costs a change.

The duck is strictly read-only. It edits no file, runs no mutating command,
and emits no spec artifact. It also invokes no other skill and spawns no
agent. It reads the repository and the spec library, so its critique rests on
the real code and the real contracts.

## When to use it

Run `/s:duck` before `/s:plan`, while the idea is still cheap to change. It
fits an idea you suspect has a hole you cannot see yet, or a choice between
two approaches.

Skip it once you know the scope of the change and understand it. Run
`/s:plan` directly instead. For a bug that already shows today, run `/s:fix`.

## How to run it

Pass the idea as the argument:

```sh
/s:duck cache the spec library in memory between engine calls
```

The first reply opens with a banner that names the running plugin version.
Later replies in the session omit it.

### What each reply carries

Each reply challenges something: an unstated assumption, an uncovered case, an
unpriced cost, or a repository constraint. Before it pushes back, the duck
reads the relevant source, the repository's conventions, and the spec library.
A critique that contradicts a binding repository rule is a wrong critique.

Each reply carries at most three critique points, blocking first. Each point
carries one label:

- **blocking** — the idea does not work until someone resolves this point.
- **non-blocking** — the idea works, but this point carries a real cost or
  risk.
- **suggestion** — a lower-priority alternative or refinement.

The duck names the strongest alternative approach when one exists. It skips
style and naming trivia. Every reply ends with exactly one closing question:
the one whose answer moves the idea furthest.

Words set the intensity. "Go easy" or "just a sanity check" softens the duck.
"Grill me" or "tear this apart" hardens it. The rules above hold at every
intensity.

### An implementation request

Ask the duck to write the code or emit the artifacts, and it declines. It
names the skill that does the work, with the exact command, and keeps
critiquing. A worked design in prose stays inside its remit; a diff or a
patch does not.

### The wrap-up debrief

Say "wrap up", or any equivalent cue, to end the session. The duck prints a
debrief as reply text only and writes no file. The debrief carries five
parts, in order:

1. **Problem** — what the session was about, as a problem, not a solution.
2. **Options considered** — each approach, with why it survived or died.
3. **Recommendation** — the option the duck would take, and why.
4. **Known risks** — the open uncertainties and unresolved blocking points.
5. **Next command** — the exit from the map below, as the exact command.

## Reference

### The exit map

When the idea converges, the duck names the skill that picks it up. It never
runs that skill; you decide when to leave.

| the idea turns out to be | exit |
| --- | --- |
| blocked on external unknowns nobody can cite | `/s:research <question>` |
| a feature spanning several independent changes | `/s:epic <feature>` |
| one buildable change, scoped and understood | `/s:plan <the change>` |
| something that already behaves wrongly today | `/s:fix <the problem>` |
| a decision that wants a standing opinion first | `/s:ask <the decision>` |

When the idea is not ready, the duck names what you must settle before the
exit is worth taking.
