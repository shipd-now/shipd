<!-- description: Drive an approved epic's members to shipped pull requests unattended. -->
# /s:autopilot — drive an approved epic to shipped pull requests

Your job is thin: preflight one epic, confirm what the run may spend, launch
the driver in the foreground, and relay its report. You never plan, build,
gate, or review anything yourself, and you never answer a driven session's
question on the user's behalf — the driver owns every stage decision.

<!-- include:preamble -->

## 1. Preflight — read-only, drives nothing

Confirm the epic is approved with
`python3 "$S/spec_status.py" epic-show <epic>`. Only `ready` and `active`
epics can be driven: a missing epic, a `draft` one (which still needs
`epic-set-status ready`), or a `complete` one (which has nothing left) stops
the flow here, with nothing driven. That approval is the last human gate —
everything past it belongs to the driver.

Relay the roster `epic-show` printed. The run drives the members shown as
`unplanned`, in risk-ascending order, and reports every other state without
touching it. Then show the pipeline the run will honour with
`python3 "$S/spec_status.py" pipeline-show`, and print the exact member order
it will use, driving nothing:

```sh
python3 "$S/autopilot.py" <epic> --dry-run
```

## 2. Confirm the run controls

The run spends real model time and opens real pull requests, so confirm its
scope against the dry run's member list before launching:

| control | what it caps | default |
| --- | --- | --- |
| `--max-members N` | how many members this run drives | unlimited |
| `--timeout S` | per-session wall-clock budget, in seconds | 1800 |
| `--max-resumes R` | resumed turns a driven session may spend | 4 |

Offer three choices — deliver every member (the recommended default), deliver
one member first as a cautious trial (`--max-members 1`), or cancel and drive
nothing — and honour a typed override of any knob. On cancel, stop here.
<!-- if:question-dialogs -->
Put that choice in a single question dialog, in a turn that carries the dry
run's member list and no other load-bearing prose.
<!-- else -->
Put that choice to the user as a plain-text numbered list, with the dry run's
member list printed above it, and wait for a typed reply.
<!-- end -->

## 3. Run the driver in the foreground

```sh
python3 "$S/autopilot.py" <epic> [--max-members N] [--timeout S] [--max-resumes R]
```

Wait for it to finish — never background it. The driver creates a worktree per
member, walks the resolved pipeline for each in turn, opens an auto-merging
pull request per member, parks the members it cannot finish, and writes a JSON
report. It cannot see this session's model, so the pipeline's symbolic model
tiers resolve against an anchor the dry run prints as its `Model tier anchor:`
line; pass `--session-model <alias>` to anchor the stages on a weaker model.
<!-- if:subagents -->
Where the user would rather watch each stage than run headless, the same
pipeline can be driven inside this session instead: one worker per stage per
member, in the dry run's order, each stage graded by reading the repository
through its own CLIs rather than by trusting the worker's summary, and every
failure raised to the user instead of parking the member.
<!-- end -->

## 4. Relay the report

Relay the driver's report verbatim, then add the pointers a human acts on:

- **Shipped** members, each with its full pull request URL, never a number.
- **Parked as `rejected`** — the context gate found the plan insufficient and
  the driver's own enrichment attempt still did not clear it. Name the member
  and point at `/s:plan <member>`, run from the repository root: it locates the
  parked worktree and runs enrichment through to the re-gate, which is the only
  path back to `ready`.
- **Parked as needs-human** — print the exact command that reopens that
  member's session, one line per member, so a person can pick up the precise
  conversation.
- **Skipped** members with their state, and **unreached** members cut off by
  `--max-members`.

Then stop. This command edits no code, plans and builds nothing, and never
answers a driven session on the user's behalf. Shipped members need no
follow-up; a parked one resumes through `/s:plan` or `/s:build`.
<!-- if:file-references -->
The pipeline entry forms, the per-stage grading table, and the failure
contract are written out in {refs}/autopilot.md — read it before interpreting
a parked member.
<!-- else -->
The pipeline entry forms, the per-stage grading table, and the failure
contract are not available as a separate file here. Say so when a parked
member needs explaining, state that you would have read the autopilot
reference for that detail, and answer from the driver's own report — it names
the stage that stopped each member.
<!-- end -->
