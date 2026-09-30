# onboard-workspaces-lesson
Status: verified

## Idea

Teach workspace configuration, including overlapping team workspaces, through an optional `/s:onboard workspaces` side-track.

### Motivation

Engineers on large teams cannot learn from the tour how a base workspace, nested team workspaces, and shared repos fit together. The tour stops at a single sandbox repo, and the workspace guides under `docs/` sit outside the guided path.

### Details

- Add a `workspaces` argument to `/s:onboard`. It runs a separate five-part lesson that never touches the nine-step state file.
- The lesson builds a throwaway `acme-base` workspace with three nested team workspaces (`myapp`, `billing`, `infra`) using the real `workspace-init`, `workspace-project`, `wiki-init`, and `workspace-show` verbs. It shows each result.
- The five parts: the manifest and the chain; nearest-wins reads with no registry merge; writes landing nearest; overlapping teams on shared repos (projects are systems, not teams); isolation through separate repos, with the `store_root` and sync pointers.
- Point the tour's step 9 and its closing offer at the side-track, and link `docs/workspaces.md` throughout.
- Affected capability: `shipd-onboard` (modified and added). Impact: `plugins/s/skills/onboard/SKILL.md`, the `README.md` and `docs/cheatsheet.md` onboard rows, and the plugin version bump.

### Non-goals

- No change to the nine steps, `state.json`, the tour sandbox, or the `add-board` example.
- No new engine verb, no template asset, and no change to workspace behavior or `docs/workspaces/`.
- No lesson on `store_root` internals beyond a pointer to the nesting guide.

## Implementation

- Keep the side-track inside `SKILL.md` as a section, beside the tour. That file is exempt from the content-directory notation test, and the skill stays one file. Rejected: a `references/` file, which would need the notation marker and a second load path.
- Build the sandbox live at `~/.shipd/onboarding/workspaces-sandbox/` by running engine verbs, with `HOME` unchanged and no file written outside that path. Each verb carries the sandbox root as cwd or target. Rejected: a shipped template tree, because the lesson's point is to watch the real verbs create the layout.
- Give the side-track its own state file `~/.shipd/onboarding/workspaces.json` as `{"part": <1-5>}`, driven by `/s:onboard workspaces`, `... next`, and `... back`. The tour's `state.json` is never read or written by it. Rejected: reusing `state.json`, which would corrupt tour resume.
- Re-entry is idempotent: when the sandbox already exists, the lesson reuses it and never re-runs `workspace-init`. `workspaces reset` deletes the sandbox and its state after the user asks.
- Teach overlap with facts the guides already state: a project registry is per manifest and never merged; a team declaring `projects` shadows the base's outright; two teams may each declare the same repo path; a wiki write lands in the nearest store; a question queued at the base is answerable only there; separate repos, not directories, are the isolation boundary.
- Verified premises (run in a scratch `HOME`): `workspace-init <base> --git` then `workspace-init <base>/<team> --nested --git` exit 0; `workspace-project add` in two teams for one path `api/core` exits 0 in both; `workspace-show` in a team with no `projects` prints `registry: <base>` and the base's projects; `wiki-show` in a team lists the base store in `chain:`; `wiki-init` in a team creates only the team's own store.
- Bump `plugins/s/.claude-plugin/plugin.json` from 0.6.241 to 0.6.242, per the repo's snapshot rule.

Risk: the lesson drifts from the workspace guides. Guard it by quoting behavior only from live verb output and linking the guides for detail.

## Questions and answers

### Q1: Where does the workspace lesson live?
- **Question:** Where should workspace-configuration teaching live relative to the fixed nine-step tour? Options: (A) an optional `/s:onboard workspaces` side-track with its own sandbox; (B) add steps 10 and beyond; (C) only a doc link in the tour. Recommendation: A.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option A, taken as the planner's recommendation because the oracle found no source and the session takes the recommended option when no human is available. The side-track leaves the fixed nine-step contract and the tour's state untouched.
- **Queued:** q-onboard-workspace-config-lesson-placement

## Readiness attestation

### Problem and motivation

Engineers on large teams get no guided path to workspace configuration or overlapping team workspaces.

Evidence:

- `plugins/s/skills/onboard/SKILL.md` covers nine steps over one sandbox repo and never mentions a workspace.
- `docs/workspaces/teams.md` and `docs/workspaces/multi-workspace-repos.md` carry the material, and the tour does not point at them.

### Scope and non-goals

The change adds one optional argument and lesson to the onboard skill and leaves the tour, engine, and guides unchanged.

Evidence:

- In scope: `plugins/s/skills/onboard/SKILL.md`, the README and cheatsheet onboard rows, `plugins/s/.claude-plugin/plugin.json`.
- Out of scope: engine scripts, `docs/workspaces/`, the sandbox assets.

### Affected capabilities and files

One capability, `shipd-onboard`, changes, in one skill file plus three small doc and manifest edits.

Evidence:

- Capability `shipd-onboard`: requirement `onboard-step-navigation` (base fdd6d557da91), from `spec_status.py base-hash`.
- Runnable premise: `spec_status.py workspace-init <base> --git`, then `workspace-init <base>/infra --nested --git` → exit 0; `workspace-show` in `infra` printed `registry: <base>` and the base's `shared` project.
- Runnable premise: `workspace-project add api api/core --url ...` in two sibling teams → exit 0 in both.
- Runnable premise: `wiki-init` inside `myapp` → created `myapp/.shipd/wiki`; `wiki-show` listed the base store under `chain:`.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- Side-track placement: Q1, taken as the recommended option.
- State file, sandbox path, and re-entry behavior: decided in Implementation.
