# Tasks

## 1. Teach skill

- [x] 1.1 [req: teach-skill, teach-distill-scan, teach-gap-interview, teach-queue-drain, teach-ingest-bookkeeping]
      Write `plugins/s/skills/teach/SKILL.md` in the house skill shape
      (frontmatter `name: teach` with a trigger-phrase `description:` covering
      "teach mikk", "distill knowledge into the wiki", "drain the queue",
      "/s:teach" — model it on `plugins/s/skills/ask/SKILL.md`). The body
      states, in order: announce `am:teach v<version>` read from
      `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`; resolve the store
      with `spec_status.py wiki-show` (STATUS_CLI at
      `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py`), running
      `wiki-init` when the store is missing and stopping with a pointer at
      `workspace-init` when no workspace is discoverable; the scan — engine
      reads only (`cat epic <slug>`, `cat verified <capability>`,
      `cat research <slug>`, `project-show`, completed changes' plan
      decisions, then `cat wiki index` and candidate pages, with read-only
      grep over the store to widen); distillation into entity/convention
      pages per the store's `schema.md`, citing backing artifacts by name,
      bounded to 5–15 page touch-ups per run preferring decision-dense
      surfaces, updating existing pages over duplicating, honoring an
      optional focus argument; the interview — only gaps and contradictions
      the scan surfaces, one batched round (visible brief, then plain-text
      numbered options-first questions, recommendation first, typed reply),
      no interview when nothing surfaces, deferred items queued via
      `wiki-queue-add` in compact-question shape; queue draining — every
      `## q-` block with `Answer:` ≠ `pending` distilled into pages and
      removed from the staged `queue.md`, drained `q-<slug>`s named in the
      log entry, pending blocks untouched; and the ingest — author the
      touched subset (pages, `index.md`, `queue.md`, dated verbatim
      answer file under `sources/`) in a `mktemp -d` staging dir and install
      with one `spec_emit.py wiki --from <staging>` call, never editing
      store files in place, every run updating `index.md` entries and
      appending a dated `log.md` entry, and never copying repo artifacts
      into `sources/`.

## 2. Roster, version, and cross-check

- [x] 2.1 [req: *] In `AGENTS.md`, extend the skill roster sentence in the
      "Spec layout and lifecycle" section with `/s:teach` (distill spec
      artifacts and answered queue entries into the workspace wiki), keeping
      the existing sentence style.
- [x] 2.2 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` from 0.6.7 to 0.6.8.
- [x] 2.3 [req: *] Cross-check `plugins/s/skills/teach/SKILL.md` against the
      delta: grep it for the `wiki-init` scaffold path, the 5–15 touch-up
      bound, the gaps-and-contradictions-only interview with
      `wiki-queue-add` deferral, the `Answer:` ≠ `pending` drain-and-remove
      rule, and the `spec_emit.py wiki --from` staged write path; fix any
      drift so the file states all five.
