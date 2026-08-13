## ADDED Requirements

### Requirement: Git-backing flow
id: git-backing-flow

`/s:preferences` SHALL run a git-backing flow around the capture install,
driven by the skill (not the engine) and confirmed in typed rounds (no
AskUserQuestion). It SHALL detect whether the personal store's git root
`<memory_dir>` (the parent of the `<memory_dir>/wiki` store) is inside a git work
tree. When it is not, the skill SHALL offer to `git init <memory_dir>` before the
staged emit — so the capture's `wiki_autocommit` includes the first page — and,
only on the user's confirmation and where `gh` is available and authenticated,
SHALL offer to create and wire a private `shipd-memory` remote (`gh repo create
shipd-memory --private` plus `git remote add origin`) and then offer a confirmed
`git push`; where `gh` is absent or the user declines the remote, the skill SHALL
complete the local `git init` and print the manual remote-and-push commands.
When the store is already a git repo with an `origin` remote and unpushed
commits, the skill SHALL offer a confirmed `git push`. The engine SHALL NOT push,
pull, or fetch — all remote and push actions are skill-driven and always
confirmed, and a failed `gh` or `git push` SHALL be non-fatal (reported, with the
local commit remaining the durable outcome). The personal repo MAY also hold a
copy of `~/.shipd-config.json` as a documented user convention, but no engine reads
or syncs settings.

#### Scenario: First-run offers git init before the commit
- **GIVEN** a capture against a personal store whose `<memory_dir>` is not a git
  work tree
- **WHEN** the user accepts the offered `git init`
- **THEN** the skill initializes the repo at `<memory_dir>` before the staged
  emit, so the captured page lands in a commit via `wiki_autocommit`

#### Scenario: Remote wiring and push are confirmed and gh-gated
- **WHEN** the first-run flow reaches the remote step with `gh` available
- **THEN** it offers `gh repo create shipd-memory --private` and `git remote add
  origin` and a subsequent `git push` only on the user's typed confirmation

#### Scenario: gh absent degrades to local init
- **WHEN** `gh` is not available or the user declines the remote
- **THEN** the skill completes the local `git init` and prints the manual
  remote-and-push commands, and the capture still succeeds

#### Scenario: Ongoing push offered when out of sync
- **GIVEN** a git-backed personal store with an `origin` remote and unpushed
  commits
- **WHEN** a later capture completes
- **THEN** the skill offers a confirmed `git push`

#### Scenario: Engine never pushes
- **WHEN** `plugins/s/skills/preferences/SKILL.md` and the flow are inspected
- **THEN** every `git push` / `gh` action is skill-driven and typed-confirmed,
  the engine's role stays the local `wiki_autocommit` commit, and a failed push
  is non-fatal

#### Scenario: Flow uses no AskUserQuestion
- **WHEN** the git-backing flow prompts for init, remote, or push
- **THEN** each prompt is a typed plain-text round and the skill issues no
  AskUserQuestion, keeping `/s:preferences` off the question-rejection-recovery
  roster
