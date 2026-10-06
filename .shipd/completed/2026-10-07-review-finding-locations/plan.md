# review-finding-locations
Status: verified
Theme: reliability

## Idea

### Motivation

A ReviewBench benchmark run (external harness at
`/Users/mikkelbergmann/projects/benchy`, shared by a peer session) measured
`/s:review`'s grounded recall at 33.2% against ReviewBench's golden findings.
Of 57 missed golden findings, roughly 10 are not missing judgement at all:
`/s:review` found the real defect, but either anchored it at the symptom's
call site instead of the line its own fix would change, or reported a defect
that recurs at several call sites only once. ReviewBench's judge matches a
finding to its golden counterpart only within the same file, so a correctly
identified defect anchored at the wrong site — or reported once instead of at
every site it recurs at — scores as a miss indistinguishable from a defect
`/s:review` never found.

Four concrete examples from the run: a `lastSynced`-never-written defect
anchored at the caller (`WorkspaceManagerModal.tsx:303`) when the fix belongs
at `syncEngine.ts:49`; a plaintext-credentials defect anchored at the modal
when the fix belongs in `storageDriver.ts`; a missing-flush defect recurring
at six call sites reported once; a URL double-encoding defect recurring at
three call sites reported once.

### Details

Teach `/s:review` two things: anchor a finding's location at the line its fix
would actually change, never at a caller or symptom site; and, when the same
defect recurs at more than one call site, carry every site in one finding
instead of reporting it once. The posting side then places one inline PR
comment per site a finding names, so a reader (and ReviewBench's judge) sees
the defect at every location it actually touches.

### Non-goals

- The other four ReviewBench-driven changes shared in the same handoff — the
  low-severity rubric and breadth pass, the PR-description-vs-implementation
  check, the new risk lenses (packaging manifests, stdlib/framework
  semantics, UI state lifecycle, sibling consistency), and the missing-test
  precision fix — are deliberately out of scope here. They are planned
  separately, one at a time, so each change's effect on recall/precision can
  be measured in isolation, per the benchmark owner's own sequencing
  (`1, then 3, then 2`, with 4 and 5 after).
- The GitHub Copilot posting surface, `copilot-review-gate.yml`, and its own
  finding contract (`path`/`start_line`/`end_line`/`detail`/`replacement`) —
  unrelated to ReviewBench, which only exercises `/s:review` locally through
  `review_gate.py`. Untouched.
- The ReviewBench harness itself, under `/Users/mikkelbergmann/projects/benchy`
  — external to this repo. Re-measurement happens there after this ships.
- No change to the severity rubric, the verdict rule, or any risk lens.

Affected capability: `semantic-review` (requirements `review-skill` and
`gate-poster`, modified). Impact: the two JSON payload references
(`json-output.md`, `harness/references/review.md`), the skill's reporting
instructions (`SKILL.md`), the poster (`review_gate.py`), the posting
reference (`posting.md`), and the poster's test suite
(`test_review_gate.py`). No new dependency.

## Implementation

### Schema: `location` (string) becomes `locations` (array)

The `--json` finding's `location: "path:LINE"` field becomes
`locations: ["path:LINE", ...]`, a non-empty array, on both documented payload
surfaces — `plugins/s/skills/review/references/json-output.md` and
`plugins/s/harness/references/review.md`, which must stay identical as they
already do for every other field. `locations[0]` is the primary/fix site; any
further entries are the other sites the same defect recurs at. The unrelated
`change.location` field (`"planned"` / `"completed"`) is untouched — it names
a different thing and is not part of this change.

### Skill instruction

`SKILL.md`'s reporting step instructs the model: anchor each location at the
line its own fix would change, never at a caller or symptom site; and when the
same defect recurs at more than one call site, write one finding whose
`locations` names every site, not one finding per site.

### `review_gate.py`

- `_parse_locations(f)` (new): maps every string in `f.get("locations") or []`
  through the existing `_parse_location`, dropping entries that fail to parse.
- `_split_findings`: a finding is anchored when **any** of its locations
  resolves to a RIGHT-side commentable line; it yields one
  `(finding, path, line, index)` tuple per commentable location — so a finding
  recurring at several commentable sites gets one inline comment per site. A
  finding lands in `unanchored` only when **none** of its locations resolve.
- `_finding_hash(path, what, index=0)`: gains an optional `index`, folded into
  the digest only when the finding declares more than one location. A
  single-location finding's hash is byte-identical to today's, so existing
  identity/dedup continuity (`prior`, `resolve`) is unaffected; each site of a
  multi-location finding gets its own identity, so each is dispositioned
  independently.
- `_inline_body`: when the finding carries locations beyond the one a given
  comment anchors, append a line naming them (`Also recurs at: path:line,
  path:line`), so any one of the posted comments shows the full recurrence.
- `_detail_cell` (summary table row) and the "Additional findings" unanchored
  renderer: show `locations[0]` plus `(+N more)` when there is more than one.
- `_suggestion`/`_review_comment`: a committable suggestion block is only ever
  attached to the comment anchored at `locations[0]` — a suggestion is a
  single contiguous-range edit and cannot replay identically across sites
  whose surrounding code differs.

### `posting.md`

Step 5's description of what the poster does — "posts anchored inline
comments for in-diff findings (folding the rest into the summary)" — is
restated to say one inline comment per anchorable location across a finding's
`locations` array.

### Spec

`.shipd/verified/semantic-review/spec.md`'s `review-skill` and `gate-poster`
requirements are MODIFIED to state the `locations` array, the fix-site
anchoring rule, the one-finding-per-recurring-defect rule, and the
one-comment-per-anchorable-location posting rule, each with new scenarios.

### Tests

Every `"location": "<path>:<line>"` fixture in `test_review_gate.py` —
including the `_finding()`/`_review()` helpers — is renamed to
`"locations": ["<path>:<line>"]`, with no behavior change for the
single-location case. New tests cover: two commentable locations across two
files producing two distinct inline comments with distinct hashes; a mixed
commentable/off-diff pair posting only the commentable one and not folding;
an all-off-diff multi-location finding folding entirely; a suggestion
attaching only to the `locations[0]` comment; and the summary/unanchored
renderers' `(+N more)` suffix.

### Version

`plugins/s/.claude-plugin/plugin.json`'s `version` is bumped in this PR, per
`AGENTS.md`: every change touching `plugins/s/` bumps it so the cached plugin
snapshot does not go stale.

## Readiness attestation

### Problem and motivation

`/s:review` findings that are correct in substance score as misses against
ReviewBench because the engine has no way to express "the fix site differs
from the symptom" or "this defect recurs at N sites" — a finding carries
exactly one `location`.

Evidence:

- `plugins/s/skills/review/references/json-output.md:27` — `"location":
  "path/to/file.ext:LINE"`, a single string.
- `plugins/s/skills/review/scripts/review_gate.py:184-207` —
  `_parse_location`/`_split_findings` resolve exactly one `(path, line)` per
  finding.
- Benchmark evidence (`/Users/mikkelbergmann/projects/benchy/runs/analysis/missed.tsv`,
  summarized in the handoff): `lastSynced` never written (shipd anchored
  `WorkspaceManagerModal.tsx:303`, golden `syncEngine.ts:49`); plaintext
  credentials (shipd `modal:277`, golden `storageDriver.ts:185`); a missing
  flush recurring at 6 call sites, reported once; URL double-encoding
  recurring at 3 sites, reported once.

### Scope and non-goals

In scope: the `locations` schema change on both JSON payload surfaces, the
skill's fix-site/one-finding-per-recurrence instruction, the poster's
anchoring/hashing/rendering, `posting.md`'s description, the spec, the tests,
and the plugin version bump. Out of scope: the other four ReviewBench changes
from the same handoff, the Copilot posting surface, the benchmark harness
itself, and the severity rubric/verdict rule.

Evidence:

- In scope: `plugins/s/skills/review/references/json-output.md`,
  `plugins/s/harness/references/review.md`,
  `plugins/s/skills/review/SKILL.md`,
  `plugins/s/skills/review/scripts/review_gate.py`,
  `plugins/s/skills/review/references/posting.md`,
  `plugins/s/skills/review/tests/test_review_gate.py`,
  `.shipd/verified/semantic-review/spec.md`,
  `plugins/s/.claude-plugin/plugin.json`.
- Out of scope: `plugins/s/integrations/copilot/copilot-review-gate.yml` uses
  its own `path`/`start_line`/`end_line`/`detail`/`replacement` finding shape
  (confirmed by reading `placed()`/`inline_body()` in that file) — a different
  contract for a different reviewer, untouched by ReviewBench.

### Affected capabilities and files

One capability, two requirements.

Evidence:

- Capability: `semantic-review`, requirement `review-skill` (base hash
  `687d64523303`) and requirement `gate-poster` (base hash `d8d8f12c1059`),
  from `spec_status.py base-hash semantic-review <id>`.
- Runnable premise: `python3 -m unittest discover -s
  plugins/s/skills/review/tests -v` passes on `main` before this change
  (confirms the suite is green to diff against).
- Runnable premise: `grep -n location
  plugins/s/integrations/copilot/copilot-review-gate.yml` shows no match on
  the finding-location field name used there (`path`/`start_line`/`end_line`),
  confirming that surface is unaffected by this schema change.

### No open task-shaping decision

- Whether to keep a singular `location` alongside the new `locations` for
  backward compatibility: no — both producer (`SKILL.md`) and consumer
  (`review_gate.py`) are updated in the same plugin-version bump, and
  `AGENTS.md` already requires every `plugins/s/` change to bump the cached
  snapshot's version, so there is no cross-version compatibility window to
  preserve.
- Whether a multi-location finding's per-site hash should include the line
  number: no — the existing `_finding_hash` doc comment explains line is
  excluded so a finding's identity survives the line moving as the diff around
  it changes; reusing that same tolerance per site (keyed on index, not line)
  keeps that property for every site, not just the first.
- Whether a suggestion should attach to more than one location: no — a
  suggestion is a single contiguous-line replacement; replaying the same
  replacement lines at a second site with different surrounding code would be
  a wrong, unreviewed edit a one-click Apply would commit verbatim.
