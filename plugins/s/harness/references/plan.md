# /s:plan — the readiness bar, the emission grammar, and enrichment

The long form the router points at. Read it when authoring artifacts, when the
readiness attestation is due, or when the context gate parks a change.

## The readiness bar

Four items, all of which must hold before you author anything.

1. **The problem is clear.** You can state what is wrong (or missing) today
   and what "fixed" looks like, in the repository's own terms.
2. **Scope and non-goals are bounded.** You can name at least one thing this
   change deliberately does *not* do.
3. **The affected capabilities and files are identified.** Named paths and
   capability slugs, not categories.
4. **No open decision would change the task list.** Every remaining unknown is
   an implementation detail the executor can settle from the spec.

**What you print.** One plain statement per item, in this order, as visible
text — `**<item name>** — <a sentence or two stating counts and reasons>` —
then a closing line `Full evidence: <absolute path to the change's plan.md>`.
Settle the change name before printing, so that path is the real destination.
Keep the terminal clean: no table, no citations, no command output. Internal
reasoning does not count; if it is not printed, it did not happen.

**Where the evidence goes.** `plan.md` carries a `## Readiness attestation`
section — one `###` subsection per item, named for the item, each opening with
the plain statement and then an `Evidence:` dash list citing capability names,
`file:line` references, and requirement ids. An item whose subsection carries
no evidence is unmet: go back to step 2 or step 4 rather than installing. The
linter does not check this section, so the self-review pass is what enforces
it. Write it in settled prose that carries none of the context gate's
placeholder markers — the gate scans it with the rest of the file.

**The runnable-premise rule.** Where the plan asserts how an existing command,
script, or flag behaves, and a task depends on that behaviour, *run it* before
emitting. Two individually reasonable decisions can be jointly broken, and only
running the command reveals it. The observation is evidence under the
affected-capabilities-and-files item, not a fifth item: name the invocation and
what it printed in that subsection's evidence, and summarize the premise in
plain language in the printed attestation.

## The emission grammar

Author into a staging directory, then install through
`spec_emit.py change <change> --from <staging-dir>`. Never write into the spec
tree directly and never construct its path yourself.

```
<staging-dir>/
  plan.md
  specs/<capability>/spec.md      one file per affected capability
  tasks.md
```

### plan.md

```
# <change-name>
Status: draft
Epic: <slug>            (only when the change belongs to an epic)

## Idea

### Motivation
Why this is being done, in the repository's terms.

### Details
What changes, and which capabilities and files it touches.

### Non-goals
What this change deliberately does not do.

## Implementation
The binding technical decisions — the ones the implementer must not
re-litigate. Rationale belongs here, where an executor with a clean context
can find it.

## Readiness attestation

### <checklist item name>
The plain statement you printed.

Evidence:

- <capability name, file:line, requirement id, or a premise's invocation and
  what running it showed>
```

The attestation section comes last, after every other section the plan
carries, and holds all four subsections in checklist order.

### specs/<capability>/spec.md

Deltas only — never the whole master. Each section is one of
`## ADDED Requirements`, `## MODIFIED Requirements`, `## REMOVED
Requirements`, or `## RENAMED Requirements`:

```
## ADDED Requirements

### Requirement: <one-line title>
id: <kebab-slug>

The system SHALL <the normative statement>.

#### Scenario: <short name>
- **WHEN** <the trigger>
- **THEN** <the observable outcome>
```

A `MODIFIED` requirement additionally carries a `base:` hash of the master
requirement it edits, so a master that has since moved is caught rather than
silently overwritten. Every requirement needs at least one scenario, and every
scenario must be refutable by exercising the real code.

### tasks.md

A flat markdown checklist. Each task names its files and its concrete change,
and is small enough to execute without architectural judgement — the judgement
lives in `plan.md`'s `## Implementation`.

```
## 1. <group title>

- [ ] 1.1 [req: <requirement-id>] <the concrete change, naming its files>
- [ ] 1.2 [P2] [req: <requirement-id>] <an independent task>
```

`[P<n>]` tags mark mutually independent tasks: tasks sharing a number may run
concurrently, groups run in ascending order, and an **untagged** task is a
sequential barrier. When in doubt, leave a task untagged. The `[req: …]` tag
is traceability metadata naming the delta requirement the task satisfies (or a
lone `[req: *]` for a whole-change task); it is never an instruction.

## Enrichment — recovering a rejected change

The context gate exits 2 by writing a `## Context insufficient` section into
the installed `plan.md` and parking the change at `rejected`. Each dot-point
in that section is one finding to resolve, and enrichment edits the installed
artifacts **in place** — it never re-emits through staging.

- **Resolve everything the repository can answer, without asking.** A stale
  `base:` hash is re-read from the current master and reconciled. A dangling
  task path is corrected to where the file really is. A placeholder (`TBD`,
  `???`, an undecided name) is replaced with a decision grounded in the
  repository's existing patterns.
- **Put only the true gaps to the user** — an undecided product choice the
  repository genuinely cannot settle. Fold the answers back into the
  artifacts.
- **Exit only through the gate.** Re-run `spec_gate.py <change>`: exit 0
  strips the section and promotes the change to `ready`; exit 2 rewrites a new
  section, which becomes the next agenda. Never leave `rejected` with
  `set-status` or `--force`.
