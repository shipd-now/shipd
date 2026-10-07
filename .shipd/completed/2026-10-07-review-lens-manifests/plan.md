# review-lens-manifests
Status: verified
Theme: reliability

## Idea

### Motivation

Item 4 of the ReviewBench handoff adds four detection lenses; this is the
first. Three golden findings on the benchmark's pg-pool PR are manifest
defects `/s:review` has no reason to look for:

- `package.json`'s `files` allowlist omits the newly added
  `diagnostics.js`, so the published package lacks a module the entry point
  requires — while every test in the repository passes.
- Dependencies present in the lockfile but never declared in
  `package.json`, which resolve locally and fail on a clean install.

All three were rated high or medium in the golden set. Nothing in the
skill's six existing passes points at a manifest: the structural diff reads
a `package.json` change as JSON edits, with no notion that the file is a
contract about what ships.

The handoff also asks for manifests to be grouped into the contracts
cohort, which is a change to `semdiff files`' classification rather than to
any prompt — the first item-4 change with a code component.

### Details

Two parts:

1. A sixth risk-lens trigger, **packaging and dependency manifests**, named
   inline on all three surfaces that carry the triggers, with its guidance
   and worked examples in `references/risk-lenses.md`.
2. `semdiff.py` groups a manifest into `contracts` by basename, so it is
   reviewed early, as a contract, wherever in the tree it sits.

### Non-goals

- No new `category` value. A manifest defect is a `contract` finding — the
  manifest *is* a contract — so the taxonomy needs nothing added, unlike
  item 3's `description-drift`.
- No severity floor. This lens rates on the existing rubric, like the three
  non-exposure lenses.
- Not the other three lenses. Framework semantics (where benchy-cf's
  double-encoding ×3 lives), UI state lifecycle, and sibling consistency
  each ship separately, per the user's four-PR decision.

## Implementation

### The lens

`references/risk-lenses.md` gains a `## Packaging and dependency manifests`
section in the shape its five siblings already use: what to look for, then
real-finding and reflex-not-worth-reporting examples, then the severity
line. It frames the lens as four ordered questions — does a new file
actually ship; does the manifest declare what the code imports; do manifest
and lockfile agree; did a version constraint move — because the pg-pool
misses are the first two and a reviewer handed only "check the manifest"
has nowhere to start.

Three surfaces carry the trigger names inline and all three gain the sixth,
with their counts moving from five to six:
`plugins/s/skills/review/SKILL.md` (step 5b), `plugins/s/harness/bodies/review.md`
(step 7), and `plugins/s/integrations/copilot/SKILL.md` (step 5). The last
two can read no reference file, so their phrasing carries the substance
inline, as the existing five do.

`TRIGGER_PHRASES` in `test_skill_references.py` gains
`"packaging and dependency manifests"`, which is what enforces the trigger
across all three surfaces — `_missing_triggers` already checks each one
against that tuple, so no new test is needed for the inline requirement.

### The cohort change

`semdiff.py` gains a `MANIFEST_BASENAMES` frozenset and the `contracts`
rule matches `base.lower() in MANIFEST_BASENAMES` alongside its existing
`.proto` test. Basename matching is deliberate: `server/package.json` is as
much a contract as a root one, and inheriting its directory's cohort is
what scattered manifests across unrelated cohorts.

`contracts` is the first rule in `COHORT_RULES`, so it wins over `tests` —
a manifest under a test directory groups as a contract too. Pinned
deliberately in the test rather than left to chance: a fixture manifest
reviewed as a contract is reviewed early, never skipped, which is the safer
failure. The alternative, reordering the rules so `tests` wins first, would
change the cohort of every existing test-directory path for one fixture
case.

### Budget

Both prompt surfaces fit without compression: `SKILL.md` 327/330 and the
rendered harness body 134/140. Worth noting for whoever takes lens 3:
`SKILL.md` has three lines of slack left, so the next lens fits and the one
after will need headroom freed first — step 5b's six trigger bullets each
carry a clause that could reduce to a bare name, which is ~6 lines.

### Version

`plugins/s/.claude-plugin/plugin.json` bumps 0.6.257 → 0.6.258.

## Readiness attestation

### Problem and motivation

Three golden findings, rated high and medium, are manifest defects no
existing pass looks for, and manifests scatter across cohorts rather than
grouping as the contracts they are.

Evidence: benchy-cf's handoff names pg-pool's `package.json` `files`
omission of `diagnostics.js` and dependencies present in the lockfile but
not the manifest; `plugins/s/skills/review/SKILL.md` step 5b lists five
triggers, none about packaging; `plugins/s/skills/review/scripts/semdiff.py`'s
`COHORT_RULES` classified `contracts` on `.proto` alone, so
`server/package.json` fell through to its top-level directory.

### Scope and non-goals

In scope: the sixth trigger on three surfaces, its reference section, the
`TRIGGER_PHRASES` addition, the manifest cohort rule with its test, the two
spec deltas, the version bump. Out of scope: the taxonomy, any severity
floor, and the other three lenses.

### Affected capabilities and files

One capability, two requirements.

Evidence: `semantic-review` requirements `review-risk-lenses` (base
`c7d2b43a7f0b`) and `cohort-grouping` (base `520c4ddf7fa9`). Files:
`plugins/s/skills/review/references/risk-lenses.md`,
`plugins/s/skills/review/SKILL.md`,
`plugins/s/harness/bodies/review.md`,
`plugins/s/integrations/copilot/SKILL.md`,
`plugins/s/skills/review/scripts/semdiff.py`,
`plugins/s/skills/review/tests/test_semdiff_files_context.py`,
`plugins/s/skills/review/tests/test_skill_references.py`,
`plugins/s/.claude-plugin/plugin.json`. Runnable premises: applied and
measured in this worktree — 237 review tests and 3172 build tests green,
`SKILL.md` 327, rendered harness body 134 — and the classification verified
directly against `COHORT_RULES` for nine representative paths, confirming
manifests reach `contracts` while `api/routes/users.py` and
`web/components/App.tsx` keep their cohorts.

### No open task-shaping decision

- Whether the lens needs its own category: no, `contract` fits because the
  manifest is one — settled above.
- Basename versus path matching for manifests: basename, so a nested
  manifest is not demoted to its directory's cohort — settled above.
- What happens to a manifest under `tests/`: it groups as a contract, since
  `contracts` matches first; pinned in the test as a decision rather than
  left implicit — settled above.
- Whether to add a severity floor: no, it rates on the existing rubric like
  the other three non-exposure lenses.
