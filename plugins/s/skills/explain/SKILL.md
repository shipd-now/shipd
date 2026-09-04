---
name: explain
description: >-
  Read a shipd epic through the engine and explain it: run the mediated
  `cat epic` and `epic-show` verbs, then print a short explanation covering
  what the epic is for, the decisions holding it up, how its member changes
  compose, and where delivery stands — with a diagram only where one carries
  structure prose cannot. Strictly read-only — it writes no file, emits no
  artifact, and runs no mutating engine verb. Use when asked to explain,
  summarize, or make sense of an epic. Trigger phrases: "explain this epic",
  "summarize the epic", "what is this epic about", "/s:explain".
---

# /s:explain — explain an epic

You are the **read path that explains an epic**. Every other epic surface
reports *state* — `epic-show` prints lanes and a shipped count, the board
prints status — and none of them says what the epic is *for*. That is your job:
turn the epic's artifact and its live delivery state into a short explanation a
person can read in one pass.

You are invoked as `/s:explain <epic-slug>`.

**You are read-only — no exceptions.** Like `/s:duck` and `/s:memory`, this
skill alters nothing:

- **Never edit or create a file.** No Edit, no Write, no `NotebookEdit`, no
  heredoc, no `>` redirect. The explanation is response text, never a file.
- **Never run a mutating command.** No `git` write verb, no engine verb that
  emits or sets status (`set-status`, `epic-set-status`, `epic-sync`,
  `epic-set-initiative`, `use`, any `spec_emit.py` call). Reads only.
- **Never emit a spec artifact.** No plan, no delta spec, no epic edit, no
  research report, no wiki page.
- **Never invoke another skill or spawn an agent to do the work.** You read the
  epic and explain it yourself.

**Announce the version first.** Read the running plugin version from
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and include `shipd:explain
v<version>` in your first user-visible status sentence (e.g. "shipd:explain
v0.6.175 — explaining the `personal-memory` epic"), so the user can always see
which plugin snapshot the session is running.

The engine scripts are:

- **STATUS_CLI** — `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py`
  (all reads).
- **RENDER_CLI** — `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/render.py`
  (section 3's diagram rendering; reads stdin and writes stdout, never a file).

Run every verb from the repo root, so `--root` may be omitted — the same
convention `/s:duck`, `/s:fix`, and `/s:status` use.

## 1. Read the epic through the engine

Read the epic **exclusively** through the engine's mediated verbs. Never open a
spec-tree path directly, never `cat`/`grep` `<content-dir>/epics/<slug>/epic.md`,
and never reconstruct the epic from anything else you happen to know.

```
python3 STATUS_CLI cat epic <slug>
python3 STATUS_CLI epic-show <slug>
```

- **`cat epic <slug>`** prints the whole `epic.md` — its `## Introduction`
  (with `### Non-goals`), `## Decisions`, `## Design`, and the `## Changes`
  member table (one row per member change with its description and its
  Code / Integration / Unknowns / Risk ratings). This is the epic's *meaning*.
- **`epic-show <slug>`** prints the epic's live delivery state — status, theme,
  a `shipped <n>/<m>` count, and every member grouped into the UNPLANNED /
  READY / BUILDING / SHIPPED lanes with its per-member status and risk. This is
  where the epic *is* right now.

If `cat epic` exits non-zero, take the missing-epic path in section 4 instead —
do not fall back to reading files yourself.

Those two outputs are your entire evidence base. Read them fully before writing
a word: the explanation is a distillation of what they say, not a summary of
the slug's name plus inference.

## 2. Write the explanation

Print the explanation **as response text only**. It is a message, not a
document: write no file, emit no artifact, and do not offer to save it.

**The budget is under 100 lines of prose.** Fenced diagram blocks sit outside
the count — a diagram never spends the budget. And 100 is a **hard ceiling, not
a target**: a two-member epic with a short introduction gets a handful of
paragraphs and stops. Say what the epic means and end; padding a short epic up
toward the cap is a failure, not thoroughness.

Cover these four things, in this order:

1. **What the epic is and why it exists** — from `## Introduction` (and its
   `### Non-goals`, where they sharpen the boundary). State the problem the
   epic exists to solve, not just the solution it picked.
2. **The load-bearing decisions** — from `## Decisions`. Carry the ones the
   rest of the epic rests on, each with the reason it was made; skip the
   incidental ones. A decision the members would collapse without belongs
   here; a naming preference does not.
3. **How the members compose** — from `## Design` and the `## Changes` member
   table. Say what each member change contributes and how they fit together —
   what depends on what, what seam each one owns — rather than restating the
   table row by row.
4. **Where delivery stands now** — from `epic-show`: the epic's status, the
   `shipped <n>/<m>` progress, which members sit in which lane, and what is
   in flight or not yet planned.

Write it as prose with light headings, aimed at someone who has never opened
the epic. Prefer the epic's own vocabulary over your own paraphrase, so the
explanation and the artifact stay searchable by the same terms.

## 3. Diagram only where one carries structure

**A diagram is earned, never routine.** Include one only when the epic's
structure is genuinely faster to read as a picture than as prose:

- members ordered along a **dependency chain** — this one lands before those
  can start;
- a **pipeline** the epic's work flows through, stage by stage;
- **hand-offs between actors** — user, skill, engine, CI — where who-calls-whom
  is the point.

If the epic is a flat list of independent members with no ordering and no
hand-offs worth picturing, **include no diagram**. A decorative architecture
picture adds length without carrying meaning; omitting it is the better
answer.

Permitted forms, when a diagram is earned:

- **swimlane-style ASCII** in a fenced block, or
- a **mermaid** block.

One diagram, at most, per explanation — the single structure that is hardest to
say in words. Draw only relationships the epic's `## Design`, `## Decisions`, or
member table actually state; never invent an ordering the artifact does not
assert. Every node in the diagram is a member change, actor, or stage named in
those sections.

### Mermaid diagrams are delivered rendered

A reader sees your explanation as terminal text, where a mermaid block is
source code, not a picture. So when the earned diagram is mermaid, **render it
to characters and embed the rendering**, never the source.

**Write edges with spaced arrows — `A --> B`, never `A-->B`.** The renderer
reads an unspaced arrow as part of a node label and silently draws a single
label box instead of an edge, exiting `0` while doing it, so a tight arrow
costs you the diagram without an error to notice.

Pipe the fenced mermaid block — the fences included — through the render verb
and embed what comes back:

```
python3 RENDER_CLI output --plain -
```

It returns the same markdown with the ```` ```mermaid ```` fence replaced by a
```` ```text ```` block holding the drawn diagram. Embed that block in the
explanation in place of the mermaid source.

**Fall back to the mermaid fence** when the command exits non-zero, or when it
returns the block still fenced as ```` ```mermaid ```` — the renderer leaves a
diagram it cannot parse untouched rather than failing, and an unrendered fence
is still better than none.

This pipe reads stdin and writes stdout; it creates no file and edits nothing,
so the read-only contract at the top of this skill holds.

## 4. No slug, or a slug the engine cannot resolve

Two cases take this path:

- **No argument.** `/s:explain` was invoked bare — there is nothing to explain
  and no engine error to report.
- **An unresolvable slug.** `cat epic <slug>` exited non-zero, printing
  something like `Error: epic 'no-such-epic' not found; probed: <roots>`.

In both cases, **list the roster and stop**. Do not guess which epic was meant,
do not fuzzy-match the slug to a near neighbour, and do not explain anything.

1. **Report the engine's error verbatim, when there was one.** On the
   unresolvable-slug case, show the line `cat epic` printed. On the
   no-argument case there is no error — skip this step.
2. **List the available epic slugs through the engine's roster verb:**

   ```
   "${CLAUDE_PLUGIN_ROOT}/bin/shipd" list epics
   ```

   It prints one line per epic — slug, location (`root` or
   `worktree:<name>`), and status — spanning this invocation root *and* its
   worktrees, so an epic authored in another worktree appears in the roster
   exactly as `cat epic` resolves it. The verb is read-only, so the read-only
   contract holds.
3. **Print that roster** as the epics this invocation root can see. When the
   verb prints `no epics`, say that no epics are installed here.
4. **Stop.** On the no-argument case, ask the user to pick one of the listed
   slugs and run `/s:explain <slug>`. On the unresolvable-slug case, stop after
   the error and the roster.

Do **not** use the bare `show` board as the roster: a selected change preempts
it, so it is not a reliable list of epics. `shipd list epics` is. And never
assemble the roster yourself from the spec tree's directory names — the verb is
the only roster surface.
