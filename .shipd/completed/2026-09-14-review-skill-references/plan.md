# review-skill-references
Status: verified
Epic: review-rubric

## Idea

Split the `/s:review` skill body into on-demand reference files, so a review
loads only the guidance its own path needs.

### Motivation

`plugins/s/skills/review/SKILL.md` runs to 484 lines and loads in full on every
review, though its three largest sections fire only on a condition. The epic
adds four risk lenses to that file, which would make the cheapest reviews pay
for the rarest guidance.

### Details

- Move three condition-gated sections out of `SKILL.md` into a new
  `plugins/s/skills/review/references/` directory: spec-aware review, machine
  output mode, and the PR posting flow.
- Add a pointer table to `SKILL.md` naming each reference by its
  `${CLAUDE_PLUGIN_ROOT}` path beside the condition that loads it.
- Add a structure test to `plugins/s/skills/review/tests/`, which CI already
  discovers.
- Bump the plugin version so the cache snapshot picks the split up.

Affected capabilities: `semantic-review` (one added requirement). Impact:
`plugins/s/skills/review/SKILL.md`, the new
`plugins/s/skills/review/references/`, a new test under
`plugins/s/skills/review/tests/`, and
`plugins/s/.claude-plugin/plugin.json`. No new dependencies, and no engine
script changes.

### Non-goals

- No rubric substance changes. Moved text travels verbatim apart from heading
  level and cross-reference fixups.
- No move of `## Degradation`. Its probe runs on every review and its ladder is
  a failure path.
- No edit to `plugins/s/integrations/copilot/SKILL.md` or
  `plugins/s/harness/bodies/review.md`, the other two rubric surfaces.
- No `cohort` to `category` rename. That is the sibling member
  `review-finding-category`.
- No change to `semdiff.py` or `review_gate.py`.

## Implementation

- **Follow the `plan` skill's reference idiom.** `plugins/s/skills/plan/` already
  splits four references out of its `SKILL.md`, so this change copies a working
  pattern rather than inventing one. Verified by `ls
  plugins/s/skills/plan/references/`, which prints `dialogue.md emission.md
  readiness.md visualization.md`.

- **Three references, chosen by load condition rather than by size.** Each
  moved section is gated on a condition the skill can test before reading:

  | Reference | Source lines | Loads when |
  | --- | --- | --- |
  | `references/spec-aware.md` | `SKILL.md` 152–172 | a planned shipd change is in scope |
  | `references/json-output.md` | `SKILL.md` 203–272 | the user passed `--json`, or the poster's JSON is being produced |
  | `references/posting.md` | `SKILL.md` 273–411 | posting to a PR was explicitly requested |

  Rejected: moving `## Degradation` as a fourth. Its probe runs at the start of
  every review, per the `review-difft-autofix` requirement in
  `.shipd/verified/semantic-review/spec.md`, and its ladder is the failure path
  where an unread reference costs accuracy. Thirty lines does not buy that risk,
  and the three moves already clear the target.

- **The pointer table sits directly after the invocation block**, above
  `## Determine what to review`, so the reader meets it before the workflow. It
  carries two columns, `Reference` and `Load when`, and names each file by its
  full `${CLAUDE_PLUGIN_ROOT}` path.

- **Each reference opens with a level-1 title and its own load condition**, so a
  file read on its own explains why it was read. Rejected: bare section text
  moved verbatim with no header — a file that does not state its trigger invites
  loading it by default, which defeats the split.

- **`### Review stage options` travels with the posting reference.** The options
  only mean anything inside the posting flow, so splitting them from it would
  create a reference nothing reads alone.

- **The structure test is the guard against dead guidance.** A moved section
  that nothing points at is worse than an inline one, because it is invisible.
  The new test asserts both directions: `SKILL.md` names every file that exists
  under `references/`, and every path it names resolves. It also asserts the
  line ceiling and the absence of the moved headings, so a later edit cannot
  quietly inline them again. It lands in
  `plugins/s/skills/review/tests/`, which `.github/workflows/ci.yml:31` already
  discovers with `python3 -m unittest discover -s plugins/s/skills/review/tests`.

- **Version bump.** `plugins/s/.claude-plugin/plugin.json` moves from `0.6.214`
  to `0.6.215`. AGENTS.md requires the bump in the same PR, because the cache
  snapshot is keyed by version and sessions otherwise keep running the stale
  skill.

- **Risk: a reference the skill never loads.** The load conditions are written
  as testable triggers rather than as advice, and the structure test proves each
  file is reachable from `SKILL.md`. The residual risk — an agent reading the
  condition and choosing not to load — is the same risk the `plan` skill already
  carries in production.
