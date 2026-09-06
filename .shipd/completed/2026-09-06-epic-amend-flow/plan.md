# epic-amend-flow
Status: verified
Epic: epic-knowledge

## Idea

Make the epic amendment discipline real: an `/s:epic <slug> amend` mode
running over a fresh `epic-amend-<slug>` worktree, plus an `epic-amend-check`
engine verb that refuses protected-section edits before the amendment ships.

### Motivation

The capture rubric and the plan/build skills already route binding epic-scope
knowledge to "the epic's amendment discipline" (a fresh worktree, a dated
provenance stamp, a lint-gated PR), but no skill mode or engine verb
implements it — a mid-delivery Decision has no sanctioned path into a live
epic today.

### Details

- New status-CLI verb `epic-amend-check <slug> [--base <ref>]`: compares the
  working tree's `epic.md` against its content at the merge-base of `HEAD`
  and the base ref (default `main`), printing one finding per protected
  region changed; exit 4 on findings, 0 clean, 1 on errors; read-only.
- `/s:epic` gains the amend mode (`/s:epic <slug> amend`): a fresh
  `epic-amend-<slug>` worktree, rubric-routed edits to `## Decisions` and the
  shelf sections only, a dated provenance stamp on every new or extended
  Decision, the epic lint and amend-check gates, then an auto-merging PR.
- Cross-reference sweep: the capture rubric and the plan/build skills'
  binding-tier text name the mode; harness body/reference mirrors;
  `.shipd/README.md` and `AGENTS.md` document the convention.

Affected capabilities: `spec-status` (modified), `shipd-epic` (modified).
Impact: `plugins/s/skills/build/scripts/spec_status.py`,
`plugins/s/skills/build/tests/test_spec_status.py`,
`plugins/s/skills/epic/SKILL.md`,
`plugins/s/skills/epic/references/capture-rubric.md`,
`plugins/s/skills/plan/SKILL.md`, `plugins/s/skills/build/SKILL.md`,
`plugins/s/harness/bodies/epic.md`, `plugins/s/harness/references/epic.md`,
`.shipd/README.md`, `AGENTS.md`, `plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No enforcement of the provenance-stamp grammar or append-only Decisions
  inside the verb — the stamp is the flow's discipline (Q1, oracle-settled);
  the verb refuses protected-section changes only.
- No changes to member stub rows, epic status derivation, or
  `epic-sync`/`epic-set-status` — status stays the existing machinery's.
- No migration of existing epics, and no new `shipd` bin dispatch entry —
  the verb stays engine-only, exactly like `epic-sync`.
- No amendment of draft epics — a draft is edited in its authoring worktree.

## Implementation

- **Base resolution via merge-base.** The verb reads the base version with
  `git -C <root> merge-base HEAD <base>` then `git show <sha>:<relpath>`
  (relpath computed against `git rev-parse --show-toplevel`), so unrelated
  motion on `main` after the amend worktree was cut never yields false
  findings. Verified in this worktree: `git merge-base HEAD main` →
  `3fc26a6`, `git show main:.shipd/epics/epic-knowledge/epic.md` prints the
  epic. Rejected: diffing against the base tip.
- **Section model.** Both versions split on `spec_common.SECTION_HEADER_RE`
  into the pre-section header block plus level-2 sections. Amendable bodies:
  `## Decisions`, `## References`, `## Research`, `## Video` — the shelf
  family the epic says may accrete. Protected: the header block (title,
  `Status:`, `Theme:`, `Initiative:`), `## Introduction` (its subsections
  included), `## Design`, `## Changes`, `## Token usage breakdown`
  (machine-owned by `epic-sync`), and any unrecognized section. A protected
  section added or removed counts as changed. Rejected: a References-only
  shelf — the shelf change keeps legacy sections extendable in place.
- **Output and exit model mirror `check-base`** (spec-status
  check-base-verb): one `protected-section <name>` finding line each
  (`header` for the pre-section block), a trailing summary line, exit 0
  clean, exit 4 with findings, exit 1 on errors (no epic in the work tree,
  epic absent at the base — not an amendment, unresolvable base ref, not a
  git work tree). The verb never writes. Rejected: `Refused:`/exit 3 — that
  vocabulary belongs to guarded transitions; this is a findings checker.
- **Provenance grammar (flow discipline, not verb-enforced).** Each new or
  extended Decision bullet carries `*(amended YYYY-MM-DD: <one-line note>)*`;
  existing Decision text is never rewritten or deleted — a superseded
  Decision is recorded as a stamped addition under the original.
- **Amend-mode placement.** A mode gate at the top of the epic skill's flow
  (modeled on `/s:plan`'s enrichment mode): `<slug> amend` bypasses the
  authoring interview entirely. A `Status: draft` epic is refused — it is
  still being authored. The ship step follows AGENTS.md's PR workflow,
  including the semantic-review gate post and full PR URL.
- **Risk.** git absent or detached HEAD → exit 1 surfacing git's own error,
  never a traceback. A stale local base branch is acceptable: amend
  worktrees are created `--fresh` from the root checkout's HEAD.

## Questions and answers

### Q1: Does epic-amend-check enforce the Decisions stamp grammar?
- **Question:** Scope of the new `epic-amend-check` verb — (a) protected
  sections plus append-only Decisions and a dated `(amended YYYY-MM-DD)`
  stamp requirement, or (b) protected sections only, stamping left to the
  flow. Recommendation was (a).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option (b). The epic's decision assigns the responsibilities
  separately: the stamp is named as part of the flow pattern, and the verb
  is defined with exactly one refusal condition — protected sections changed
  against `main`. Widening the verb would exceed the recorded decision and
  would itself need an epic amendment or an explicit human call.
- **Cited:** epic/epic-knowledge, verified/shipd-epic
