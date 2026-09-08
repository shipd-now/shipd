## 1. Tests first

- [x] 1.1 [req: wiki-status-verbs] In
      `plugins/s/skills/build/tests/test_spec_status.py`, next to the existing
      `wiki-show` tests (near `test_wiki_show_reports_store_health`), add a
      populated-store fixture (an indexed page with an `index.md` summary, an
      unindexed page, a `queue.md` with one pending `## q-…` block carrying
      all five fields, a `log.md` with one dated entry) and a test asserting
      `wiki-show --json` prints exactly one parseable JSON object with:
      `store`/`present`/`fallback`/`personal` fields, `chain` `[]`, `base`
      `null`, `pages` sorted by slug each carrying `slug`, `summary` (null
      for the unindexed page), and raw markdown `body`, `coverage` naming the
      unindexed slug and empty `orphaned`, `queue` carrying the block id and
      its field values, and `log` carrying the entry's `date`, `op`,
      `subject`. Run it and observe it fail — the flag does not exist yet.
- [x] 1.2 [req: wiki-status-verbs, json-output] In the same test file, add:
      (a) a byte-identity test capturing `wiki-show` flagless output on the
      populated store and asserting the exact current line sequence
      (`wiki: …`, `chain: none`, `base: none`, `pages: N`, `coverage: …`,
      `pending questions: N`, `last log: …`); (b) a
      `wiki-show --personal --json` test against a seeded personal store
      asserting `personal` true, `chain` `[]`, `base` null; (c) a no-store
      test asserting `--json` exits non-zero with the same `Error:` text as
      the flagless form. Observe the new `--json` cases fail.

## 2. Implementation

- [x] 2.1 [req: wiki-status-verbs] In
      `plugins/s/skills/build/scripts/spec_status.py`, refactor
      `cmd_wiki_show` to build a data dict first (store path, present,
      fallback, personal, chain list, base object-or-None, pages with
      slug/summary/body, coverage lists sorted, queue blocks via
      `sc.parse_queue_blocks`, log entries via the three
      `sc.WIKI_LOG_HEADER_RE` groups), then branch: flagless renders the
      existing text lines from that dict byte-identically; `--json` prints
      `json.dumps` of the document and nothing else. Resolution and error
      paths stay before the branch so both modes share them.
- [x] 2.2 [req: wiki-status-verbs, json-output] Wire the flag: call
      `_add_json_flag` on the `wiki-show` subparser (help text naming the
      store-state document), pass the parsed flag through `main()`'s
      `wiki-show` dispatch into `cmd_wiki_show(..., as_json=...)`, and update
      `_add_json_flag`'s docstring roster sentence to include `wiki-show`.
- [x] 2.3 [req: wiki-status-verbs, json-output] Run the new tests from 1.1
      and 1.2 and confirm they pass, flagless byte-identity included.

## 3. Version and verification

- [x] 3.1 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json`
      from 0.6.191 to 0.6.192.
- [x] 3.2 [req: *] Run the full engine suite
      (`python3 -m pytest plugins/s/skills/build/tests/ -q`, no `textual`
      installed) and confirm it passes.

## 4. Validator fixes

- [x] 4.1 [req: wiki-status-verbs, json-output] In
      `plugins/s/skills/build/scripts/spec_status.py`, make page-body reads
      JSON-only: `_wiki_show_data` (or its caller) reads page files only when
      the JSON document is being emitted, decoding as UTF-8 with
      `errors="replace"`; an `OSError` on a page file raises `StatusError`
      naming the file. The flagless path must not open any `wiki/<slug>.md`.
- [x] 4.2 [req: wiki-status-verbs, json-output] In
      `plugins/s/skills/build/tests/test_spec_status.py`, add regressions: a
      latin-1-encoded page renders the flagless report exactly as before
      (rc 0, same 7 lines) while `--json` carries the body with U+FFFD
      replacement; an unreadable page (chmod 000, skipped when running as
      root) leaves the flagless report intact and makes `--json` exit
      non-zero with an `Error:` line naming the file. Re-run the full engine
      suite and confirm OK.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 126 | 39.4k |
| Edit | 14 | 1.2k |
| SendMessage | 2 | 1.2k |
| Read | 7 | 1.1k |
| Agent | 2 | 781 |
| (no tool) | 0 | 534 |
| ToolSearch | 1 | 188 |
| **Total** | 152 | 44.4k |
