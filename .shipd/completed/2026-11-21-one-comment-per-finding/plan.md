# one-comment-per-finding
Status: verified
Planned-at: f05885040682aa3309edf95ee335f4d8f623f3d3
Gated-hash: e0baf5430390

## Idea

The review gate posts one inline comment per finding, anchored at its first
anchorable location and naming the rest, and every folded finding names all
its locations.

### Motivation

A pull request reader sees the same finding twice when it names two sites:
on 2026-11-21 a factory review posted two identical full comments at
`progress.js:90` and `:92`, and three medium findings opened six threads and
six room tasks. A folded multi-location finding shows `<first> (+N more)`, so
the reader cannot see its other sites.

### Details

- `_split_findings` keeps only the first anchorable location of each finding.
- That comment keeps its `Also recurs at:` line and the identity its site had
  under the per-location scheme. Its room task data gains `locations`.
- Folded bullets in "Additional findings" and "Already there" name
  `locations[0]` in bold and add an `Also recurs at:` sub-line.
- `prior --from <review-json|->` tags each thread entry with the `id` of the
  payload finding whose identities match it. Every location's per-location
  hash counts, so threads already posted per location on existing pull
  requests still map to their finding.
- `posting.md` step 3 and step 5, and `docs/semantic-review-reference.md`,
  describe the new posting and matching rules.

Affected capabilities: `semantic-review` (`gate-poster` and
`review-incremental` modified). Impact:
`plugins/s/skills/review/scripts/review_gate.py`, its tests, the two docs, and
the plugin manifest.

### Non-goals

- Bumping the factory's pinned plugin ref (`SHIPD_REF` in
  `server/runner-image/versions.env` of `mikkel-bergmann/shipd-factory`). That
  is a separate factory change after this one merges.
- No edit, deletion, or repost of per-location threads already on a pull
  request. `resolve` and `autoreply` keep working on them per thread.
- No change to the copilot CI gate workflow, which posts single-path
  findings.
- No change to the summary table's `(+N more)` cell.

## Implementation

- **Anchoring.** In `_split_findings`, loop over a finding's parsed locations
  and stop at the first anchorable one. Append one `(f, path, line, idx)` per
  finding. `_review_comment` and `_post_review` stay as they are, so the
  existing rule holds: a suggestion attaches only when `idx == 0`.
  `post`'s `anchored` result count now counts findings.
- **Identity (Q1).** The one comment keeps the hash `_inline_body` already
  computes for its anchored site:
  `_finding_hash(path_k, what, k if len(locations) > 1 else 0)`. For a
  single-location finding, or one anchored at `locations[0]`, that is the
  same hash as before. `_finding_hash` does not change. Rejected: always
  hashing `locations[0]`, which breaks when `locations[0]` has no line and
  would give the comment a hash no earlier thread at that site carried.
- **Identities.** Add `finding_identities(f)`. It returns, in location order,
  `_finding_hash(path_i, what, i if n > 1 else 0)` for each location whose
  path parses with `_parse_location`. This set holds every hash the old
  per-location scheme posted for that finding.
- **Matching old threads (Q2).** `prior(pr, gh, findings=None)`. Given
  `findings`, each entry gains `"finding"`: the `id` of the first finding
  whose `finding_identities` contain the entry's `hash`, or `None`. Without
  `findings`, the entries do not change. The CLI adds
  `prior <pr> --from <json|->`, which reads the payload's `findings`.
  `posting.md` step 3 writes the draft payload to a temp file, runs
  `prior <pr> --from <that file>`, and omits each finding that a `replied`
  entry names, whatever location that thread sits at. Rejected: leaving the
  hash math in prose, because a session cannot recompute a per-location hash
  by hand, so old threads at index 1 and later would never match and the
  finding would be posted again.
- **Old threads.** Old per-location threads are left in place. `resolve`
  resolves each one on its own evidence, a reply or a later commit, and
  `autoreply` replies to each unreplied one. Neither reads hashes, so no old
  thread is orphaned and none is posted again. Tests pin both behaviours.
- **Summary (Q3).** In `render_summary`'s `bullets`, the bold location is
  `locations[0]` with no `(+N more)`. When there are more locations, the next
  line is `  - Also recurs at: <the rest, comma-separated>`, followed by Why
  and Fix. `_detail_cell` keeps `(+N more)`. The rejected-review fallback
  folds through the same bullets, so it names every location too.
- **Room task data (Q4).** `_room_finding_line` adds
  `"locations": list(f.get("locations") or [])` to the data part, so an author
  agent reading the task sees every site to fix.
- **`Also recurs at:` format.** Keep the line as it is,
  `Also recurs at: <loc>, <loc>`. The in-flight `resolve-fixed-in-reply`
  parses that line.
- **Version.** Advance the plugin version once. If
  `version_guard.py --help` lists `--advance`, leave the bump to `/s:build`'s
  ship-time step. Otherwise set it one patch above `origin/main`.

Risk: `resolve-fixed-in-reply` also modifies `review-incremental` from the
same base, `2362742d864e`. Whichever change merges second sees a stale-base
warning and must restate both sets of edits. Risk: a reply on any old
per-location thread now suppresses the whole finding. That is intended,
because a person has answered that finding.

## Questions and answers

### Q1: Which identity does the one comment carry?
- **Question:** Options: (1) the per-location hash its anchored site already
  had; (2) always the `locations[0]` hash. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. `_finding_hash` stays unchanged, single-location The user chose this default on 2026-11-21, answering "Accept all defaults".
  identities stay the same, and the hash is always computed from a parseable
  path.
- **Queued:** q-review-single-comment-identity

### Q2: How does the post flow match old per-location threads?
- **Question:** Options: (1) `prior --from <review-json>` tags each entry with
  the matching finding id, using every per-location identity; (2) state the
  rule in `posting.md` only. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1, and a `replied` thread at any of the finding's The user chose this default on 2026-11-21, answering "Accept all defaults".
  locations omits it. The match is then code and can be tested, not hash
  math a session does by hand.
- **Queued:** q-review-prior-legacy-match

### Q3: Where does the summary name the other locations?
- **Question:** Options: (1) the table keeps `(+N more)` and each folded
  bullet gains an `Also recurs at:` sub-line; (2) the table lists every
  location. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. The table stays one scannable line per finding, and The user chose this default on 2026-11-21, answering "Accept all defaults".
  each location still appears in an inline comment or a folded bullet.
- **Queued:** q-review-summary-locations

### Q4: Does the room task data carry the full locations list?
- **Question:** Options: (1) add `locations` to the data part; (2) keep only
  `path` and `line`. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. With one task per finding, the task is the only The user chose this default on 2026-11-21, answering "Accept all defaults".
  place an author agent learns the other sites.
- **Queued:** q-review-room-task-locations

## Readiness attestation

### Problem and motivation

A multi-location finding posts one full comment per site, and a folded one
hides its other sites.

Evidence:

- `review_gate.py:256-274` `_split_findings` appends one tuple for each
  anchorable location.
- `review_gate.py:408-415` and `:545-549` render `(+N more)` and no other
  locations.

### Scope and non-goals

The poster, `prior`, and two docs change. The copilot workflow, `resolve`,
`autoreply`, and the factory pin stay as they are.

Evidence:

- In scope: `review_gate.py:256-274`, `:529-556`, `:839-858`, `:1620-1669`,
  `:1716-1719`, `:1781-1788`; `posting.md` steps 3 and 5;
  `docs/semantic-review-reference.md:125-164`.
- Out of scope: `plugins/s/integrations/copilot/copilot-review-gate.yml:1304-1350`
  (single-path findings) and `resolve` at `review_gate.py:1524-1564`.

### Affected capabilities and files

One capability, `semantic-review`, has two requirements modified.

Evidence:

- `gate-poster` (base c4d268a334db) and `review-incremental` (base
  2362742d864e), hashes from `spec_status.py base-hash`.
- Runnable premise: `post` run through the test `FakeGh` with a medium
  finding at `public/js/ui/progress.js:90` and `:92` produced 2 inline
  comments with the same body, each carrying a room Message, with hashes
  `57a841cd9cba` and `85576313a94a`.
- Runnable premise: `_finding_hash("public/js/ui/progress.js", "dup")` gave
  `57a841cd9cba`, the same as the index-0 comment's marker.
- Runnable premise: a folded finding at `z.py:9`, `y.py:8` and `x.py:7`
  rendered `- **z.py:9 (+2 more)** ...`, with `y.py:8` absent from the body.
- Runnable premise: a confident finding with an off-diff `locations[0]`
  anchored once at `locations[1]`, with no suggestion.
- Runnable premise: `python3 -m unittest discover -s plugins/s/skills/review/tests`
  ran 351 tests, `OK`. `version_guard.py --help` lists no `--advance`.

### No open task-shaping decision

Every decision is settled by a planner default, pending a human answer.

Evidence:

- Q1 to Q4 above, each queued.
- The `Also recurs at:` format is kept for `resolve-fixed-in-reply`, settled
  by investigation.
