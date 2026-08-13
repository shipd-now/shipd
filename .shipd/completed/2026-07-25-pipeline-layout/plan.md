# pipeline-layout
Status: verified

## Idea

The spec library's directory names don't tell the pipeline story: `am/spec/`
nests a `specs/` (truth), `changes/` (in-flight), and `changes/archive/`
(applied) whose names say nothing about the lifecycle. This change flattens and
renames the tree so browsing it reads as the pipeline itself, with `verified`
as the terminal stage:

```
am/
  README.md            # grammar authority (was am/spec/README.md)
  constitution.md      # steering rules (was am/spec/constitution.md)
  planned/             # in-flight changes (was am/spec/changes/)
    <change>/
  completed/           # applied changes (was am/spec/changes/archive/)
    <date>-<change>/
  verified/            # master library — distilled truth (was am/spec/specs/)
    <capability>/spec.md
```

The five statuses (`draft`, `ready`, `active`, `complete`, `verified`) are
unchanged and stay in the `plan.md` header — a change rides them inside
`planned/`, moves to `completed/` at merge, and its truth lands in `verified/`.

Affected capabilities (all modified): `shipd-spec-format`, `shipd-plan`,
`build-context-gate`, `build-spec-lifecycle`, `build-task-coordination`,
`project-readme`, `statusline`. Impact: every path-bearing file — the four
engine scripts, `claim_task.sh`, `statusline.sh`, all tests and fixture trees,
the three SKILL.mds, plan references, subagent prompt, root `README.md`,
`AGENTS.md`, and the moved `am/README.md`/`am/constitution.md` texts. After the
build, refresh the plugin snapshot (`claude plugin update s@shipd`).

## Implementation

- **Pure rename/flatten; no behavior change.** Every tool keeps its semantics;
  only resolved paths change. `git mv` preserves history. Archived change
  *contents* are untouched (the immutability rule constrains content, not the
  container's location).
- **`completed/` is a sibling, not a nested `archive/`.** `planned/` therefore
  contains only live changes: `statusline.sh` drops its `! -name archive`
  exclusion and `spec_status.py use` validates simply "directory exists under
  `am/planned/`". The `<date>-<change>` prefix in `completed/` stays.
- **The flip is one atomic barrier task.** Task 1.1 performs all `git mv`
  operations (archive out of `changes/` *first*, then `changes` → `planned`)
  **and** repaths `claim_task.sh` in the same task. The claim happens under old
  paths, the completion under new ones — the script resolves paths per
  invocation and its claim-time lock is released within the claim call, so this
  is safe. Until the statusline task lands, the statusline is silent (it sees
  no `am/spec/changes/`) — accepted cosmetic gap.
- **Delta specs describe the target state** (new paths); they merge into
  `am/verified/` at build end via the already-repathed engine — the same
  self-hosting pattern the OpenSpec cutover used.
- **`.shipd/state.json` is untouched** — it stores the change *name* only.
- Constitution honored: engine scripts stay stdlib-only, `statusline.sh` stays
  bash-3.2-safe, every engine/statusline edit ships with its updated tests.
- Rejected: per-status physical directories (4 moves per build, every resolver
  becomes status-aware, mid-build moves race the coordinator) and a generated
  symlink view (machinery for state the header + statusline already show).
