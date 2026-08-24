# Working in this repo

## The plugin cache snapshot — edits are not live

This repo is both the **source** of the `s` plugin (`plugins/s/`) and a
consumer of it. The plugin is installed at **user scope** from a local
marketplace registration:

- Marketplace `shipd` → registered in `~/.claude/plugins/known_marketplaces.json`
  as a `directory` source pointing at this repo's root (the marketplace manifest
  is `.claude-plugin/marketplace.json`).
- Plugin `s@shipd` → installed as a **cached snapshot** under
  `~/.claude/plugins/cache/shipd/s/<version>/`. Claude Code runs the
  `/s:*` skills and commands **from that snapshot, not from the repo**.

Consequences:

- **Every change touching `plugins/s/` bumps the plugin version** in
  `plugins/s/.claude-plugin/plugin.json`, in the same PR. The cache snapshot
  is keyed by version, so without a bump `claude plugin update` is a no-op and
  sessions keep running the stale skills. Plans for such changes include the
  bump as a task.
- **After editing anything under `plugins/s/`, refresh the snapshot** or you
  will keep running stale skills:
  ```
  claude plugin update s@shipd
  ```
  (or press `u` on the plugin in the `/plugin` UI). Then start a new session —
  skills load at session start.
- The statusline is the exception: `.claude/settings.json` invokes
  `plugins/s/integrations/statusline.sh` straight from the repo, so statusline
  edits are live immediately.
- The `extraKnownMarketplaces` / `enabledPlugins` entries in
  `.claude/settings.json` are redundant for this machine (the user-scope
  install wins) and are kept only so other checkouts can self-advertise the
  plugin. Note they are trust-gated: they do nothing until the folder's trust
  dialog has been accepted.
- Do not recreate `.claude/skills/` symlinks into `plugins/s/skills/` — that
  was the pre-plugin loading mechanism and it shadows the `/s:` namespace with
  un-namespaced duplicates.

## Workflow

**One change = one worktree = one branch = one PR.** Every change is developed
in its own git worktree: the plugin's
`plugins/s/skills/build/scripts/worktree.sh <change>` creates
`.worktrees/<change>` on branch `change/<change>`. The whole shipd lifecycle
(`/s:plan` → `/s:build`, including the `spec_merge.py` merge/archive) runs
inside that worktree, so the change's artifacts and implementation travel in a
single PR. The main checkout is only for launching sessions, reviewing, and
post-merge pulls.

**Ship via PR, never direct push.** When a change is verified and merged/
archived on its branch, ship it:

```
git push -u origin change/<change>
gh pr create --fill
gh pr merge --auto --squash --delete-branch
```

Auto-merge waits on **both** required checks — `ci` and `semantic-review` — and,
because `main` now requires conversation resolution, on **zero unresolved
review threads**. So after `gh pr create` post the semantic-review gate to the
PR and disposition its findings: run the `/s:review` post flow against the PR
(review `change/<change>` vs `main`, then `review_gate.py post`, the poster at
`plugins/s/skills/review/scripts/review_gate.py`), which sets the
`semantic-review` commit status the merge waits on. Then run the disposition
loop over every posted finding — implement it (edit, commit, push, re-post) when
the suggestion is correct, otherwise `review_gate.py reply` on its thread with
the concrete reason — and finish with `review_gate.py resolve`, which resolves
the gate threads and reports `unresolved=0`. Re-post the review after any new
push, since a new commit invalidates the status. Branch protection blocks direct
pushes to `main` — including yours. Never commit or push to `main` directly.
Always report a PR with its full clickable URL, never just the number.

**After merge**, from the main checkout: remove the worktree through the
guarded verb — `plugins/s/skills/build/scripts/worktree.sh remove <change>`,
never raw `git worktree remove` — then pull `main`, and refresh the plugin
snapshot (`claude plugin update s@shipd`) when `plugins/s/` changed. The
`remove` verb refuses (exit 2, listing every reason) while the worktree still
shows work in progress, so a session can't prune a worktree another is using;
pass `--force` only once you have confirmed the refusal is spurious. A squash
merge deletes only the *remote* branch, so reclaim the local `change/*`
branches whose content already landed with
`plugins/s/skills/build/scripts/worktree.sh prune-branches`, which deletes
merged ones (squash merges included) and lists everything it keeps.

**Epic status derivations** (`epic-sync`/`epic-set-status`) on a merged epic
run in a fresh `epic-close-<slug>` worktree — created with
`worktree.sh epic-close-<slug> --fresh`, so the derivation never adopts a stale
close-out branch — and ship as a PR, never from the main checkout, whose
uncommitted epic-file edit a protected-main workflow cannot ship.

**Conventions live here (or in the specs), never only in an assistant's private
memory** — a durable rule is checked into this file or the spec library so
every session inherits it.

### Spec layout and lifecycle

Specs live in `.shipd/` (master library in `verified/`, in-flight changes in
`planned/`, applied changes in `completed/`) — the content directory is
configurable via `.shipd-config.json` (the `dir` key, default `.shipd`), resolved
by layered upward search. The engine is the plugin's own scripts under
`plugins/s/skills/build/scripts/`. Use `/s:plan` to
spec work, `/s:build` to execute it, `/s:fix` to debug a reported problem
against the spec library and fix it, `/s:review` for a semantic review of
local changes before pushing, `/s:gate` to set up that review as a
repository's merge gate (and `/s:gate update` to refresh an already-gated
repository's managed files to the running plugin version),
`/s:status` for lifecycle status,
`/s:epic` to decompose features, `/s:research` to produce a cited research
report an epic can link, `/s:workspace` to set up and inspect the
workspace, `/s:initiative` to run workspace initiatives, `/s:ask` to
query the ask-mikk oracle before interrupting the user, `/s:teach` to
distill spec artifacts and answered queue entries into the workspace wiki,
`/s:remember` to capture the user's durable preferences into the personal
memory store, `/s:memory` to list the captured memories, `/s:forget` to
remove a captured memory from the personal store, and `/s:doctor` to run the
read-only `shipd doctor` preflight and then run the remedies the user consents
to.

### The engine's two third-party dependencies

The spec engine is stdlib-only Python 3 (`.shipd/constitution.md`), with two
scoped exceptions, both pinned in the repo-root `requirements.txt`:

- **`textual` — the delivery board's `tui`.**
  `plugins/s/skills/build/scripts/dashboard.py`'s `tui` verb renders the board
  as a `textual` application. Run `pip install -r requirements.txt` before
  using `dashboard.py tui` or running its test suite,
  `plugins/s/skills/build/tests_textual/`.
- **`pydantic` — declared-pipeline validation.** Only the pipeline-declaration
  validation path may import it, and only lazily; nothing else in the engine
  does. `plugins/s/bin/shipd doctor` reports a `warn pydantic` line when it is
  not importable — the probe uses `importlib.util.find_spec`, so the binary
  itself stays stdlib-only — and `/s:doctor` offers the consent-gated install.

Every other engine script, including the rest of `dashboard.py` and the
delivery engine `autopilot.py` depends on (via the stdlib-only
`heartbeat.py`), stays dependency-free — `plugins/s/skills/build/tests/` never
installs `textual` or `pydantic` and always passes without them.
