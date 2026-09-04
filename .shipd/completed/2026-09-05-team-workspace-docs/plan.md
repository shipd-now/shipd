# team-workspace-docs
Status: verified

## Idea

Extend `docs/portable-workspaces.md` to cover team-shared workspace repos:
several engineers cloning one workspace, the concurrency expectations on its
shared knowledge surfaces, and the minimal footprint a headless consumer needs
to read a workspace.

### Motivation

The portable-workspaces guide frames multi-machine use as one engineer moving
between their own machines (§3–§4), while the engine's local-only scoped
auto-commits and network-free read verbs already support team sharing and
headless reading — behavior that is verified in the specs but documented
nowhere user-facing.

### Details

- Append two sections to `docs/portable-workspaces.md`: `## 8. Sharing a
  workspace with a team` (multi-engineer cloning, per-machine members, git as
  the knowledge transport, concurrency expectations) and `## 9. Headless
  consumers` (what a bot/CI reader needs).
- Add one cross-reference note in §3 pointing team readers at §8.
- Affected capability: `shipd-workspace` (ADDED — the doc has no owning
  requirement yet). Impact: `docs/portable-workspaces.md` only; nothing under
  `plugins/s/`, so no plugin version bump.

### Non-goals

- No engine changes: no locking, no merge machinery, no push automation, no
  new verbs — the doc describes what exists.
- No restructuring of §1–§7 beyond the single §3 cross-reference note.
- No changes to other docs or the README catalog.

## Implementation

- **Append, don't restructure.** New content lands as §8 and §9 after the
  existing §7, keeping §1–§7 anchors stable. Rejected: reworking §3–§4 into a
  team-first narrative — churns published anchors for no added coverage.
- **The delta adds a `portable-workspaces-doc` requirement to
  `shipd-workspace`.** Precedent: a doc's requirement lives in its owning
  feature capability (`oracle-user-docs` in `shipd-ask`, change
  `2026-09-04-oracle-docs-advisory`). The requirement pins the doc's existence
  plus the three new coverage areas; the legacy sections are not exhaustively
  restated, keeping the delta lean.
- **Every doc claim is grounded in verified behavior**, cited by requirement
  id so the writer paraphrases rather than invents: local-only scoped
  auto-commits that never push/pull/fetch (`shipd-wiki` `wiki-autocommit`),
  unique `q-<slug>` queue blocks where duplicates invalidate the queue
  (`shipd-wiki` `wiki-question-queue`), per-machine materialization with
  drift reported never repaired (`shipd-workspace`
  `workspace-clone-sync-flows`), and git-free upward discovery
  (`shipd-workspace` `workspace-root-discovery`).
- **Headless claims are runnable-premise verified**, not sourced from code
  reading: against a bare workspace (config + wiki store, no members, no
  git), `workspace-show` exits 0 marking members `(absent) [url]`,
  `cat wiki <slug>` exits 0, `workspace-sync` prints the plan without
  touching the network, and `wiki-queue-add` outside git exits 0 printing
  `q-<slug>` with no commit attempted; a duplicate slug is refused with exit
  1. The doc's §9 asserts exactly these observed behaviors.
- **Concurrency expectations are stated as git facts, not protocol.** The doc
  tells teams: the engine takes no locks; conflict surfaces are `queue.md`
  (EOF appends collide) and `index.md` (catalog rewrites collide) while
  per-page files merge cleanly; a merge yielding two blocks with the same
  `q-<slug>` leaves the queue invalid until de-duplicated; pull before a
  session, push after it. Rejected: prescribing a branching model for the
  workspace repo — teams differ, and the engine is agnostic.
- **No diagram.** The doc's established style is plain-fence file trees; the
  new sections carry lists and one command sequence, no shape a diagram would
  earn.

Risk: doc drift from future engine behavior — mitigated by the delta's
scenarios phrasing the contract as doc-inspection checks tied to the cited
requirement ids, so a behavior change that invalidates the doc shows up as a
spec conflict.
