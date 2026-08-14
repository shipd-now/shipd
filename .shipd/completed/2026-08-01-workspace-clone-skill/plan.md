# workspace-clone-skill
Status: verified
Epic: portable-workspaces

## Idea

Give the `/s:workspace` skill the execution half of portable workspaces:
`clone` and `sync` flows that run the engine's materialization plan with
real git and report the roster, plus init exposure of the engine's `--git`
seeding.

### Motivation

The engine can now plan a job workspace's materialization (`workspace-sync`)
but nothing executes it — cloning a workspace repo and materializing its
members means hand-run git, and the skill cannot even create a git-ready
root because `workspace-init --git` is unreachable through it.

### Details

- `/s:workspace` gains `clone <url> [dest]` (clone the workspace repo with
  real git, then run the sync flow inside it) and `sync` (execute the
  plan's per-member actions, reconcile the gitignore block, report the
  roster).
- The skill is the only place networked git runs — the engine verbs it
  drives stay network-free (epic decision; constitution).
- The init flow additionally offers git seeding, passing
  `workspace-init --git` (oracle-settled: the skill half of the flag was an
  unowned gap left by `workspace-repo-manifest`).

Affected capabilities: `shipd-workspace` (modified + added requirements).
Impact: `plugins/s/skills/workspace/SKILL.md`, plugin version. No engine
code changes — `workspace-sync --json`, `--write-gitignore`, and
`workspace-show` already provide everything the flows drive.

### Non-goals

- No engine changes: planning stays in `workspace-sync`; the skill never
  re-derives the materialization ladder.
- No drift repair: mismatched origins and occupied paths are reported,
  never modified — the planner's posture is upheld at execution.
- No push/pull automation beyond the materializing clones themselves;
  keeping members fresh stays a session habit (epic non-goal).
- No eval-harness case: the evals grader asserts a planned change produced
  by `/s:plan`, so it cannot grade this skill; verification is a scripted
  scenario run over local path URLs.

## Implementation

- **`clone <url> [dest]` flow.** Run `git clone <url> [dest]` (dest
  defaulting to git's derived directory name), then continue with the sync
  flow from inside the created root and end on the roster report. When a
  workspace root resolves from the destination's parent, proceed and report
  a one-line note naming the enclosing workspace — nearest-ancestor
  discovery makes the nested job workspace resolve correctly from within,
  and the epic's own example lives at `~/projects/jobs/<job>/`. Refuse only
  when the destination's immediate parent directory itself declares
  `workspace` in its own `.shipd-config.json` — the topology
  `workspace-init`'s guard rejects (oracle-settled). Rejected: a blanket
  refuse-to-nest — it would make the epic's worked example an error.
- **`sync` flow.** From the workspace root: run `workspace-sync --json`,
  parse one record per line, and execute per action — `none`: report,
  surfacing any `drift:` note verbatim and touching nothing; `worktree`:
  run the record's advisory `command:` (local git); `reference-clone` and
  `clone`: run the `command:` (networked git — the skill's prerogative);
  `unmaterializable`: report the `reason:` and skip. A failed command is
  reported against its member and the run continues — partial
  materialization is a report, not an abort. Afterwards re-run
  `workspace-sync --json --write-gitignore` to reconcile the marked member
  block and confirm convergence (each executed member now `none` without
  drift), then report the roster via `workspace-show`. No confirmation
  round: the epic's success criterion is "`git clone` + one sync command";
  the invocation is the consent. Rejected: a pre-execution
  AskUserQuestion — it breaks unattended bootstrap.
- **Init `--git` exposure.** The init interview stays one AskUserQuestion
  call, now carrying two questions: the existing target-root choice and
  whether to seed the root as a portable git workspace (recommended
  default: plain init, unchanged behavior). Seeding maps to
  `workspace-init <path> --git`; the skill still never hand-writes the
  declaration or the gitignore block — the engine owns both.
- **Skill contract updates.** Frontmatter description and trigger phrases
  grow clone/sync; the verb dispatch, question contract, and Ending
  sections cover all four verbs.
- **Version.** Bump `plugins/s/.claude-plugin/plugin.json` to the next
  free patch above remote main.
- **Risks.** Advisory-command failures (worktree branch collision,
  auth-less clone) surface at execution; the per-member continue-and-report
  posture bounds them. Parsing drift between skill and verb is bounded by
  the speced `--json` record shape (`kind`/`member`/`path`/`state`/
  `action`/…).
