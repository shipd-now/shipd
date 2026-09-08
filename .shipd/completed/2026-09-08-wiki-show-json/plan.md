# wiki-show-json
Status: verified

## Idea

Add a `--json` flag to the status CLI's `wiki-show` verb that emits the wiki
store's full state — health fields, pages with bodies and index summaries,
queue blocks, and log entries — as one JSON document.

### Motivation

The shipd-app dashboard's wiki epic (shipd-now/shipd-app#14) decides that its
sync service consumes wiki state via engine JSON reads, never by parsing
`.shipd/wiki/*.md` itself — but none of the wiki verbs carry `--json` today,
so no machine-readable read of the store exists. This change closes that gap
upstream, exactly as the consumer's engine-as-contract decision prescribes.

### Details

- Extend `wiki-show` with the shared `--json` flag: one JSON document on
  stdout, derived from the same reads as the text report, flagless output
  byte-identical, error handling unchanged in both modes.
- The document carries the store's full content — page bodies, index
  summaries, queue block fields, parsed log entries — not just the text
  report's health counts, because the consumer must render pages without
  parsing markdown files itself.
- Works under `--personal` and for the repo-local fallback store with the
  same semantics the text form already has.

Affected capabilities: `spec-status` (modified: `json-output`,
`wiki-status-verbs`). Impact: `plugins/s/skills/build/scripts/spec_status.py`,
`plugins/s/skills/build/tests/test_spec_status.py`,
`plugins/s/.claude-plugin/plugin.json` (version bump per AGENTS.md); no new
dependencies (stdlib `json` plus existing `spec_common` parsers).

### Non-goals

- No JSON on the other wiki verbs (`wiki-init`, `wiki-remove`, the queue
  mutators, `cat wiki`) — mutating and guarded verbs stay text-only per the
  json-output convention.
- No git-derived data (per-page timestamps, revision counts) — the verb stays
  pure-filesystem; a consumer that owns a clone derives times itself.
- No chain-content merging: the document describes the resolved store's own
  content; inherited chain stores are named as paths only, exactly like the
  text `chain:` line.
- No new store grammar — every field comes from the existing `spec_common`
  parsers.

## Implementation

- **One data pass, two renderers.** Refactor `cmd_wiki_show` (currently
  `spec_status.py:3383`) to gather a data dict first, then render either the
  existing text lines or `json.dumps` of the document. The text branch must
  reproduce today's output byte-for-byte (observed live: 7 lines from
  `wiki: …` through `last log: …`, `(repo-local fallback)` marker included).
  Rejected: a separate `wiki-dump` verb — a second read surface for the same
  store state, against the one-verb-one-report convention.
- **Document shape (binding).** Exactly one JSON object with keys:
  - `store` (absolute store path), `present` (bool: the store's `wiki`
    directory root exists — false in the absent-nearest-store chain case),
    `fallback` (bool), `personal` (bool);
  - `chain`: list of inherited chain store paths, nearest first (empty where
    the text form prints `chain: none`);
  - `base`: `null` where the text form prints `base: none`, else
    `{"path": <abs path>, "present": <bool>}`;
  - `pages`: list sorted by slug, each `{"slug", "summary", "body"}` —
    `summary` from the store's `index.md` entry for that slug (`null` when
    unindexed), `body` the raw markdown file content;
  - `coverage`: `{"unindexed": [<slugs>], "orphaned": [<slugs>]}`, both
    sorted (empty lists where the text form prints `coverage: ok`);
  - `queue`: list in document order, each `{"id": "q-<slug>",
    "fields": {<the five WIKI_QUEUE_FIELDS present on the block>}}`;
  - `log`: list in document order, each `{"date", "op", "subject"}` from
    `WIKI_LOG_HEADER_RE`'s three groups.
  Counts (`pages`, pending questions) are derivable and not duplicated.
- **Parser wiring.** Attach the shared `_add_json_flag`
  (`spec_status.py:3824`) to the `wiki-show` subparser with a help text
  naming the document; pass the flag through `main()`'s dispatch as a
  keyword. Update `_add_json_flag`'s docstring roster sentence to include
  `wiki-show`.
- **Errors and edge semantics are shared, not duplicated.** The no-store
  error, the `--personal` fixed-path resolution, and the fallback resolution
  all run before the render branch, so both modes inherit them unchanged —
  matching json-output's "error handling unchanged in both modes" clause.
- **Version bump.** `plugins/s/.claude-plugin/plugin.json` 0.6.191 → 0.6.192
  in the same change (AGENTS.md: every `plugins/s/` change bumps the version
  in the same PR).
- **Page bodies are a JSON-only read.** The flagless rendering never opens
  page files (the pre-flag verb never did, and eager body reads would turn a
  store's own unhealth — a non-UTF-8 or unreadable page — into a crash of the
  health report). Under `--json`, bodies decode as UTF-8 with U+FFFD
  replacement so one undecodable page cannot kill a store read, and an
  unreadable page file raises the verb's normal `Error:` path naming the
  file. Error-path stdout is deliberately not preserved: the partial lines
  the old text form printed before a malformed-`wiki_base` error are gone,
  while stderr text and exit codes stay identical.
- Risk: silently drifting the flagless text output during the refactor —
  guarded by a test asserting the exact pre-change line sequence on a
  populated store.
