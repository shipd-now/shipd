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
in its own git worktree: the plugin's `plugins/s/bin/shipd worktree <change>`
creates `.worktrees/<change>` on branch `change/<change>` and then runs any
`post-worktree-scripts` the layered config declares, so a fresh checkout
arrives already set up. That verb is the create path's front door — it drives
the git mechanics through `worktree.sh` and adds the hook step; a failing hook
exits `3` with the worktree left in place, resumable with
`shipd worktree hooks run` from inside it. Register the scripts through
`shipd worktree hooks add` (or `/s:worktree-hooks`), never by hand-editing
`.shipd-config.json`. The whole shipd lifecycle
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
`plugins/s/skills/build/scripts/worktree.sh sweep [--dry-run]` reclaims a
merged worktree and its branch together — everything `remove` plus
`prune-branches` would, run across every worktree at once, reporting an
unmerged one on a `stale:` line rather than touching it — and the engine's
`shipd worktree` create path already runs it automatically after every create
unless the layered config declares `worktree_sweep` false, so an abandoned
`pr-mode: draft` worktree or one orphaned by a crashed build session is
usually reclaimed on its own by the next `worktree` invocation.

**Epic status derivations** (`epic-sync`/`epic-set-status`) on a merged epic
run in a fresh `epic-close-<slug>` worktree — created with
`shipd worktree epic-close-<slug> --fresh`, so the derivation never adopts a stale
close-out branch — and ship as a PR, never from the main checkout, whose
uncommitted epic-file edit a protected-main workflow cannot ship.

**Amending a live epic** follows the same shape, and is never a free edit of
the epic file: run `/s:epic <slug> amend`, which works in a fresh
`epic-amend-<slug>` worktree (`shipd worktree epic-amend-<slug> --fresh`),
changes only `## Decisions` and the shelf sections (`## References`,
`## Research`, `## Video`) with every new or extended Decision carrying a dated
`*(amended YYYY-MM-DD: <note>)*` stamp, and — with the epic tracked in this
repo — ships as a PR. Two gates run before the push: the linter's single-epic
mode and
`plugins/s/skills/build/scripts/spec_status.py epic-amend-check <slug>`, which
exits `4` naming every protected region — the header metadata,
`## Introduction`, `## Design`, `## Changes`, the token breakdown — that the
amendment changed against `main`. Where the repo's configuration resolves the
epic into an external store (`store_root`), there is no worktree, branch, or
PR: the flow edits the epic in the store's working tree and runs both gates
against that uncommitted edit, with `--root` still naming the consuming repo.
It then ships one local commit in the store scoped to the epic file alone,
subject `shipd: amend epic <slug>`, never pushed. A draft epic is not amended
at all; it is edited in its authoring worktree.

**Documentation under `docs/` is authored and revised through `/s:document`.**
That skill carries the shipd documentation standard — the one canonical rules
file, `plugins/s/skills/document/references/standard.md` — and the stdlib-only
lint that enforces its mechanical rules. Write a new doc or revise an existing
one through the skill, and fix every lint finding before the change ships.
Never hand-write `docs/` prose against a private idea of the house style.

**Conventions live here (or in the specs), never only in an assistant's private
memory** — a durable rule is checked into this file or the spec library so
every session inherits it.

### Spec layout and lifecycle

Specs live in `.shipd/` (master library in `verified/`, in-flight changes in
`planned/`, applied changes in `completed/`) — the content directory is
configurable via `.shipd-config.json` (the `dir` key, default `.shipd`), resolved
by layered upward search. The engine is the plugin's own scripts under
`plugins/s/skills/build/scripts/`. Use `/s:duck` to talk an idea through with
the adversarial rubber-duck critic before planning it, `/s:prd` to interview
for and install a workspace PRD — the discover phase, `/s:plan` to
spec work, `/s:build` to execute it, `/s:fix` to debug a reported problem
against the spec library and fix it, `/s:review` for a semantic review of
local changes before pushing, `/s:drive` to drive a real browser against a
running app and verify a change with a `PASS`/`FAIL` verdict (optionally
recording a branded demo video), `/s:gate` to set up that review as a
repository's merge gate (and `/s:gate update` to refresh an already-gated
repository's managed files to the running plugin version),
`/s:status` for lifecycle status,
`/s:epic` to decompose features, `/s:explain` to read a shipd epic and explain
it in under 100 lines plus at-most-necessary diagrams, `/s:document` to author
and revise `docs/` documentation against the shipd documentation standard,
`/s:research` to produce
a cited research report an epic can link, `/s:workspace` to set up and inspect the
workspace, `/s:initiative` to run workspace initiatives, `/s:ask` to
query the oracle before interrupting the user, `/s:teach` to
distill spec artifacts and answered queue entries into the workspace wiki,
`/s:remember` to capture the user's durable preferences into the personal
memory store, `/s:memory` to list the captured memories, `/s:forget` to
remove a captured memory from the personal store, `/s:worktree-hooks` to author
and register the `post-worktree-scripts` a fresh worktree runs, and `/s:doctor`
to run the read-only `shipd doctor` preflight and then run the remedies the
user consents to.

### The engine's one third-party dependency

The spec engine is stdlib-only Python 3 (`.shipd/constitution.md`), with one
scoped exception, pinned in the repo-root `requirements.txt`:

- **`textual` — the engine's display surfaces.**
  `plugins/s/skills/build/scripts/dashboard.py`'s `tui` verb renders the board
  as a `textual` application, and `render.py`'s `screen` mode is a `textual`
  viewer whose styled `output` mode prints through the `rich` that ships as a
  `textual` dependency. Run `pip install -r requirements.txt` before using
  `dashboard.py tui`, `render.py screen`, or the styled `render.py output`, or
  before running the display test suite,
  `plugins/s/skills/build/tests_textual/`. `render.py` keeps those imports
  inside its display code paths, so importing it needs nothing installed;
  `dashboard.py` imports `textual` at module scope behind its script-entry
  bootstrap, as it always has.

The mermaid renderer behind `render.py` is **vendored, not a dependency**:
`plugins/s/skills/build/scripts/beautiful_mermaid.py` is a checked-in,
stdlib-only copy of the MIT-licensed upstream, pinned to the reviewed snapshot
its provenance header names. Nothing installs it, and `render.py`'s
substitution function is importable with no third-party package present at all.

Every other engine script, including the rest of `dashboard.py` and the
delivery engine `autopilot.py` depends on (via the stdlib-only
`heartbeat.py`), stays dependency-free — `plugins/s/skills/build/tests/` never
installs `textual` and always passes without it. Declared-pipeline validation
(`pipeline_schema.py`) is likewise stdlib-only, imported lazily by
`spec_common.resolve_pipeline` only to keep the two modules free of an import
cycle, not for any dependency it carries.

## Evals

`evals/run.py` is a local harness that drives the `s` plugin's LLM-facing
skills as real headless Claude Code sessions and grades the result. Run
`python3 evals/run.py` for every discovered case, or `python3 evals/run.py
--case <name>` for one; add `--runs N` to repeat a case and `--keep-scratch`
to retain each run's scratch directory for inspection instead of deleting it.
The harness's own unit tests live under `evals/tests/` — stdlib `unittest`,
no third-party dependency — run via
`python3 -m unittest discover -s evals/tests` (wired into `ci.yml`).

Each case is a directory under `evals/cases/<name>/` holding a `prompt.md`
(the request sent to the headless session) and a `fixture/` (the minimal repo
tree copied into a scratch git repo before the session runs). An optional
`evals/cases/<name>/expect.json` selects the **grader** via a `grader` key:

- Absent, or present without a `grader` key: **structural** (the default).
  Grades the scratch repo against `spec_lint.py` and a few structural
  assertions — one change directory, lint-clean, `Status: ready`. The three
  `/s:plan` cases use this.
- `{"grader": "behavior"}`: **behavior**. Grades whether the produced
  software actually works. After the session ends, the runner restores the
  case's shipped `fixture/tests/` tree over the scratch copy — reverting any
  session edit to a shipped test — copies in the case's held-out `verify/`
  tree, and runs `python3 -m unittest discover -s tests` in the scratch root;
  the run passes only on exit 0.
- `{"grader": "handoff", "handoff_requirement": "<id>"}`: **handoff**. Grades
  a case whose *correct* outcome is that no code changes — the documented
  behavior itself is wrong, so the right move is to name the problem and stop
  rather than patch the code or the spec. A run passes only when all four
  hold: every file under the scratch `src/` matches the fixture's; every file
  under the scratch content directory (`.shipd/`) matches the fixture's; the
  shipped suite still exits 0; and the session's final result text (read from
  the scratch transcript — the highest-numbered
  `eval-transcript-turn<N>.json` if any resume ran, else
  `eval-transcript.json`) contains the requirement id `handoff_requirement`
  names. The `handoff_requirement` key is required — an `expect.json`
  declaring `"handoff"` without it fails every run immediately, naming the
  case and the missing key, spawning no session.

**The oracle is held out of the fixture.** A behavior case's regression test
lives at `evals/cases/<name>/verify/`, outside `fixture/`, so the session
under test never sees it and cannot read, weaken, or delete it before
grading. Before each behavior run, the harness sanity-checks the fixture
itself: the shipped suite must exit 0 before the session runs, and must exit
non-zero once `verify/` is copied in — a mis-seeded fixture (the seeded bug
absent, or the held-out test already passing) fails the run immediately,
naming which check failed, without spawning a session. A handoff case is
sanity-checked the same way minus the second probe: the shipped suite must
exit 0 before the session runs, since the code is expected to implement its
documented contract faithfully — there is no held-out oracle to flip, because
the correct outcome leaves the code untouched.

`evals/cases/fix-report-drift/` is the worked example: its `fixture/` ships
a `.shipd/verified/report-output/` capability documenting a row sort order
its `src/report.py` doesn't implement, plus a green `tests/test_report.py`
that only checks the header and column padding; its held-out
`verify/test_report_order.py` asserts the documented order; and `prompt.md`
invokes `/s:fix` on the symptom (rows print in the wrong order) without
naming the sorting rule or the file to edit.

`evals/cases/fix-spec-wrong/` is the handoff grader's worked example: its
`.shipd/verified/report-output/` capability's `report-column-width`
requirement fixes the name column at a width of six characters, its
`src/report.py` implements that width exactly (`"%-6s  %3d  %s"`), and one
`ROWS` entry carries a name longer than six characters, so the printed table
visibly misaligns for that row even though the code faithfully matches its
documented contract — the shipped `tests/test_report.py` only asserts the
rows that fit the width, so it stays green regardless of what a session
does. `prompt.md` invokes `/s:fix` on the symptom (the columns don't line up
for some rows) without naming the requirement, the width, or the file to
edit. The positive signal the grader looks for is the requirement id
(`report-column-width`) in the session's own words, never the skill's
vocabulary (e.g. `/s:plan`) — a bare agent that correctly diagnosed the
contract and a `/s:fix` session that did the same both name the requirement
they read, whichever arm they ran in, so asserting a skill-specific term
would penalize the baseline arm for not knowing it rather than measuring the
outcome under test.

**`--arm {treatment,baseline,both}` (default `treatment`) runs a no-skill
baseline as an A/B.** `treatment` is today's behavior — every session loads
the plugin via `--plugin-dir`. `baseline` runs the same fixture, content
directory, permission mode, timeout, resume cap, and grader, but drops
`--plugin-dir` so the session sees no plugin at all — a controlled
experiment varies one thing. `both` runs `--runs N` of each arm and reports
the two pass rates together, one labelled row per arm per case.

The baseline run's prompt is **derived, never authored**: the harness strips
the leading `/s:<skill>` token from the case's own `prompt.md` and sends the
remainder verbatim, so both arms receive identical wording. A hand-authored
sibling prompt file would make prompt parity a matter of trust — thin
phrasing flattering the skill, a full brief flattering the baseline —
deriving it from the one prompt file makes parity structural instead.

The harness refuses a `baseline`/`both` arm on two cases, before assembling
any scratch repo or spawning a session, naming the case in both messages:

- A **structural**-graded case — structural grading asserts a change
  directory, a clean `spec_lint.py`, and `Status: ready`, artifacts only the
  plugin's skills produce, so a baseline arm would fail by construction and
  the comparison would be theatre.
- A `prompt.md` whose first line carries no `/s:<skill>` token — nothing to
  derive a baseline prompt from.

**The exit code gates on the treatment arm alone.** A failing baseline run is
the expected, informative outcome of a working comparison, not a harness
regression, so its pass rate is reported and never affects the exit code.
