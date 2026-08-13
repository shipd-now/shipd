# memory-git-backing
Status: verified
Epic: personal-memory
Theme: developer-experience

## Idea

Layer a git-backing flow onto `/s:preferences`: when a capture runs against a
personal store that is not a git repo, offer (typed-confirmed) to `git init` it,
optionally create and wire a personal `shipd-memory` remote via `gh`, and push; and
on a git-backed store with unpushed commits, offer a confirmed push — so the
user's memory is versioned and portable across machines.

### Motivation

The epic's whole portability promise — "a new machine is one `git clone` away
from the user's accumulated memory" — needs the personal store to be a git repo
with a remote, but nothing sets that up. The store engine already commits every
write locally through `wiki_autocommit` when the store is inside a git work tree;
this final member adds the one-time setup and the ongoing push that turn those
local commits into a synced, portable history.

### Details

- Add a git-backing flow to `plugins/s/skills/preferences/SKILL.md` that runs
  around the capture install:
  - **Detect** whether the personal store's git root — `<memory_dir>` (the
    parent of the `<memory_dir>/wiki` store) — is inside a git work tree.
  - **First run (not a git repo):** offer, in a typed round, to `git init
    <memory_dir>` before the emit (so the capture's `wiki_autocommit` commits the
    first page); then, when the user accepts and `gh` is available, offer to
    `gh repo create shipd-memory --private` and wire it as the `origin` remote;
    then offer a confirmed `git push -u origin <branch>`. When `gh` is absent or
    the user declines the remote, complete the local `git init` and print the
    manual remote-and-push commands.
  - **Already git-backed:** the capture autocommits locally as today; when an
    `origin` remote exists and there are unpushed commits, offer a confirmed
    `git push` so the remote stays in sync over time.
- Edit the SKILL.md line that currently says the skill "adds no git logic" to
  reflect the new flow.
- Document the config-as-convention note: the personal repo MAY also hold a copy
  of `~/.shipd-config.json`, but no engine reads or syncs settings.

Affected capabilities: `shipd-memory` (added — `git-backing-flow`). Impact:
`plugins/s/skills/preferences/SKILL.md`; plugin version bump to 0.6.25. No
engine or script changes — `wiki_autocommit` already does the local commit; all
`git`/`gh`/`push` beyond it is skill-driven. No new dependencies (`gh` is
optional and its absence is handled).

### Non-goals

- No engine change — the engine keeps its local-git-only contract
  (`status`/`add`/`commit` via `wiki_autocommit`); it never pushes, pulls, or
  fetches. Remote creation and pushing are skill-driven and always confirmed.
- No automatic or silent git action — every `init`, remote wiring, and push is a
  typed-confirmed step the user can decline.
- No AskUserQuestion — the flow's confirmations are typed rounds, so
  `/s:preferences` stays off the question-rejection-recovery roster.
- No config-sync feature — the config-as-convention note is documentation only;
  nothing reads, writes, or reconciles `~/.shipd-config.json`.
- No git flow on `/s:forget` or `/s:memory` — the epic layers this onto the
  capture path only; forget's removals autocommit locally once the repo exists.

## Implementation

- **The flow is skill-driven Bash, not an engine change.** `/s:preferences`
  runs `git`/`gh` directly (a skill may; the engine may not). The engine's
  `wiki_autocommit` still does the local commit on the emit write — this member
  only establishes the repo/remote and pushes. This is exactly the epic's split:
  "the engine never pushes … remote creation and pushing are skill-driven and
  always confirmed."

- **Git root is `<memory_dir>`, detected with `git -C <memory_dir> rev-parse
  --is-inside-work-tree`.** Initializing at `<memory_dir>` (the parent of the
  `<memory_dir>/wiki` store) means `wiki_autocommit`'s
  `_inside_git_work_tree(<memory_dir>/wiki)` check passes, so the capture's emit
  commits the first page automatically. Rejected: `git init` at
  `<memory_dir>/wiki` (would nest the repo below the intended root and split the
  memory tree from any co-located `~/.shipd-config.json`).

- **First-run ordering: init → emit (auto-commits) → remote → push.** Offer and
  run `git init` *before* the staged emit so the first captured page lands in the
  initial commit; then, after the capture, offer the remote wiring and push. On
  an already-git-backed store, skip init and — when `origin` exists with unpushed
  commits (`git rev-list @{u}..HEAD` is non-empty, or no upstream is set) — offer
  the confirmed push. Rejected: init after emit (the first page would sit
  uncommitted until the next write).

- **`gh` is optional; its absence degrades gracefully.** The remote step runs
  `gh repo create shipd-memory --private` (repo name `shipd-memory`, matching the
  default `~/.shipd-memory` store and the user's stated intent) and
  `git remote add origin <url>` only when `gh` is on `PATH`, authenticated, and
  the user accepts. Otherwise the skill completes the local `git init` and prints
  the exact manual commands (`gh repo create …` / `git remote add …` /
  `git push -u origin …`) for the user to run later. Pushing is always the user's
  confirmed choice — an outward-facing action is never automatic.

- **Confirmations are typed rounds.** Each offer (init, remote, push) is a
  plain-text prompt answered by a typed reply — no AskUserQuestion — preserving
  the `preferences-skill` contract that `/s:preferences` issues none and stays
  off the interaction roster.

- **Config-as-convention is a documented note, not behavior.** The SKILL.md
  states the personal repo may also hold `~/.shipd-config.json` (e.g. symlinked) so
  a `git clone` carries the user's build settings too, while making clear no
  engine reads or syncs it. This satisfies the epic's non-goal boundary
  (memory sync, not config sync) without adding config logic.

Risk: a push could fail (no auth, rejected non-fast-forward, network). The skill
treats a failed `gh`/`push` as non-fatal — it reports the failure and the manual
command, and the capture (already committed locally) still succeeds; the local
commit is the durable outcome and the remote is best-effort, mirroring
`wiki_autocommit`'s own never-fail-the-write stance.
