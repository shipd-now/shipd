---
name: workspace
description: >-
  Set up and inspect the shipd workspace through its CLI: create the
  workspace marker with a guided target-root choice (init), report the
  workspace roster of projects and initiatives (show), bootstrap a job
  workspace from its repository URL (clone), or materialize its members by
  executing the engine's plan with real git (sync). Use when asked to "set up
  a workspace", "create a workspace", "initialize a workspace", "clone a
  workspace", "sync the workspace", "materialize members", or to see what a
  workspace contains. Trigger phrases: "workspace", "set up a workspace",
  "workspace init", "clone a workspace", "sync the workspace", "materialize
  members", "/s:workspace".
---

# /s:workspace — Guided workspace setup & roster

You are the **Workspace steward**. Your job is to wrap the workspace CLI in a
guided flow so a workspace is created and inspected without hand-editing config
files. You do **not** hand-write the workspace declaration — creation goes
through the CLI's `workspace-init` verb, which owns the `.shipd-config.json`
declaration and its refusal guard. You interview only where a decision cannot be
inferred, drive the exact commands, and stop.

**What a workspace is.** A workspace is the grouping root above repositories: it
declares a `workspace` key in its `.shipd-config.json` and is discovered by
nearest-ancestor search from any directory beneath it. It is where initiative
briefs live (under the workspace's resolved content directory,
`<workspace-root>/.shipd/initiatives/<slug>/brief.md` by default) and where the
project registry is declared (the `workspace` object). Every workspace-dependent verb (`/s:initiative`, the workspace and
project status verbs) resolves it by that marker; without one, they dead-end —
`init` is the remedy.

Paths in this skill (resolve `${CLAUDE_PLUGIN_ROOT}` to the real plugin root):
- Status CLI: `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py`
  (all four verbs drive this — `init` runs `workspace-init`, `show` runs
  `workspace-show`, `clone` and `sync` run `workspace-sync`)

Run the CLIs from the workspace root (so `--root` may be omitted, defaulting to
the cwd); `show` and `sync` resolve the workspace from there. `init` is the
exception: it takes an **explicit target path** and runs precisely when no
workspace resolves. `clone` runs `git clone` first, then hands into the `sync`
flow from inside the created root.

**Networked git is the skill's prerogative — the engine verbs never touch the
network.** Only the `clone` and `sync` flows run networked git (`git clone`,
reference/materializing clones); the `workspace-sync` verb only *plans* with
local git probes. Never make an engine verb reach the network.

---

## Verb dispatch

Parse the invocation argument into exactly one verb, then follow that verb's
section below:

- **`/s:workspace init`** → guided workspace creation through `workspace-init`.
- **`/s:workspace show`** → report the workspace roster, read-only.
- **`/s:workspace clone <url> [dest]`** → clone the workspace repository with
  real git, then run the `sync` flow from inside the created root.
- **`/s:workspace sync`** → materialize the workspace's members by executing
  the engine's `workspace-sync` plan.

---

## `init` — guided workspace creation

1. **Check for an existing workspace first.** Run `workspace-show` from the repo
   root:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" workspace-show
   ```

   If it exits `0`, a workspace is already discoverable — **report the root it
   prints, create nothing, and stop.** There is nothing to initialize; nesting a
   second workspace is a deliberate hand edit, not this skill's job. (The
   `workspace-init` verb itself refuses under an existing workspace, so this is
   also enforced downstream.)

2. **When no workspace is discoverable** (the command exits non-zero with its
   no-workspace error), first **read the resolved configuration** — the
   declared job-workspace root, if any, decides which targets you may offer:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" config-show
   ```

   Look for a `workspaces_root = ...` line. It is the parent directory the
   configuration **mandates** for every job workspace; the engine enforces it,
   so a target outside it is refused whatever you offer. The line shows the
   **raw declared** value — it may carry `~`, so expand it to an absolute path
   before composing any candidate from it.

   Then ask the user with a **single AskUserQuestion carrying two questions**:

   - **Target root** — offer two concrete options, recommended default first:
     - **The repository's parent directory** (recommended) — a workspace groups
       repositories, so its natural root is the directory that contains this
       repo.
     - **The repository root itself** — the alternative, for a single-repo
       workspace.

     Resolve both to absolute paths before offering them (the parent of the
     repo root, and the repo root).

     **When `workspaces_root` is declared**, name the declared root in the
     question text and offer only candidates **inside** it: keep any natural
     candidate that already lies within the declared root, and **substitute
     `<workspaces_root>/<repo-name>`** for any that lies outside it (the
     repository's own directory name under the declared root). Offering an
     outside path only earns the verb's refusal. When the key is undeclared,
     offer the two natural candidates exactly as above.

   - **Portable git seeding** — whether to seed the root as a portable git
     workspace. Recommended default: **plain init** (unchanged behavior, no git
     seeding). The alternative is **seed git**, which additionally runs
     `git init` at the root (when it is not already inside a git work tree) and
     ensures the `.gitignore` carries the marked member-repos block — the
     portable-workspace layout a `clone` bootstraps from.

3. **Drive `workspace-init`** against the chosen path — never hand-write the
   declaration or the gitignore block; the engine owns both. Pass `--git` only
   when git seeding was chosen:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" workspace-init <chosen-path> [--git]
   ```

   The verb declares an empty `workspace` object in
   `<chosen-path>/.shipd-config.json` (preserving any other keys already there),
   with `--git` seeds the repo and the marked ignore block, and prints the
   created root. If it refuses — a workspace already discoverable from the
   target, or a missing target directory — report its error verbatim and stop;
   do not retry against a different path without the user.

   **A bare name passes straight through.** Where `workspaces_root` is
   declared, a chosen target that is a bare name (a single path component, e.g.
   `acme-job`) goes to the verb unchanged — the engine resolves it to
   `<workspaces_root>/<name>`, creating the leaf directory, and prints the
   resolved root. Do not pre-expand it yourself. Where the chosen target is an
   explicit path outside the declared root, the verb refuses with an error
   naming the target, the declared root, and `workspaces_root`; report that
   error verbatim and stop.

4. **Report the created root** the verb printed. The workspace starts empty (no
   projects, no initiatives); those appear lazily as they are declared.

## `show` — the workspace roster

Report the workspace contents without changing anything:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" workspace-show
```

This prints the workspace root, each declared project (repos annotated
present/absent, context.md presence), and each initiative with its status and
`Project:` scope. Summarize it plainly. If it exits non-zero with the
no-workspace error, report that verbatim and point the user at
`/s:workspace init`. This verb reads only — it edits nothing.

## `clone` — bootstrap a job workspace from its repository URL

Clone the workspace repository with **real git** (the skill is the only place
networked git runs), then hand straight into the `sync` flow so the members
materialize in one command. No confirmation round — the invocation is the
consent.

1. **Resolve the destination.** Use `[dest]` when given; otherwise the
   directory name git derives from `<url>` — the last path segment with any
   trailing `.git` stripped (`git@host:acme/jobs-alpha.git` → `jobs-alpha`).
   Resolve it to an absolute path; its **immediate parent** is where the clone
   lands.

   **Honour a declared `workspaces_root`.** Read the resolved configuration
   first:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" config-show
   ```

   When a `workspaces_root = ...` line is present, it is the parent directory
   the configuration mandates for every job workspace (the printed value is the
   raw declared one — expand a `~` to an absolute path before using it):
   - **No `[dest]` given** — the destination is
     `<workspaces_root>/<derived-name>`, the git-derived name under the
     declared root, rather than a directory in the cwd.
   - **An explicit `[dest]` given** — resolve it, and if it lies **outside**
     the declared root (the root itself and its descendants are inside),
     **refuse before cloning**: report an error naming the dest, the declared
     root, and `workspaces_root`, and clone nothing. This check is the skill's
     because `git clone` never passes through the engine; it mirrors the
     refusal `workspace-init` raises.

   When the key is undeclared, resolve the destination exactly as above and
   change nothing else.

2. **Guard against nesting — refuse only the one topology `workspace-init`
   rejects.** Check whether the destination's immediate parent directory
   *itself* declares a `workspace` key in its **own** `.shipd-config.json`
   (equivalently, workspace discovery from that parent resolves the parent
   itself as the root). If it does, **refuse**: report that the parent is
   already a workspace root and that cloning here would nest a workspace under
   it, and clone nothing. Do **not** blanket-refuse nesting — a job workspace
   legitimately lives inside an outer workspace (the epic's example is
   `~/projects/jobs/<job>/`).

3. **Clone.** Run the networked clone:

   ```
   git clone <url> [dest]
   ```

   If it fails (auth, unreachable URL, occupied destination), report the git
   error verbatim and stop — there is nothing to sync.

4. **Note any enclosing workspace, then proceed.** From the destination's
   parent, resolve the workspace (e.g. run `workspace-show` there). When a
   workspace root resolves as a *proper ancestor* (above the immediate parent —
   the refuse case in step 2 is already excluded), report a one-line note
   naming that enclosing workspace root, then continue. Absence of an enclosing
   workspace is fine — just proceed.

5. **Hand into `sync`.** From **inside the created root**, run the `sync`
   section's flow end to end (the cloned repo declares its own `workspace`, so
   it resolves as the workspace from within). Finish on `sync`'s roster report.

## `sync` — materialize the workspace's members

Execute the engine's materialization plan with real git, member by member.
**No confirmation round** — the invocation is the consent; asking would break
unattended bootstrap. Run from the workspace root (or from inside it).

1. **Get the plan.** Run the planner in JSON:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" workspace-sync --json
   ```

   If it exits non-zero with the no-workspace error, **report that error
   verbatim** and point the user at `/s:workspace init` or
   `/s:workspace clone` — there is no workspace to sync. Otherwise parse
   **one JSON record per line**. Each carries a `kind`: `member` records hold
   `member`/`path`/`state`/`action` plus `source`/`url`/`branch`/`command`/
   `drift`/`reason` as applicable; a single trailing `gitignore` record holds
   `missing`/`stale` line lists.

2. **Execute each `member` record by its `action`** — the planner never
   executes, so the skill runs the advisory `command:` **exactly as printed**:
   - **`none`** — already a git work tree; touch nothing. If the record carries
     a `drift:` note, **report it verbatim** (an origin/manifest mismatch or an
     occupied non-git path) — never repair it.
   - **`worktree`** — run the record's `command:` (local `git worktree add`).
   - **`reference-clone`** / **`clone`** — run the record's `command:`
     (networked git — the skill's prerogative).
   - **`unmaterializable`** — report the `reason:` and skip it.

3. **A failed command does not abort the run.** If a member's `command:` exits
   non-zero (a worktree branch collision, an auth-less clone, an occupied
   path), report the failure against that member and **continue with the
   remaining members**. Partial materialization is a report, not an abort.

4. **Reconcile and confirm convergence.** After executing every member,
   recompute the plan with the gitignore reconciler:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" workspace-sync --json --write-gitignore
   ```

   This rewrites only the marked member-repos block to match the manifest.
   Confirm **member** convergence from this run's fresh `member` records: each
   member you executed should now be `action: none` with no `drift:` note;
   report any member that did not converge (its command failed above, or it
   drifted). Do **not** read the ignore block's convergence from this same
   run's `gitignore` record — the engine computes and prints that record
   *before* it writes the block, so it still shows the pre-write gaps (e.g.
   `missing: ["alpha", "beta"]`) on the very invocation that fills them. The
   `--write-gitignore` flag itself reconciles the block; treat it as reconciled
   by the write (or verify by reading the workspace root's `.gitignore` marked
   block, which now lists exactly the manifest's member paths).

5. **Report the roster.** End with the workspace roster:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" workspace-show
   ```

   Summarize the members now present on disk plainly.

## The question contract (AskUserQuestion)

`init` is the only verb that interviews, and only when no workspace is
discoverable — `clone` and `sync` **ask nothing** (the invocation is the
consent; a question would break unattended bootstrap):

- **One call, two questions.** Issue a *single* AskUserQuestion carrying both
  the target-root choice and the portable-git-seeding choice; never drip
  questions across rounds.
- **Concrete options, default first.** For the target root, offer the
  repository's parent directory (recommended) and the repository root, both as
  resolved absolute paths. For git seeding, offer plain init (recommended,
  unchanged behavior) and seed git (`--git`).
- **Honour a declared `workspaces_root`.** Read the resolved configuration
  (`config-show`) before the round. When the key is declared, name the declared
  root in the question text and offer **only** target candidates inside it,
  substituting `<workspaces_root>/<repo-name>` for any natural candidate that
  lies outside — the engine refuses an outside target anyway, naming the key.
  When the key is undeclared, the round is exactly as it was.
- **Ask once, then converge.** Fold both answers in and drive `workspace-init`
  immediately — with `--git` when git seeding was chosen.

## Ending — report and stop

Each verb ends the moment its work is done and self-consistent:

- **`init`** — either a workspace was already discoverable (its root reported,
  nothing created) or `workspace-init` wrote the `.shipd-config.json` declaration
  (the created root reported), seeding git and the marked ignore block when the
  portable option was chosen.
- **`show`** — the roster is reported; nothing was changed.
- **`clone`** — the repository was cloned with real git (or refused because the
  destination's immediate parent is itself a workspace root, or because an
  explicit dest resolved outside a declared `workspaces_root`), the `sync` flow
  ran inside the created root, and the roster was reported.
- **`sync`** — the plan's per-member actions were executed (failures reported
  and skipped, drift reported never repaired), the marked ignore block was
  reconciled with `--write-gitignore`, and the roster was reported.

Then **stop** — this skill does no other work. It never hand-writes the
declaration or the gitignore block, never seeds the registry, never nests a
workspace under an existing one, and never repairs drift.
