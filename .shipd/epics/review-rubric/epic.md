# review-rubric
Status: active
Theme: developer-experience

## Introduction

`/s:review` judges correctness well and judges little else. Its rubric chases
changed signatures to their call sites, traces the values those sites pass, and
compares uneven sibling implementations. It names no security lens, no
performance lens, no stability lens, and no data-integrity lens. A public
methodology from a widely used review tool covers six dimensions; ours covers
two of them.

Three further defects compound that gap. The review runs no linter over the
changed code, so it reasons out by hand what a static check settles for free.
The gate re-reviews every push in full, so a finding the author already
dismissed returns identically. And the skill calls two different things a
`cohort` — the architectural grouping and the finding taxonomy — which our own
voice rules forbid.

The skill file has meanwhile reached 484 lines, every one of them loaded on
every invocation. Adding four lenses to a file already loaded in full makes the
cheapest reviews pay for the rarest guidance.

This epic closes the four rubric gaps and converts the skill to load its parts
on demand. A review afterwards names a leaked secret, an unbounded loop, a
leaked connection, and an irreversible migration. It reads the repo's own
linter output. It stops repeating findings a human already answered. And one
word carries one meaning.

Success criteria: a review over a diff carrying a planted secret, an unbounded
query, and a down-migration-free schema change reports all three; a second gate
review of an unchanged, dismissed finding does not re-post it; `SKILL.md` drops
below 300 lines with no rubric substance lost.

### Non-goals

- Adopting a five-tier severity scale. Three tiers map onto the blocking rule,
  and splitting `low` changes no decision.
- Adding a hosted service, a network call, or a third-party dependency to the
  review path.
- Auto-fixing findings. The review stays read-only.
- Changing the gate's posting, disposition, or auto-reply semantics.
- Restructuring the `diff`, `files`, or `context` subcommands.

## Decisions

- **Two rubric surfaces, one substance.** The rubric lives in two files: the
  plugin skill at `plugins/s/skills/review/SKILL.md`, and the vendored template
  at `plugins/s/integrations/copilot/SKILL.md`. `shipd copilot add` installs the
  template plus `semdiff.py` into a user repo, where a GitHub Actions runner
  executes it. That runner has no `${CLAUDE_PLUGIN_ROOT}` and no reference
  files. Every member that changes rubric substance updates both surfaces, and
  the template keeps its substance inline.

  Three surfaces, not two. `plugins/s/harness/bodies/review.md` is the third — a
  distilled command body that the `review-skill` requirement in
  `.shipd/verified/semantic-review/spec.md` binds to the same judgement passes
  as the skill, so the two cannot drift. Which surfaces a member touches now
  follows from what it changes: a member that changes a judgement pass updates
  all three, and a member that changes only the `--json` finding shape updates
  the plugin alone, because neither the harness body nor the copilot template
  carries that shape. The copilot template's JSON array holds `severity`,
  `path`, `start_line`, `end_line`, `detail` and `replacement`, and no taxonomy
  field at all.
  *(amended 2026-09-14: corrected the surface count from two to three, after the
  harness body surfaced while building `review-skill-references`.)*
- **A reference states its whole trigger.** A member that moves guidance behind a
  load condition writes that condition in full at the pointer, never only inside
  the file the condition gates. A pointer that under-states its trigger makes the
  guidance unreachable, because the reader who needs it never learns it applies.
  The agreement test at
  `plugins/s/skills/review/tests/test_skill_references.py` pins every pointer
  against its reference's own condition sentence; a member that adds a reference
  extends that test rather than working around it.
  *(amended 2026-09-14: added after the spec-aware pointer shipped half its
  trigger in `review-skill-references` and the review gate caught it.)*
- **Progressive disclosure binds the plugin skill only.** Follow the existing
  `plugins/s/skills/plan/references/` idiom. `SKILL.md` names each reference by
  its `${CLAUDE_PLUGIN_ROOT}` path and states the condition that loads it. The
  agent reads a reference when its condition fires, never by default.
- **Severity stays three tiers.** `high` and `medium` block; `low` never does.
  A reviewer unsure between two tiers states the doubt rather than inflating.
- **The finding taxonomy field is `category`.** `cohort` keeps its one meaning —
  the architectural grouping `semdiff files` emits. `kind` keeps its one
  meaning — the file kind `added`, `deleted`, or `modified` that `semdiff diff`
  emits. No member introduces a third use of either word.
- **`semdiff.py` stays one dependency-free file.** The CLI vendors it
  byte-identical, so no member adds a third-party import or a sibling module.
- **A vendored change marks installs stale, and that is the designed path.**
  Editing `semdiff.py` or the template flips existing gate installs to `stale`.
  `/s:gate update` refreshes them. No member alters that mechanism or tries to
  avoid the staleness.
- **Linter discovery detects first and reads config second.** `semdiff lint`
  infers linters from repo files. `.shipd-config.json` overrides the detection
  or disables a linter. A repo that configures nothing still gets a working
  check.
- **Incremental review applies to gate mode only.** Prior findings are read
  back from the PR's posted threads, which `review_gate.py` already parses over
  GraphQL. No member adds a local cache. A pre-push `/s:review` stays stateless.
- **Linters run in check mode.** No member passes a fix or write flag to a
  detected linter. The review never edits the repo.

## Design

The epic works on three layers, and the members follow them.

**The skill text.** `SKILL.md` today mixes the hot path with the cold. Steps 1
through 7 and the severity rubric run on every review. The `--json` shape, the
`suggestion` contract, the posting flow, the stage options, and the degradation
ladder run rarely. The split moves each cold region into
`plugins/s/skills/review/references/`, leaving `SKILL.md` as the workflow plus
the pointers. The new risk lenses land in that structure as their own reference,
loaded when a diff touches the cohort each lens guards.

**The engine.** `semdiff.py` gains one subcommand, `lint`. It detects the
repo's linters, runs them over the changed paths only, and emits findings in
the same JSON envelope the other subcommands use. Detection reads the repo's
own files; `.shipd-config.json` overrides it.

**The gate.** `review_gate.py` already reads back posted threads with their
severity and resolution state. Incremental review consumes that readback:
before reporting, the review matches its findings against the threads already
posted, and suppresses a match a human dismissed.

The seams follow the dependency order. The scaffold lands first so the later
rubric text has somewhere to go. The rename lands second so the lenses are
written once, in the final vocabulary. The lenses land third. The engine and
gate members are independent of the text members and of each other.

## Changes

| Change | Description | Code | Integration | Unknowns | Risk |
| --- | --- | --- | --- | --- | --- |
| review-skill-references | Split the plugin SKILL.md into on-demand reference files and state each load condition | low | low | medium | medium |
| review-finding-category | Rename the finding taxonomy field from `cohort` to `category` across both rubric surfaces, the spec, and the tests | low | medium | low | low |
| review-risk-lenses | Add security, performance, stability, and data-integrity lenses as a loaded reference, inline in the vendored template | low | medium | medium | medium |
| review-static-analysis | Add the `semdiff lint` subcommand with linter auto-detection and config override | high | medium | medium | medium |
| review-incremental | Suppress gate findings already posted and dismissed, read back from the PR's threads | medium | high | high | high |

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 442 | 137.7k |
| Edit | 29 | 30.1k |
| (no tool) | 0 | 23.3k |
| Write | 8 | 14.8k |
| Read | 51 | 10.4k |
| Agent | 12 | 6.3k |
| ToolSearch | 9 | 2.6k |
| AskUserQuestion | 2 | 2.4k |
| SendMessage | 2 | 1.3k |
| Monitor | 4 | 1.1k |
| WebFetch | 1 | 142 |
| **Total** | 560 | 230.2k |
