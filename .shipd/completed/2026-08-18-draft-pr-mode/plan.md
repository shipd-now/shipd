# draft-pr-mode
Status: verified

## Idea

Add a workspace-settable `pr-mode` configuration key that makes change-shipping
flows open draft PRs without auto-merge, so humans review and merge.

### Motivation

Every change ships as an auto-merging PR (`ship-changes-as-prs`,
`build/SKILL.md`) with no configuration surface to soften that policy, so a
workspace whose norms require human review and merge cannot adopt the
delivery flows. Layered config already lets a workspace root's
`.shipd-config.json` govern every member repo, making a workspace-level
setting the natural surface.

### Details

- New layered config key `pr-mode`: `auto` (default, today's behavior) or
  `draft`, plus a stdlib-only `resolve_pr_mode(root)` accessor.
- Build ship phase in draft mode: `gh pr create --fill --draft`, no
  auto-merge arming, no merge watch or close-out; the semantic-review gate
  posting is unchanged; the report ends on the draft PR URL.
- Autopilot: a member completing its pipeline with an open unmerged PR under
  draft mode records a new `drafted` terminal outcome with its own report
  bucket, instead of parking as needs-human.

Affected capabilities: `shipd-config` (added), `build-spec-lifecycle`
(modified), `epic-autopilot` (modified). Impact:
`plugins/s/skills/build/scripts/spec_common.py`,
`plugins/s/skills/build/scripts/autopilot.py`,
`plugins/s/skills/build/SKILL.md`, `README.md`, engine tests, plugin version
bump.

### Non-goals

- Metadata PRs (epic-close status derivations, initiative-set tagging) keep
  auto-merging regardless of the mode (user decision Q2).
- No change to `worktree.sh`'s static next-steps hint text — it is advisory
  prose, and reading JSON config from bash is not worth the coupling.
- No pipeline-entry option for draft mode: the key is standalone config, not
  part of `autonomous-pipeline`.
- No review-gate behavior change: draft mode leaves posting and disposition
  exactly as the pipeline's review entry declares.

## Implementation

- **Standalone layered key, not a pipeline stage option.** A pipeline option
  would force any workspace wanting drafts to declare a wholesale
  `autonomous-pipeline` and install pydantic (`pipeline-entry-validation`
  fails closed without it). A top-level key rides the existing
  nearest-wins-wholesale merge, stays stdlib-only, and composes with any
  pipeline. Rejected: `BuildStep` option in `pipeline_schema.py`.
- **Accessor shape.** `PR_MODE_KEY = "pr-mode"` and `resolve_pr_mode(root)`
  in `spec_common.py` beside `resolve_pipeline`: returns `"auto"` when
  undeclared, the declared value when `auto`/`draft`, and raises
  `ConfigError` naming `pr-mode` and the accepted values otherwise — the
  `clone_sources` validation pattern.
- **Skill read surface.** Verified by running `spec_status.py config-show`:
  it prints every declared key generically as `<key> = <json> [<source>]`
  (observed `valid_themes = [...] [/…/.shipd-config.json]`, exit 0), so
  `pr-mode` surfaces there with no new verb. The build skill reads the mode
  from that line; a value other than `auto`/`draft` stops the ship step with
  an error naming `pr-mode`.
- **Autopilot wiring.** Resolve the mode once per run in `drive_epic` and the
  targeted drive, thread it to `drive_member`. Terminal PR check
  (`autopilot.py` end of `drive_member`): draft mode + existing unmerged PR →
  `MemberResult(outcome="drafted", pr_url=url)`; no PR still parks
  needs-human at `merge`; the vanished-worktree path is unchanged in every
  mode. Report dicts gain a `drafted": []` bucket (both assembly loops),
  `_summarize` renders `drafted:` lines with URLs, and `any_merged` — hence
  the epic-sync close-out — keys off actual merges only. The build stage
  prompt in `_stage_prompt` names the draft-PR ship instead of "auto-merging
  PR" when the mode is draft.
- **Docs.** README's configuration section documents the key alongside
  `autonomous-pipeline`; `plugins/s/.claude-plugin/plugin.json` bumps to the
  next patch version in the same PR (plugin cache is version-keyed).
- **Risk: parallel drafts diverge.** Draft-mode autopilot members all branch
  from the same `main` (nothing merges between members), so overlapping
  members can conflict at human merge time. Accepted consequence of the
  policy; the `drafted` report bucket keeps every open PR visible.
- **Risk: worktrees accumulate.** Draft mode leaves worktrees in place until
  humans merge; the guarded `worktree.sh remove` already refuses while work
  is unmerged, so cleanup stays safe and manual.

## Questions and answers

### Q1: How does autopilot treat a draft-mode member ending with an open draft PR?
- **Question:** Under `pr-mode: draft`, how should the epic autopilot treat a
  member whose pipeline completes with an open draft PR? Options: (a) a
  distinct `drafted` terminal outcome with its own report bucket; (b) park as
  needs-human with a draft-specific reason; (c) leave autopilot out of scope.
  Recommendation: (a).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option (a) — record the member `drafted` with its PR URL in a
  dedicated report bucket, so an expected draft is never reported as a
  needs-human failure. The oracle noted the existing parking rationale is
  premised on auto-merge being armed, which draft mode makes false.
- **Queued:** none (no discoverable workspace)

### Q2: Which PR-opening flows does draft mode govern?
- **Question:** Should `pr-mode: draft` govern every PR any shipd flow opens,
  or only change-shipping build PRs? Options: (a) only change-shipping PRs —
  build ship phase and autopilot members; (b) every PR including epic-close
  and initiative-set metadata PRs. Recommendation: (a).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option (a) — change-shipping PRs only; metadata PRs (epic-close
  derivations, initiative tagging) keep auto-merging.
- **Queued:** none (no discoverable workspace)
