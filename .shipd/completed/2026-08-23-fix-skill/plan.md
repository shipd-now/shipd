# fix-skill
Status: verified

## Idea

Add a `/s:fix` debugging skill that retrieves the spec-library artifacts
related to a user-described problem — through a new `related` search verb on
the engine and the `shipd` binary — reads them, diagnoses the code, and fixes
it.

### Motivation

When a user reports a bug there is no guided path from the problem description
to the spec surfaces documenting the intended behavior — 228 completed changes
and 47 verified capabilities are reachable only by exact slug. The user wants a
`/s:fix` skill that finds the related specs, locates the problem in the code,
and fixes it.

### Details

- New `related <term> [<term>...] [--json]` verb in
  `plugins/s/skills/build/scripts/spec_status.py`: stdlib term-hit ranking
  over verified specs, planned and completed changes, research reports, epics,
  and the workspace wiki (when discoverable).
- New curated `shipd related` delegation row in `plugins/s/bin/shipd`.
- New skill `plugins/s/skills/fix/SKILL.md` and harness body
  `plugins/s/harness/bodies/fix.md` registering `/s:fix`.
- `README.md` / `AGENTS.md` listings and a plugin version bump to `0.6.148`.

Affected capabilities: `spec-status` (modified), `shipd-cli` (modified),
`shipd-fix` (added). Impact: the files above plus
`plugins/s/skills/build/tests/test_spec_status.py` and
`test_shipd_cli.py`.

### Non-goals

- No embeddings, index service, or third-party retrieval — case-insensitive
  term counting in stdlib Python only, per the constitution.
- `/s:fix` never edits spec artifacts or change statuses; a fix that requires
  changing documented behavior hands off to `/s:plan`.
- No shipping from `/s:fix` — it stops after fix + verification; commit,
  branch, and PR stay with the user and host-repo conventions.
- `related` searches the invocation root's content directory only — no
  `.worktrees/` probing (that is `locate`'s job).

## Implementation

- **The verb lives in `spec_status.py`**, host of every mediated read (`cat`,
  `locate`), so `bin/shipd` delegation is one `VERB_TABLE` row. Rejected: a
  new `spec_search.py` — a new script plus scaffolding for one read verb.
- **Corpus and kinds** (each match is one artifact `(kind, slug)` whose slug
  feeds the matching `cat` verb):
  `verified` → `verified/<slug>/spec.md`; `planned` →
  `planned/<slug>/{plan.md,tasks.md,specs/*/spec.md}`; `completed` →
  `completed/<date>-<slug>/` same file set, slug printed with the date prefix
  stripped (regex `^\d{4}-\d{2}-\d{2}-(.+)$`, mirroring `bin/shipd`'s
  `ARCHIVE_DIR_RE`) so it feeds `cat change <slug>`; `research` →
  `research/<slug>/report.md`; `epic` → `epics/<slug>/epic.md`; `wiki` →
  the workspace store's `wiki/<slug>.md` pages, resolved through workspace
  discovery like `_wiki_store(root, personal=False)`, wrapped so any
  resolution failure (observed: `wiki-show` exits 1 with `Error: no wiki
  store …` in this repo) silently skips the wiki while the other surfaces
  still print.
- **Scoring**: per term, case-insensitive substring occurrence count, summed
  over all of an artifact's files; artifacts with score 0 are dropped.
  Ordering is score descending, then kind, then slug — fully deterministic.
  Output caps at ten blocks followed by one `… and N more` line when more
  matched. Rejected: regex tokenizing/stemming — needless complexity for a
  grep-convention repo.
- **Output shape mirrors `locate`**: one keyed block per match — `kind:`,
  `slug:`, `score:`, `path:` (path relative to the root when inside it,
  absolute otherwise, e.g. wiki pages). `--json` emits exactly one JSON array
  of objects with those four keys. No match → single `Error: no artifacts
  match …` line, exit 1, matching `locate` and the error-output convention.
  Missing corpus directories are skipped silently; at least one term is
  required (argparse usage error otherwise).
- **Skill flow** (`skills/fix/SKILL.md`): announce the plugin version; distill
  the problem description into search terms; run `related` and read every
  retrieved artifact through the `cat` verbs before diving into code;
  reproduce the problem where a runnable surface exists before changing
  anything; then classify — code drifted from documented behavior (or a bug no
  spec covers) → apply the fix with a regression test per the host repo's
  testing conventions and re-run the reproduction and relevant tests; the
  documented behavior itself wrong → stop without touching any spec artifact
  and hand off to `/s:plan` with the findings. End by reporting diagnosis,
  fix, and verification evidence — no commit, branch, push, or PR. Engine
  scripts are invoked via `${CLAUDE_PLUGIN_ROOT}` paths, matching the review
  skill.
- **Registration mirrors gate-rename**: the bodies/skills id-set equality
  test forces `bodies/fix.md` and `skills/fix/` to land together; body carries
  the `<!-- description: -->` marker and `<!-- include:preamble -->` like
  `bodies/review.md`. No `harness/references/fix.md` — most commands ship
  without one; the body's file-references gate takes the inline else-branch.
- **Version bump** `0.6.147` → `0.6.148` in
  `plugins/s/.claude-plugin/plugin.json`, per the plugin-cache rule.

Risk: scanning ~230 archives per invocation — a few hundred small files read
sequentially; stdlib I/O handles this in well under a second, and no cache is
added until proven needed.

## Questions and answers

### Q1: After the fix, does /s:fix ship it?
- **Question:** After applying and verifying the fix, does `/s:fix` stop and
  report (shipping left to the user and host conventions) or drive branch,
  commit, push, PR, and the review gate itself? Options: (a) stop and report;
  (b) drive full shipping. Recommendation: (a).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Stop and report — the skill ends with diagnosis, fix, and
  verification evidence; committing, branching, and PR shipping stay with the
  user and the host repository's conventions, mirroring `/s:review`'s
  restraint.
- **Queued:** none (no workspace discoverable from this repo)

### Q2: What corpus does `related` v1 search?
- **Question:** Does v1 search verified specs + planned changes + completed
  archives only, or also research reports, epics, and the workspace wiki?
  Options: (a) specs + changes only; (b) everything. Recommendation: (a).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Everything — verified specs, planned changes, completed
  archives, research reports, epics, and the workspace wiki, with the wiki
  skipped silently when no workspace is discoverable.
- **Queued:** none (no workspace discoverable from this repo)
