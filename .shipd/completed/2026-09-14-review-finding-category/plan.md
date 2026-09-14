# review-finding-category
Status: verified
Epic: review-rubric

## Idea

Rename the review finding's taxonomy field from `cohort` to `category`, bring
the second taxonomy surface back into agreement, and pin that agreement.

### Motivation

`cohort` names two different things: the architectural grouping `semdiff files`
emits, specified at `.shipd/verified/semantic-review/spec.md:83`, and the
finding taxonomy at `plugins/s/skills/review/references/json-output.md:17`. One
word for two meanings is what the shipd voice rules forbid, and the ambiguity
already hid a drift — the taxonomy's second copy at
`plugins/s/harness/references/review.md:24` sits five values behind and ships
that way to thirteen harnesses.

### Details

- Rename the finding field `cohort` to `category` at both taxonomy sites, in
  the skill prose that names a taxonomy value, in the verified requirement, and
  in the test that reads the enum.
- Backfill the harness reference's enum to match the plugin's: it lacks
  `test-coverage`, `security`, `performance`, `stability`, and
  `data-integrity`.
- Add a parity test asserting the two enums agree, so the next value added to
  one cannot silently skip the other.
- Leave every architectural use of `cohort` untouched.

Affected capabilities: `semantic-review` (one modified requirement, one added).
Impact: `plugins/s/skills/review/references/json-output.md`,
`plugins/s/harness/references/review.md`,
`plugins/s/skills/review/SKILL.md`,
`plugins/s/skills/review/tests/test_skill_references.py`, and
`plugins/s/.claude-plugin/plugin.json`. No engine script changes and no new
dependencies.

### Non-goals

- No renaming of the architectural `cohort`. It keeps the name across roughly
  twenty sites, including the `cohort-grouping` requirement, `semdiff files`
  output, and every "report by cohort" instruction.
- No use of `kind`. `semdiff diff` already spends it on a file's
  added/deleted/modified state.
- No change to `semdiff.py` or `review_gate.py`. The poster reads only
  `severity`, never the taxonomy.
- No closing of the copilot template's missing judgement passes. That gap is
  recorded on pull request 208 and belongs to its own change.

## Implementation

- **`category`, decided at the epic.** `cohort` stays architectural and `kind`
  stays the file kind, so the taxonomy needs the third word. Rejected: renaming
  the architectural grouping to `layer` instead, which would touch `semdiff.py`,
  its tests, and every "report by cohort" instruction across four surfaces to
  spare a field named in two files.

- **Five sites carry the taxonomy; everything else is architectural.** Each
  mention was classified before any edit:

  | Site | Change |
  | --- | --- |
  | `references/json-output.md:17` | field name and enum |
  | `harness/references/review.md:24` | field name, enum, and the five missing values |
  | `SKILL.md:180` | prose naming the `test-coverage` value |
  | `.shipd/verified/semantic-review/spec.md:188` | the modified requirement |
  | `tests/test_skill_references.py:322` | the line that reads the enum |

  The harness body and the copilot template use `cohort` only architecturally
  and are not touched.

- **The backfill is part of the rename, not scope creep.** Renaming a stale
  enum ships it renamed and still wrong. The staleness is drift rather than a
  declared subset: `git log -- plugins/s/harness/references/review.md` returns
  one commit, its creation in `39b57d2`, while `test-coverage` entered the
  taxonomy later in the change merged as pull request 191 and the four lens
  values in pull request 208. No note in the file declares a reduced taxonomy.

- **The reference is live, so the drift is live.** Rendering the body with the
  `file-references` feature emits the `REFS/review.md` pointer, and
  `harness_registry.HARNESSES` lists thirteen harnesses declaring that feature:
  claude-code, cursor, github-copilot, windsurf, codex, cline, roocode,
  continue, antigravity, devin, oh-my-pi, opencode, and pi. Every one of them
  currently receives the five-value enum.

- **Parity is pinned, because its absence is what caused this.** A new test
  extracts the enum values from both taxonomy sites and asserts the two sets are
  equal, failing with the symmetric difference named. This mirrors the agreement
  test `review-skill-references` added for the same class of defect: two
  surfaces stating one contract with only one end pinned. Rejected: asserting
  the harness merely contains the plugin's values, which would let the harness
  accumulate values the plugin does not accept.

- **Risk: a rename that misses a site leaves the JSON silently wrong.** The
  poster ignores the taxonomy entirely, reading only `severity`, so a stray
  `cohort` key would never raise an error — it would simply be dropped. The
  guard is a test asserting no taxonomy site still names `cohort`, which fails
  loudly where the runtime would stay quiet.

- **Version bump.** `plugins/s/.claude-plugin/plugin.json` moves to `0.6.217`,
  per the cache-snapshot rule in AGENTS.md.
