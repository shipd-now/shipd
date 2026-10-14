# review-revert-distance
Status: verified
Theme: reliability

## Idea

### Motivation

v0.6.280 added a distance condition to the further-location rule and failed its
registered criteria. It is reverted, and the idea behind it is closed rather
than deferred, because the premise was arithmetically false.

**The mechanism worked.** Near further locations — same file, within fifteen
lines of the primary — fell from 11 to 1 over three rounds, which is the
primary criterion and it passed.

**It bought nothing.** Precision moved 0.283 to 0.278 while matches per round
fell 8.7 to 5.7. That 3.0 gap sits past the ~2.3 set-to-set noise floor this
collaboration measured on a single version, so it is a real loss and not a
draw.

**And it could never have worked.** The change rested on "every further
location that matches nothing is a scored false positive", with near anchors
matching 4 of 34. The measuring session corrected that figure after the run:
v0.6.276's near anchors matched the judge **10 of 11**. They were *redundant* —
every one covered a golden finding another candidate already covered — but they
were matched. Redundant and unmatched are not the same thing, and the whole
precision case treated them as one.

ReviewBench scores each location as its own candidate. Banning a subset that
matches at 91% when overall precision is 28% removes true positives roughly
three times faster than it removes false ones, so it can only move precision
down. No wording reaches that; it is arithmetic.

### Details

The review path returns to v0.6.276, byte for byte.

### Non-goals

- **No partial keep.** The distance condition, its five scenarios and both
  ceiling raises all go. Keeping the mechanism while its justification is
  disproved is how this series spent eleven versions.
- **No retry with narrower wording.** Two failure modes were found — the
  duplicate-code case, where the reviewer dropped the whole finding rather than
  anchor one site, and residual undecidability of "block or table" in Markdown
  and extension-less files — but neither is why this is reverted. Fixing both
  would still leave a change that cannot raise precision.
- **No change to `references/risk-lenses.md`**, whose "Five triggers, four
  lenses" miscount remains open. It is a live suspect for a separate question
  and belongs in its own version with its own round set.
- **Nothing from v0.6.277, v0.6.278 or v0.6.279 is touched.** Those are the
  copilot capability, the conflict-marker lint and a spec-and-docs change; none
  is on the `/s:review` prompt path.

## Implementation

`plugins/s/skills/review/SKILL.md` and `plugins/s/harness/bodies/review.md` are
restored from `c677745`, which carries v0.6.276's prompt byte for byte —
v0.6.277 and v0.6.278 touched neither file. Verified: the diff against
`428e80b`, the v0.6.276 merge, is empty on both.

`DistanceConditionParityTest` is removed with the rule it pinned. Both ceilings
return to the figures that fit the restored content: `SKILL.md` to 336 under
340, the worst rendered harness body to 145 under 150.

Each ceiling test's docstring records the arithmetic rather than only the
number, so the next reader finds out why the idea is closed and does not
re-derive it. The measuring discipline the last raise added is kept verbatim:
measure the figure, never add to the last number written in the docstring —
the 332 recorded there went stale the moment v0.6.276 added four lines.

### What survives from the attempt, and is worth keeping

Three facts the run established, none of which depend on the change staying:

- Near anchors are **redundant, not false**. That kills this idea and any
  variant of it.
- Faced with a prohibition it cannot satisfy, the reviewer **drops the
  finding** rather than reporting it with fewer anchors. `chronicle #12`
  anchored at `files.rs:5→10` under v0.6.276 and vanished entirely under
  v0.6.280. That is a general caution about adding prohibitions to this
  prompt, and it cost a whole finding.
- The packaging risk lens **went silent**: zero rounds mentioned `npm pack` or
  tarballs against two of three at v0.6.276, and the `package.json`
  files-allowlist finding disappeared rather than losing an anchor. There is no
  grounded explanation for that and this change does not offer one. It is the
  sharpest unexplained result in the data, and it is recorded rather than
  theorised about.

### Version

`plugins/s/.claude-plugin/plugin.json` bumps 0.6.280 → 0.6.281.

## Readiness attestation

### Problem and motivation

The shipped review prompt carries a rule that costs recall past the noise floor
and cannot deliver the precision gain that justified it.

Evidence from three rounds on chronicle, CrabTrap and node-postgres with
`--pr-context`, all nine transcripts loading 0.6.280: near further locations
11 → 1; precision 0.283 → 0.278; matches per round 8.7 → 5.7 against a ~2.3
noise floor; locations per finding 1.84 → 1.39; keep-check `#23` 2/3 → 0/3 with
the packaging finding absent and packaging never investigated; guard 5 losses
against an allowance of 2, 0 gains; severity targets held at medium 3/3. And
the corrected figure that settles it: v0.6.276's near anchors matched 10 of 11
with unique coverage 0.

### Scope and non-goals

In scope: the two prompt surfaces, the test class that pinned the rule, both
ceiling figures in their owning requirements and their enforcing tests, the
version bump.

Out of scope: `references/risk-lenses.md`, every file outside the `/s:review`
path, and any narrower retry of the distance idea.

### Affected capabilities and files

Two capabilities, three requirements, hashes from `spec_status.py base-hash`
here: `semantic-review`/`review-skill` (`66008b1edd4d`),
`semantic-review`/`review-skill-references` (`4e3f894627a6`),
`harness-command-bodies`/`body-content` (`1a580072d524`).

Files: `plugins/s/skills/review/SKILL.md`,
`plugins/s/harness/bodies/review.md`,
`plugins/s/skills/review/tests/test_skill_references.py`,
`plugins/s/skills/build/tests/test_harness_bodies.py`,
`plugins/s/.claude-plugin/plugin.json`.

Runnable premises measured here: both prompt files restored from `c677745`
diff empty against `428e80b`; `SKILL.md` is 336 lines; the worst rendered
harness body is 145, measured by rendering every registered harness.

### No open task-shaping decision

- Revert or retry with narrower wording: revert, because the premise is
  arithmetically false and no wording reaches arithmetic — settled above with
  the 91%-against-28% calculation.
- Whether to keep the mechanism and drop only the justification: no — settled
  above as the error that cost this series eleven versions.
- Which state to restore: `c677745`'s, verified byte-identical to v0.6.276's
  prompt — settled above.
- Both ceilings: back to 340 and 150, the smallest round figures above the
  restored 336 and 145 — settled above.
