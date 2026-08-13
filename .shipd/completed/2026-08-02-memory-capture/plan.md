# memory-capture
Status: verified
Epic: personal-memory
Theme: developer-experience

## Idea

Add `/s:preferences`, the write path into the personal memory store: it extracts
preference candidates (from an invocation argument or the session), reconciles
them against existing `memory-<subject>` pages, confirms with the user, and
installs them through one staged `spec_emit.py wiki --personal` call.

### Motivation

The `personal-memory` epic shipped the personal store (`personal-memory-store`)
and taught the oracle to read it first (`oracle-personal-rung`), but nothing
yet writes to it — so no preference can actually be captured. This member is
that write path: the on-demand skill that turns "mikk prefers vim / ASCII
diagrams / a terse tone" into `memory-*` pages the oracle already consults.

### Details

- Define the `memory-<subject>` page family: a `wiki/memory-<subject>.md` page in
  the personal store carrying a one-line preference statement and a provenance
  block (`- Origin:` the invoking repo, `- Captured:` the date).
- New skill `plugins/s/skills/preferences/SKILL.md` (`/s:preferences`):
  announce the plugin version, resolve the personal store with `wiki-show
  --personal` (scaffolding it with `wiki-init --personal` when absent), extract
  candidates from the invocation argument or the session, reconcile each against
  existing `memory-*` pages (add a new page, update an existing one, or skip a
  duplicate), confirm the proposed set with the user in a typed round, and
  install the touched subset through one staged `spec_emit.py wiki --personal`.
- Add a one-line `/s:preferences` entry to the AGENTS.md skill roster.

Affected capabilities: `shipd-memory` (added — `memory-page-family` and
`preferences-skill`). Impact: new `plugins/s/skills/preferences/SKILL.md`,
`AGENTS.md` roster sentence; plugin version bump to 0.6.23. No engine or script
changes — the `--personal` verbs already exist. No new dependencies.

### Non-goals

- No browse or removal — `/s:memory` (list) and `/s:forget` (remove) are the
  `memory-browse` member.
- No git first-run flow — detecting a non-git store and offering `git init` /
  remote / push is the `memory-git-backing` member; here, `wiki_autocommit`
  simply no-ops until the store is a git repo.
- No oracle or engine change — reads and writes go through the shipped
  `--personal` verbs; the oracle already consults the personal store first.
- No base/job split — the personal store is itself the single durable
  cross-workspace store, so the teach-style promotion does not apply.
- No embeddings or external service; reconciliation is LLM-side over grep and the
  index, per the epic's bindings.

## Implementation

- **`/s:preferences` mirrors the `/s:teach` write path, pointed at the personal
  store.** Like teach it resolves the store, decides what to write, confirms, and
  installs through **one** staged `spec_emit.py wiki` call over a throwaway
  staging dir — never editing store files in place. The only differences: every
  store verb carries `--personal` (so the target is `~/.shipd-memory/wiki`, resolved
  by fixed path), and there is no base-promotion step (the personal store is the
  single durable store). Rejected: a bespoke capture flow (needlessly diverges
  from the proven teach ingest contract).

- **The staged subset mirrors the store layout.** For a capture the staging dir
  holds each touched `wiki/memory-<subject>.md`, the **full** `index.md`
  (existing entries from `cat wiki index --personal` plus one
  `- [[memory-<subject>]] — <summary>` per touched page, so the entry set matches
  the page set after install), and the **full** `log.md` with a fresh
  `## [YYYY-MM-DD] preferences | <subject>` entry appended. Install:
  `spec_emit.py wiki --from <staging> --personal`, which backs up, installs,
  runs the whole-store wiki lint, and restores byte-for-byte on any finding.

- **Reconcile is LLM-side: add / update / skip-duplicate.** The skill reads
  `cat wiki index --personal` and greps the personal store's `wiki/` dir for the
  candidate's subject terms, then classifies each candidate: **add** a new
  `memory-<subject>` page, **update** an existing page whose statement the new
  information changes (re-emit the page — in-place edits stay forbidden), or
  **skip** a duplicate the store already records. No embeddings; grep + index
  only, per the epic. Rejected: always-add (would accrete duplicate pages).

- **Confirm before writing, via a typed round.** Because the capture writes
  durable personal memory — and, for session extraction, memory the user did not
  state verbatim — the skill first presents the proposed set (each candidate with
  its add/update/skip classification and target slug) and proceeds only on the
  user's typed go-ahead, mirroring teach's confirm-before-ingest discipline. This
  round uses plain-text (no AskUserQuestion), so the skill does not join the
  `shipd-interaction` question-rejection-recovery roster. Rejected: silent capture
  (writes personal memory the user never approved).

- **`memory-<subject>` page shape.** Line 1 `# memory-<subject>`; a one-line
  preference statement; then a provenance block — `- Origin: <invoking-repo>` and
  `- Captured: <YYYY-MM-DD>`. Kebab-case `<subject>`. It is an ordinary wiki page
  (indexed, lint-clean, oracle-readable), distinguished only by the `memory-`
  prefix the browse/forget members filter on.

- **Store scaffolding and git are out of band.** When `wiki-show --personal`
  reports no store, scaffold once with `wiki-init --personal` (mirroring teach's
  `wiki-init`). Commits ride the engine's existing `wiki_autocommit`, a silent
  no-op until `memory-git-backing` makes `~/.shipd-memory` a git repo — this member
  adds no git logic.

Risk: extracting from the session could over-capture (recording noise as a
preference); guarded by the mandatory confirm round, where the user prunes the
proposed set before anything is written. A skill-only change is exercised by a
real drive (capture into a throwaway `memory_dir`), not the engine unit suite,
and — per AGENTS.md — warrants a local eval run before shipping (the eval harness
does not yet cover `/s:preferences`, so this is a manual drive).
