# Getting started

You've installed shipd ([quickstart](quickstart.md) if not — it's one
command). This guide is the first real session: set up the ☕ statusline so
you can watch everything that follows, then take one change through
`/s:plan` → `/s:build` and understand every artifact it produces along the
way. By the end you'll know what each file is for, where it lives, and what
you're left with after a change ships.

## 1. Set up the statusline

Claude Code reserves a line at the bottom of every session for a status
command, and shipd ships one worth having before you do anything else:
`plugins/s/integrations/statusline.sh` renders the spec currently in flight —
name, lifecycle status, task progress — live, as the session works:

```
☕ export-json-flag · active · 3/7
```

Register it with one command:

```
shipd statusline install
```

That writes the `statusLine` entry into `~/.claude/settings.json` — creating
the file if you don't have one and leaving every other setting untouched —
and picks the right command for how you run shipd. Run `shipd statusline`
with no arguments first if you want to see what it would register, and what
(if anything) is registered today; bare, it reports and changes nothing.

If you'd rather edit the settings yourself: when you installed via the
installer (the normal case), the script lives inside the versioned plugin
snapshot and its path changes on every update — so resolve the newest
snapshot at render time instead of pinning one:

```json
{
  "statusLine": {
    "type": "command",
    "command": "bash \"$(ls -d \"$HOME\"/.claude/plugins/cache/shipd/s/*/ | sort -V | tail -n 1)integrations/statusline.sh\""
  }
}
```

(`sort -V` orders dotted versions correctly — `0.6.10` after `0.6.9` — and
works with both macOS and GNU `sort`. This is exactly the shape
`shipd statusline install` writes for a snapshot install. If you run shipd
from a checkout of this repository instead, register the repo path directly:
`bash plugins/s/integrations/statusline.sh`.)

It appears at the start of your next session. What you can see, and why it's
worth the thirty seconds:

- **The name** (light blue) is the change that owns the line. An `active`
  change wins wherever it lives — including inside a `.worktrees/` worktree —
  so the line tracks the work even when your session's directory doesn't.
- **The status** is colored by lifecycle: `draft` grey, `ready` light blue,
  `active` yellow, `complete` green, `verified` bright green, `rejected` red.
  One glance tells you whether it's safe to walk away.
- **The task counter** (`3/7`) is read straight from the change's `tasks.md`
  checklist — you watch it tick up as execution sub-agents finish items.
- It grows brackets exactly when they're informative: an epic member shows
  its position (`(EPIC: export-cli, spec 2/5)`), and when several changes
  are live at once you get a position bracket plus an aggregate across all
  of them (`(1 of 3) · 3/7 (7 of 18)`).
- During an autopilot run, a breathing green dot pulses next to `active`,
  driven by the run's heartbeat file — dot pulsing means the run is alive,
  dot gone means finished or stalled.
- It never adds noise: a shipd project with no live change says
  `☕ no active specs`; a repo without `.shipd/` shows nothing at all.

The net effect: for the question you'll ask most — *is it still going, and
how far along?* — you never run a command again. The answer is already on
screen.

## 2. Plan a change: `/s:plan`

Open a session in a repository you want to work on and describe the change
in prose:

```
/s:plan Add a --json flag to the export command so scripts can consume its output
```

The Planner investigates your codebase first and asks only what it genuinely
cannot infer. Then it names the change (say, `export-json-flag`), creates a
dedicated git worktree for it (`.worktrees/export-json-flag` on branch
`change/export-json-flag`), writes the change's artifacts there — and
**stops**. No code is written at this stage.

Your statusline now reads something like:

```
☕ export-json-flag · ready · 0/7
```

### What you get: the artifact set

Every change, regardless of size, carries the same lean artifact set under
`.shipd/planned/<change>/`:

```
.shipd/planned/export-json-flag/
  plan.md                     the idea and the binding decisions
  tasks.md                    the implementation checklist
  specs/
    export-command/
      spec.md                 a delta spec per affected capability
```

**`plan.md` — the decision document.** This is the one file that drives
everything else. It records the change's status on line 2 (the same status
the statusline colors) and two required sections:

- `## Idea` — a one-sentence summary, then `### Motivation` (why, at most
  two sentences, grounded in what the Planner actually found — never a
  guess), `### Details` (the concrete what: the changes, the affected
  capabilities, the impact), and `### Non-goals` (what this change
  deliberately does *not* do — often the most valuable section, because it's
  where scope creep goes to die).
- `## Implementation` — the binding technical decisions, ADR-style: each
  with a rationale and, where it matters, the rejected alternative. Plus the
  risks and their guards.

**`specs/<capability>/spec.md` — the delta spec.** The testable contract.
For each capability the change touches, a delta file states what's being
`ADDED`, `MODIFIED`, `REMOVED`, or `RENAMED` as requirements — SHALL-style
prose, each with concrete scenarios:

```markdown
## ADDED Requirements

### Requirement: Export supports JSON output
id: export-json-output

The export command SHALL accept a `--json` flag that renders the export
as a single JSON object on stdout.

#### Scenario: JSON flag produces parseable output
- **WHEN** `export --json` is run
- **THEN** stdout parses as JSON and contains the exported records
```

These scenarios are not decoration — they're what the build is verified
against at the end, and what an adversarial validator later tries to refute
by exercising the real code.

**`tasks.md` — the checklist.** The implementation plan as flippable
checkboxes, each tagged with the requirement it satisfies:

```markdown
## 1. Flag and rendering

- [ ] 1.1 [req: export-json-output] Add the `--json` flag to the export
      argument parser and route it to a JSON renderer.
```

The `[req: …]` tags mean every task traces to a requirement and every
requirement is covered by tasks — nothing is built that wasn't specified,
nothing specified goes unbuilt. This is also the file the statusline counts:
`0/7` is unchecked-boxes-over-total, and executors flip boxes as they go.

### The context gate, and your one job

Planning ends with a deterministic context-sufficiency gate. Pass, and the
change is promoted to `ready`. Fail, and it's parked as `rejected` with the
gaps written into `plan.md` for you to fill — the engine refuses to build on
guesses.

Then comes the single most valuable moment in the whole loop: **read the
three files.** Right now the entire change is markdown — wrong assumptions,
missing non-goals, a decision you'd have made differently — all of it costs
one edit to fix. After the build it costs a rework. Correct course here.

## 3. Build it: `/s:build`

```
/s:build export-json-flag
```

The Orchestrator adopts the planned change and continues in its worktree. It
delegates the checklist to execution sub-agents running one model tier down,
answers their questions, and keeps `tasks.md` current — which is why your
statusline now earns its keep:

```
☕ export-json-flag · active · 3/7
```

Boxes flip, the counter climbs, the status turned yellow the moment work
began. Prefer a full-screen view? `shipd board` renders the delivery board;
`shipd status` prints the same one-liner on demand.

When the checklist is done, the result is **verified against the delta
spec's scenarios** — the WHEN/THEN blocks you read in step 2 — not against a
vibe of "seems done". Only then does the engine merge and archive.

### What you get when it's done

Three durable outcomes, in three places:

1. **Working code**, committed on `change/export-json-flag` in its worktree,
   ready to ship as a PR — one change, one branch, one PR.
2. **An updated master library.** The delta is merged into
   `.shipd/verified/<capability>/spec.md` — the single source of truth for
   how the system behaves *now*. Your `export-command` capability
   permanently gained the JSON-output requirement, scenarios included. This
   is the part that compounds: the next `/s:plan` in this repo starts from a
   library that already knows what the export command does, so every change
   makes the next one better-informed.
3. **An immutable archive.** The change's full artifact set moves to
   `.shipd/completed/<date>-export-json-flag/` — plan, delta, checklist,
   all checkboxes flipped. Six months from now, "why does `--json` work
   this way?" has an answer with a date on it: the motivation, the decisions,
   the rejected alternatives, and exactly which requirement each task served.

`.shipd/planned/` holds only live work, so it's empty again — and the
statusline says so: `☕ no active specs`.

## Where you are now

You've seen the whole loop: a change is born as three reviewable markdown
files, built against a testable contract, verified against that contract's
scenarios, and retired into a library that documents the system as-built
plus an archive that documents *why*. The statusline watched all of it.

From here:

- [Quickstart](quickstart.md) — the condensed six-step version, including
  `shipd doctor` and the `/s:onboard` guided tour
- [Cheatsheet](cheatsheet.md) — the command lookup reference: every `/s:`
  command and every `shipd` verb with its options and one example
- [What is shipd?](what-is-shipd.md) — the model behind the loop
- [`.shipd/README.md`](../.shipd/README.md) — the full requirement and delta
  grammar these artifacts follow
- The README's [Skills table](../README.md#skills) — every `/s:` command,
  including `/s:epic` to decompose a feature into member changes and
  `/s:review` for a semantic review before you push
