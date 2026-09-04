# cross-universe-reads
Status: verified

## Idea

Route every read-side spec/epic lookup — `cat`, `related`, and a kind-aware
`shipd list` — through the engine's existing cross-worktree/cross-universe
resolution seam, so read surfaces can never disagree about which artifacts
exist.

### Motivation

`cat epic` and `related` resolve the invocation root only, while `epic-show`,
`locate`, and the board resolve across `.worktrees/*` and declared workspace
project repos — reproduced live, `cat epic demo-epic` exits 1 while
`epic-show demo-epic` prints the same epic from its hosting worktree. So a
session can be told an epic does not exist by one verb and shown it by the
next, and `/s:explain`'s fallback roster inherits the blindness.

### Details

- Resolve `cat change|verified|epic|research|video` across the universes the
  shared seam yields (`sc.aggregation_universes` × the root-then-worktrees
  candidate walk), root candidates first; not-found errors name the probed
  roots, `locate`-style. `cat initiative` and `cat wiki` keep their
  workspace-chain resolution unchanged.
- Span `related`'s corpus over the invocation root's own universe (root plus
  its `.worktrees/*`), deduped by `(kind, slug)` root-first.
- Extend `shipd list` with an optional kind word —
  `changes` (default) | `epics` | `verified` | `research` | `video` — spanning
  workspace universes at a workspace-level invocation, and scoping to the
  named root's own universe when `--root` is passed explicitly.
- Switch `/s:explain`'s missing-epic roster from a raw directory listing to
  `shipd list epics`.
- Bump the plugin version to 0.6.176.

Affected capabilities: `spec-io`, `spec-status`, `shipd-cli`, `shipd-explain`
(all modified). Impact: `plugins/s/skills/build/scripts/spec_status.py`,
`plugins/s/bin/shipd`, `plugins/s/skills/explain/SKILL.md`,
`plugins/s/.claude-plugin/plugin.json`; no new dependencies.

### Non-goals

- No change to any mutating verb: `spec_emit.py`, `set-status`, `epic-sync`,
  `epic-set-status` keep resolving the invocation root alone, so nothing ever
  writes into another checkout.
- No change to `cat initiative` / `cat wiki` resolution, the board, or
  `locate` — they already resolve correctly.
- No new engine script and no public "resolve this path" verb for skills:
  skills keep obtaining content (`cat`), rosters (`shipd list`), and point
  lookups (`locate`) — paths stay an engine implementation detail.

## Implementation

- **The seam stays in `spec_status.py`, not `spec_common.py`.** The walk
  already lives there (`_epic_candidate_roots`, `_epic_hosting_root`,
  `_epic_hosting_universe`) and `dashboard.py` and `bin/shipd` already import
  `spec_status`. Rename `_epic_candidate_roots` to public `candidate_roots`
  (it is no longer epic-specific); keep `_epic_hosting_root` /
  `_epic_hosting_universe` as-is. Rejected: promoting into `spec_common` —
  churn with no consumer that needs it there.
- **`cmd_cat` resolves through a shared probe walk.** A helper iterates
  `sc.aggregation_universes(root)` and, within each universe,
  `candidate_roots(universe_root)`, returning the first candidate whose
  content directory holds the kind's artifact — `epics/<slug>/epic.md`,
  `_readable_change_dir(candidate, slug)` (planned then completed, per
  candidate), `verified/<slug>/spec.md`, `research/<slug>/report.md`,
  `video/<slug>/brief.md`. On a miss the error lists the probed candidate
  roots. Separator relpaths are computed against the invocation root, falling
  back to the absolute path outside it (the `_related_path` convention).
- **Read precedence is root-first everywhere in `cat`/`related`/`list`
  non-change kinds**, matching `locate`'s invocation-root-first ordering and
  `all_epic_slugs_with_roots`. The one exception stays: `shipd list`'s
  `changes` kind keeps its spec'd worktree-wins dedup (`cli-list`) — for an
  in-flight change the worktree copy is the live one.
- **`related` spans the invocation universe only** (root + its worktrees),
  never declared project repos: `/s:fix` debugs the repo it runs in, and
  workspace-level knowledge is already the wiki surface `related` searches.
  Dedup by `(kind, slug)`, first seen (root-first) wins.
- **`shipd list [kind]`**: row discovery moves into a public
  `spec_status.list_rows(root, kind, span_workspace)` returning
  `{name, location, project, status}` dicts — `changes` reuses the existing
  planned/completed logic, `epics` pairs `all_epic_slugs_with_roots` per
  universe with `read_epic_status` on the hosting root, `verified` /
  `research` / `video` list slug directories per candidate with status `None`.
  `bin/shipd`'s `cmd_list` keeps parsing and rendering (text status `-` for
  `None`; a foreign universe's location renders `<project>:<location>`; JSON
  rows gain a `project` key, `null` in the own universe) and drops its private
  `_probes`/`_planned_rows`/`_archived_rows`/`_collect` duplicates. Rejected:
  keeping discovery in the binary — it would re-implement the seam privately,
  which is the defect class this change removes.
- **Scoping**: `--root` given explicitly ⇒ `span_workspace=False` (list what's
  there: that root and its worktrees). Default (cwd) ⇒ spanning, which
  `sc.aggregation_universes` already collapses to the single own universe for
  any invocation inside a member repo, so non-workspace behavior — including
  the bare `shipd list` text output — is byte-identical. `--all` stays
  meaningful for `changes` only; any other kind combined with `--all` exits
  non-zero with an error.
- **`/s:explain` fallback** runs
  `"${CLAUDE_PLUGIN_ROOT}/bin/shipd" list epics` for the roster (still
  read-only, now engine-mediated and worktree-aware) and drops the
  "an epic in another worktree is invisible" caveat, which `cat epic`'s fix
  makes false.
- **Risks**: byte-compat of the bare `shipd list` text/JSON — guarded by the
  existing `test_shipd_cli` list tests staying green unmodified; extra stat
  cost of the candidate walk is bounded by the same single-level
  `.worktrees` listing `locate` already pays.
