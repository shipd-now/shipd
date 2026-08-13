# lean-format-drift
Status: verified

## Idea

The lean-spec-format cutover left "old format" residue in live files: the plan
skill still calls its output "the full-ceremony artifacts" (frontmatter
description and body), the README's `/s:plan` catalog row says the same, the
build skill's Phase 2 heading leans on the retired "full ceremony" phrase,
`build_report.py` comments cite a `design.md` that now lives only in the
archive, the `shipd-plan` capability still carries the stale requirement id
`silent-full-ceremony-emission`, two `project-readme` requirements reference
`design.md` and "full-ceremony change artifacts", and the git-tracked
`.claude/commands/opsx/` directory still ships the four retired bootstrap-era
OpenSpec commands (explore/propose/apply/archive) that teach the old
proposal.md/design.md workflow.

This change sweeps all of it onto the lean-format vocabulary and removes the
retired opsx commands. Frozen archives (`am/spec/changes/archive/`,
`openspec/`) stay untouched.

Capabilities modified: `shipd-plan` (requirement id renamed to
`silent-lean-emission`), `project-readme` (two terminology-only requirement
rewrites).

## Implementation

- **Wording:** "full-ceremony artifacts" → "lean `am/spec` artifacts
  (`plan.md`, delta specs, `tasks.md`)" in the plan skill and README row. The
  build skill's Phase 2 principle keeps its meaning (never skip the spec
  workflow) but is rephrased to "The full spec workflow below always runs" so
  "ceremony" no longer names the artifact set.
- **Requirement id rename via the RENAMED delta op** — `FROM:
  silent-full-ceremony-emission TO: silent-lean-emission` in the `shipd-plan`
  delta; the merge engine re-keys the master. First real use of the rename
  path.
- **`project-readme` deltas:** the banner scenario drops "exactly as fixed in
  `design.md`" (that design lives only in the archive); the spec-engine
  requirement says "lean change artifacts (`plan.md`, `tasks.md`, delta
  specs)" instead of "full-ceremony change artifacts".
- **`build_report.py`:** comment-only edits — the two "per design.md …" cites
  become "per the archived build-report design …" so they stop pointing at a
  file that no longer exists in the change dir.
- **opsx removal:** `git rm -r .claude/commands/opsx/` — completes the
  bootstrap-skill retirement started in commit 066e23d; the OpenSpec CLI and
  its workflow are already dead here.
- **Snapshot discipline:** `plugins/s/` is edited, so bump
  `plugins/s/.claude-plugin/plugin.json` to `0.1.3` and refresh the snapshot
  (cache is version-keyed).
- **Risk:** near-zero — docs, comments, and deletions of unused commands; the
  only engine-visible change is the id re-key, which the merge engine owns.
