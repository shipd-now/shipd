# wiki-emit-autocommit
Status: verified
Epic: portable-workspaces

## Idea

Every successful wiki write through the engine — a staged `wiki` emission or
a `wiki-queue-add` append — makes a local git commit in the workspace repo
when the store sits inside a git work tree.

### Motivation

The portable-workspaces epic makes the workspace root a clonable git repo
whose wiki is the payload, but wiki writes today leave the working tree
dirty and unversioned, so knowledge history and cross-machine sync cannot
ride ordinary git push/pull.

### Details

- New `wiki_autocommit(store_dir, paths, subject)` helper in
  `spec_common.py`: a silent no-op outside a git work tree, otherwise a
  commit scoped to exactly the written files; a failed commit never fails
  the write.
- `spec_emit.py`'s `emit_wiki` commits the installed file set after the
  whole-store lint passes; `spec_status.py`'s `wiki-queue-add` commits
  `queue.md` after a valid append.

Affected capabilities: `shipd-wiki` (added requirement). Impact:
`plugins/s/skills/build/scripts/spec_common.py`, `spec_emit.py`,
`spec_status.py`, their tests, plugin version bump.

### Non-goals

- No push, pull, or fetch — networked git stays out of engine scripts
  (constitution); syncing remotes stays a session habit or a skill step.
- No auto-commit on `wiki-init` or any non-wiki emit mode — the epic
  decision covers wiki emit and queue-add only.
- No commit of anything beyond the files the write touched — unrelated
  staged or dirty state in the workspace repo is never swept in.

## Implementation

- **Helper in `spec_common.py`**, beside the existing local-git helpers:
  `wiki_autocommit(store_dir, paths, subject)` returning True only when a
  commit was made. Gate on the existing `_inside_git_work_tree(store_dir)`
  — not a work tree is the epic's silent no-op. Then probe
  `git -C <store_dir> status --porcelain -- <paths>`: empty output means
  the write changed no bytes, so skip the commit quietly. Otherwise
  `git add -- <paths>` followed by `git commit -m <subject> -- <paths>` —
  the pathspec on the commit scopes it to exactly the written files, so
  unrelated staged index state in the workspace repo is never swept in.
  Any git failure (missing identity, hook failure) prints one
  `warning: wiki auto-commit skipped: …` line to stderr and returns False
  — the write already succeeded and its exit code stays 0. Rejected:
  `git commit -a` or a whole-store `git add` — both sweep unrelated state
  into a commit the user never reviewed.
- **Call sites.** `emit_wiki` calls the helper only after the whole-store
  lint passes, passing the installed destination paths and the subject
  `shipd-wiki: emit <n> file(s)`. `cmd_wiki_queue_add` calls it after queue
  validation with `[queue_path]` and the subject
  `shipd-wiki: queue-add q-<slug>`. Failure paths (lint rollback, duplicate
  slug, invalid queue) never reach the helper, so a failed write never
  produces a commit.
- **Constitution fit.** Local-git subprocess in engine scripts is
  precedented (`_inside_git_work_tree`, `_git_probe`) and the epic
  explicitly permits local-only git in engine verbs; the helper runs only
  `status`, `add`, and `commit` — never the network.
- **Risk: absolute pathspecs.** Callers hold absolute destination paths;
  git accepts absolute pathspecs inside the work tree. Tests cover the
  nested-store layout (`<ws>/.shipd/wiki` committed in a repo rooted at
  `<ws>`) to pin this down.
