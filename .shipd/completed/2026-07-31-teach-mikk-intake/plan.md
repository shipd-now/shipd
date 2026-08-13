# teach-mikk-intake
Status: verified
Epic: mikk-knowledge

## Idea

Add the mikk-knowledge epic's write path: a `/s:teach` skill that distills
the repo's spec artifacts into workspace wiki pages, interviews the user only
about gaps and contradictions the scan surfaces, and drains answered queue
entries — writing exclusively through the store's staged, lint-gated engine
verbs.

### Motivation

The wiki store and the ask-mikk oracle shipped with no way to fill the store —
the workspace wiki holds zero pages today, so every oracle consult ends
`INSUFFICIENT` and answered queue entries have no path into wiki pages.
`/s:ask` already points users at "the future teach-mikk write path"; this
member is that path.

### Details

- New skill `plugins/s/skills/teach/SKILL.md` (`/s:teach`): resolve the
  store (scaffolding via `wiki-init` when missing), scan the repo's spec
  surfaces and the existing wiki, distill entity/convention pages, interview
  the user in one batched round on gaps and contradictions only, and ingest
  through `spec_emit.py wiki`.
- Queue draining: `queue.md` blocks whose `Answer:` is no longer `pending`
  are distilled into pages and removed in the same staged ingest.
- `AGENTS.md` skill roster gains `/s:teach`; plugin version bumps
  0.6.7 → 0.6.8.

Affected capabilities: `shipd-teach` (new). Impact: one new markdown file under
`plugins/s/skills/teach/`, `AGENTS.md`,
`plugins/s/.claude-plugin/plugin.json`. No engine scripts change — the store
verbs this skill uses (`wiki-init`, `wiki-show`, `wiki-queue-add`,
`cat wiki`, `spec_emit.py wiki`) shipped in `mikk-wiki-store`.

### Non-goals

- No engine changes and no new lint rules — the store grammar and verbs are
  complete; this member is skill-only.
- No caller integrations — `plan-ask-mikk` and `autopilot-ask-mikk` are later
  epic members.
- No background or scheduled ingestion, embeddings, or search services —
  every run is on-demand, index- and grep-based, per the epic.
- No whole-workspace multi-repo sweep in one run — a run ingests the invoking
  repo's surfaces; other repos are ingested by running the skill there.

## Implementation

- **Naming.** Skill directory `teach` (single-word verb like `ask`/`plan`) →
  `/s:teach`, capability `shipd-teach` per the `am-<skill>` convention.
  Rejected: a `teach-mikk` directory — no skill directory is multi-word and
  the `/s:` namespace already carries the brand.
- **Scan scope.** The invoking repo's spec surfaces, all engine-mediated:
  `cat epic <slug>` (Decisions/Design), `cat verified <capability>`,
  `cat research <slug>`, `project-show` for project context, and completed
  changes' plan decisions — plus the existing wiki (`cat wiki index`, then
  candidate pages) so distillation updates pages instead of duplicating them.
  Rejected: a whole-workspace sweep in one run — unbounded, and every engine
  read is rooted per-repo; cross-repo compounding comes from running the
  skill in each repo.
- **Bounded, prioritized ingest.** A run touches 5–15 pages (the epic's
  bound), preferring decision-dense surfaces first: epic Decisions/Design,
  then verified masters' norms, research findings, project context, completed
  changes. The run's log entry records what was covered so later runs
  continue; an optional invocation argument narrows a run to one topic or
  surface.
- **Write path.** The skill authors the touched store subset (`wiki/<slug>.md`
  pages, `index.md`, `queue.md`, `sources/` additions) in a throwaway staging
  dir and installs it with one `spec_emit.py wiki --from <staging>` call —
  lint-gated with rollback, so an interrupted or invalid run never corrupts
  the store. Rejected: in-place edits — the epic forbids skills writing into
  the store outside the staged, validated conventions.
- **Interview discipline.** Only gaps and contradictions the scan surfaces —
  never an open-ended interview. One batched round in the plugin's house
  shape: a visible context brief, then plain-text numbered options-first
  questions with the recommendation listed first, answered by typed reply.
  When the scan surfaces nothing, no interview happens. Items the user defers
  are queued via `wiki-queue-add` (compact-question shape) so they compound
  instead of vanishing. Rejected: interview-only or ingest-only intake — the
  epic rejected both.
- **Queue draining.** Every `## q-` block whose `Answer:` is not `pending` is
  distilled into page content and removed from the staged `queue.md` in the
  same ingest; the log entry names the drained `q-<slug>`. The queue lint
  accepts answered blocks, so draining is purely skill-side flow. Rejected:
  keeping answered blocks in the queue — the wiki page is the durable home
  and the queue stays a pending-only worklist.
- **Provenance.** Pages cite repo artifacts by name (e.g.
  `shipd verified/shipd-wiki`, `epic/mikk-knowledge`) — repo artifacts are
  never copied into `sources/` (duplication drifts, and add-only sources
  would refuse a refresh). Interview and drained-queue answers, which exist
  nowhere else, are preserved verbatim as a dated add-only file under
  `sources/` before being distilled. Rejected: sourcing every distilled
  artifact — the repos already hold them durably.
- **Store resolution.** `wiki-show` resolves the workspace and store health;
  a missing store is scaffolded with `wiki-init` (the verb refuses an
  existing store, so the call is safe). Unlike the non-blocking oracle,
  `/s:teach` is user-invoked and interactive: with no discoverable workspace
  it stops and points at `workspace-init` rather than inventing a store
  location.
- **Risks.** A model-driven distillation can misstate an opinion — guarded by
  citing the backing artifact on every page so a reader can verify, and by
  the interview surfacing contradictions rather than silently overwriting.
  Concurrent wiki writers can interleave — accepted epic-wide (no
  multi-writer coordination).
