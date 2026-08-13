# mikk-wiki-store
Status: verified
Epic: mikk-knowledge

## Idea

Add the mikk-knowledge epic's foundation: a lint-gated, Karpathy-grammar
knowledge store at the workspace root, with engine verbs to scaffold, read,
queue into, and write it.

### Motivation

The epic's ask-mikk oracle and teach-mikk intake need a central store to read
from and write to, and nothing like it exists — durable context today is
scattered across epic Decisions, research reports, and per-project context
files.

### Details

- New store layout at `<ws-root>/<content-dir>/wiki/`: `schema.md`,
  `index.md`, `log.md`, `queue.md`, `sources/`, `wiki/` pages.
- `spec_common.py` gains wiki path helpers and grammar parse helpers.
- `spec_lint.py` gains a `--wiki` mode; `spec_status.py` gains `wiki-init`,
  `wiki-show`, `wiki-queue-add`, and a `wiki` cat kind; `spec_emit.py` gains a
  staged `wiki` write verb.

Affected capabilities: `shipd-wiki` (new), `shipd-spec-lint`, `spec-status`,
`spec-io` (modified). Impact: the four engine scripts plus their tests under
`plugins/s/skills/build/tests/`, `.shipd/README.md`, and the plugin version.

### Non-goals

- No skills, agents, or model-driven behavior — ask-mikk/teach-mikk are later
  epic members; this is engine-only.
- No concurrent-writer coordination (page leases, cross-machine sync) — out of
  scope per the epic.
- No search beyond grep/index reading — no embeddings, databases, or network.
- No CI wiring — the store lives outside any repo; lint runs on demand and
  inside every wiki emit.

## Implementation

- **Location and discovery.** `wiki_dir(ws_root)` returns
  `specs_dir(ws_root)/wiki` beside `initiatives_dir`/`projects_dir` in
  `spec_common.py`; every wiki verb resolves the workspace via
  `find_workspace_root` and errors with the existing no-workspace message
  pattern when none is discoverable. Rejected: a repo-local store — the epic
  binds one central cross-repo wiki.
- **Grammar (binding, enforced by lint).** Pages are `wiki/<slug>.md`, kebab
  slugs; `index`, `log`, `queue`, `schema`, `sources` are reserved and invalid
  as page slugs. `[[slug]]` wikilinks in `wiki/` pages and `index.md` must
  resolve to an existing page; fenced code blocks are skipped (reuse the
  research linter's fence handling). Index entries are lines matching
  `- [[slug]] — <summary>`; non-matching lines are ignored; entry set and page
  set must match exactly (bidirectional coverage). `log.md` level-2 headers
  must match `## [YYYY-MM-DD] <op> | <subject>`. `queue.md` holds `## q-<slug>`
  blocks (kebab, unique) each carrying the five `- <Field>:` lines `Asked`,
  `Question`, `Options`, `Recommendation`, `Answer` (presence, non-empty;
  `Answer: pending` until answered).
- **Scaffold.** `wiki-init` creates the layout, seeding `schema.md` with the
  grammar conventions, an empty `index.md` and `queue.md`, a first dated
  `log.md` entry, and empty `sources/` and `wiki/` dirs; it refuses when the
  wiki directory already exists (mirror `init_workspace`'s refuse-to-nest
  guard). Rejected: overwrite-and-merge — hand recovery beats silent damage.
- **Staged write path.** `spec_emit.py wiki --from <staging-dir>`: the staging
  dir mirrors a store subset — `wiki/<slug>.md` files, `index.md`, `log.md`,
  `queue.md`, and add-only `sources/<file>` (overwriting an existing source is
  refused; sources are immutable). The engine backs up affected store files,
  installs the staged set, runs the full wiki lint on the resulting store, and
  on any finding restores the backup and exits non-zero. Existing pages are
  overwritten without a `--replace` flag — incremental page updates are the
  normal case, and the lint-and-rollback provides the guarantee. Rejected:
  in-place edits + trailing lint (an interrupted session leaves an invalid
  store); full-store swap (heavy, racy).
- **Queue verb.** `spec_status.py wiki-queue-add <q-slug> --question TEXT
  --options TEXT --recommendation TEXT [--origin TEXT]` builds a block with
  `Asked: <today> <origin>` and `Answer: pending`, appends it to `queue.md`,
  and re-validates the queue; a duplicate `q-<slug>` or invalid result restores
  the prior content and exits non-zero. Ships here so the ask-mikk-oracle
  member stays skill/agent-only.
- **Read verbs.** `wiki-show` prints the store root, page count, index
  coverage health, pending-question count, and the last log entry. `cat wiki
  <slug>` prints `wiki/<slug>.md`; the reserved slugs `index`, `log`, `queue`,
  `schema` resolve to the top-level files of the same name.
- **Risks.** Two sessions emitting concurrently can interleave — accepted and
  documented (epic non-goal); the per-file backup/rollback keeps the window to
  one emit. Dates come from the script's local clock, matching existing
  engine behavior.
