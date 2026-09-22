# workspace-team-setup
Status: verified
Theme: developer-experience

## Idea

Make the nested base-workspace layout the one blessed way teams share a
workspace repo, and add an interactive wizard that builds it.

### Motivation

The guide documents two competing multi-workspace shapes, so a team has no
blessed answer; and the guided front door cannot build the nested shape at
all, because `/s:workspace init` stops whenever a workspace is discoverable.

### Details

- Add an engine writer for the workspace registry's `projects` map, the
  missing piece that makes post-setup member mapping possible.
- Add an interactive team wizard: it names teams, creates their folders,
  initializes each as a nested workspace, declares their repos, and closes
  with a mapping round for checkouts the engineer already has.
- Expose the wizard on the `shipd` binary as `shipd workspace team`, and
  mirror its steps in the `/s:workspace` skill.
- Rewrite the guide so team use shows only the nested shape, leaving two
  documented setup paths: a standalone workspace, and a base plus nested
  team workspaces.

Affected capabilities: `shipd-workspace` (modified), `shipd-cli` (modified).
Impact: `plugins/s/skills/build/scripts/spec_status.py`, a new
`plugins/s/skills/build/scripts/workspace_tui.py`, `plugins/s/bin/shipd`,
`plugins/s/skills/workspace/SKILL.md`, `docs/workspaces.md`,
`docs/workspaces/teams.md`, `docs/workspaces/multi-workspace-repos.md`,
`docs/workspaces/getting-started.md`, and tests. No new dependencies.

### Non-goals

- No change to `/s:workspace init`'s refuse-to-nest branch — the wizard is a
  separate verb, never a new branch of `init`.
- No networked git. The wizard clones nothing; materializing members stays
  `shipd workspace sync`'s job.
- No engine refusal of the sibling shape. It stops being documented, it does
  not stop working.
- No access-control mechanism. Separate repos remain the isolation boundary.

## Implementation

- **`workspace-project` verb** (`spec_status.py`) writes the registry's
  `projects` map: bare lists, `add <project> <path> [--url U] [--branch B]`
  appends a repo entry, `remove <project> [--repo <path>]` drops a repo or the
  whole project. It validates the resulting registry through the existing
  `validate_workspace_registry` **before** writing, so an ambiguous repo path
  or a malformed project name refuses and writes nothing. Rejected:
  hand-editing the manifest from the wizard — every other workspace file the
  engine owns has a writer verb, and `workspace-map set` already refuses a
  member path the registry does not declare.
- **`workspace_tui.py`** carries the wizard in `install_tui.py`'s three
  layers, so all but the terminal layer is testable without a tty: a pure
  reducer over typed answers producing an ordered action plan; pure file
  surfaces that execute one planned action each; and the terminal loop with a
  numbered line-prompt fallback and headless degradation that prints a note
  and writes nothing. Rejected: a `textual` screen — the constitution holds
  every engine script but the named display surfaces to the stdlib.
- **Team names are validated as project names.** The wizard holds each typed
  name to `PROJECT_NAME_RE`, the pattern the registry already enforces, so a
  name is always a safe directory component and always legal as a project.
- **The wizard runs local-only verbs.** Per team it calls the existing
  `cmd_workspace_init(..., nested=True, git=True)`, then the new project
  writer, then `cmd_workspace_map` for each checkout the user points at.
  Nothing reaches the network, preserving the engine's no-network rule.
- **`shipd workspace team`** joins `init` and `sync` as a consumed mode word
  in the binary's workspace mapping, and the binary's docstring gains it as a
  tenth declared write exception.
- **Docs**: `teams.md` and `multi-workspace-repos.md` both sit at the 150-line
  how-to cap, so the sibling-shape removal pays for the nested-shape material
  rather than adding to it.
- Risk: the wizard's terminal layer cannot run in CI. Guarded by the layer
  split — the reducer, the writers, and the headless degradation are all
  covered by the stdlib suite, and only the raw prompt loop is untested.

## Questions and answers

### Q1: What happens to the sibling shape in the guide?
- **Question:** The guide documents two multi-workspace shapes — siblings in a
  plain container repo, and a base workspace holding nested job workspaces.
  With the nested shape becoming the blessed team pattern, does the sibling
  shape stay documented? Options: (a) remove it entirely; (b) keep it scoped
  to solo use; (c) keep both with the comparison. Recommendation: (a).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Remove the sibling shape from the guide entirely. Two
  team-shaped answers make the blessed path ambiguous, and the inherited base
  wiki is what multi-team use actually needs. The guide then presents exactly
  two setup paths: a standalone workspace, and a base plus nested team
  workspaces.
- **Queued:** q-docs-blessed-workspace-shape-alternatives

### Q2: Does the guided init gain a nested path?
- **Question:** `/s:workspace init` stops whenever a workspace is
  discoverable, so it cannot build the nested team layout. Should it gain a
  nested branch? Options: (a) yes, amend the init branch; (b) no, document a
  manual command; (c) a separate explicit verb. Recommendation: (a).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option (c). Leave the refuse-to-nest branch alone and add a
  separate interactive team verb on the `shipd` binary, with the
  `/s:workspace` skill mirroring its steps. The wizard names teams, creates
  their folders, initializes each nested workspace, and ends with a mapping
  round so an engineer who already has the repos checked out gets running
  without re-cloning.
- **Queued:** q-workspace-init-guided-nested-branch

### Q3: What test level covers the setup?
- **Question:** What level of test covers the nested team layout and
  simulates usage across it? Options: (a) a stdlib unittest driving the real
  CLI, plus a docs drift guard; (b) the behavior test alone; (c) additionally
  an LLM eval case. Recommendation: (a).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option (a). A stdlib `unittest` module under
  `plugins/s/skills/build/tests/` that builds the layout and drives the real
  verbs end to end, plus a docs drift guard — a doc convention is real only
  when a test can refuse its violation. An eval case has no standing position
  behind it. The suite must be reachable from CI; placing it in the existing
  engine tests directory satisfies that, since `ci.yml` already discovers it.
- **Cited:** wiki/prompt-convention-enforcement, queue
  q-evals-tests-framework-and-ci-wiring

## Readiness attestation

### Problem and motivation

The guide blesses no single team shape, and the guided front door cannot
build the nested one.

Evidence:

- `docs/workspaces/multi-workspace-repos.md` documents both shapes and
  compares their trade-offs, leaving no blessed team answer.
- `plugins/s/skills/workspace/SKILL.md` `init` step 1 stops on a discoverable
  workspace and never passes `--nested`.

### Scope and non-goals

The change touches the registry writer, the wizard, the binary dispatch, the
workspace skill, the guide, and tests. The sibling shape keeps working, and
no networked git is added.

Evidence:

- In scope: `spec_status.py`, `workspace_tui.py` (new), `plugins/s/bin/shipd`,
  `plugins/s/skills/workspace/SKILL.md`, the four guide pages, the tests.
- Out of scope: `workspace-sync`'s materialization ladder is unchanged.

### Affected capabilities and files

Two capabilities carry the change: `shipd-workspace` holds the verb semantics
and the doc contracts, `shipd-cli` holds the binary's mode mapping.

Evidence:

- Capability `shipd-workspace`: `workspaces-doc` (base 0e0cf9e7688e),
  `workspaces-doc-examples` (base 36cf72f2c986), `workspace-setup-skill`
  (base 701e4cf11f71), hashes from `spec_status.py base-hash`.
- Capability `shipd-cli`: `cli-dispatch` lists the workspace mode words.
- Runnable premise: building the layout with
  `spec_status.py workspace-init <base> --git` then
  `workspace-init <base>/<team> --nested --git` exited 0, and the bare verb
  refused to nest with exit 1.
- Runnable premise: `spec_status.py --root <nested> wiki-queue-answer
  base-question` exited 1 with `queue has no block`, while the same call at
  the base exited 0 — the queue write target is the nearest store.
- Runnable premise: `workspace-show` from a nested workspace declaring its own
  `projects` printed only its own; from one declaring none it printed the
  base's under a `registry:` provenance line.
- Runnable premise: `docs_lint.py` over the guide exits 0 today, with
  `teams.md` and `multi-workspace-repos.md` each at 150 lines against the
  150-line how-to cap.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- Sibling-shape removal: settled by the user, Q1.
- A separate team verb rather than an init branch: settled by the user, Q2.
- Test level and placement: settled by the oracle, Q3.
