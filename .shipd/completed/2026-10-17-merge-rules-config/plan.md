# merge-rules-config
Status: verified
Epic: merge-rules
Planned-at: d77b207225bc087d35f8ad6aa8de52c77cab6cee
Gated-hash: b8044e8ea3f4

## Idea

Add a `merge` config key with a typed resolver, and a `shipd gate rules` verb family that maps it onto one shipd-owned GitHub ruleset.

### Motivation

Repository owners cannot make GitHub require approvals from someone other than the author, because shipd has no place to declare merge rules and no way to apply them; the live ruleset on unkannybanny requires zero approvals. Every later member of the merge-rules epic (doctor drift, the test rerun) is judged against this key and this ruleset.

### Details

- `merge` config key and `resolve_merge(root)` in `spec_common.py`; registered, documented in the config example and `docs/customise.md`.
- New stdlib module `merge_rules.py` building the ruleset body, diffing it against the live ruleset, and creating or updating it.
- `shipd gate rules` (report) and `shipd gate rules apply` in `plugins/s/bin/shipd`; `/s:gate` gains a consent row for apply.
- Plugin version bump, one patch above `main` at build time.

Affected capabilities: `shipd-config` (added), `shipd-cli` (modified, added), `shipd-gate` (added).

### Non-goals

- No doctor drift check, no approval event change, no identity work: other members.
- No edit of any ruleset other than `shipd merge rules`, no classic branch protection writes.
- No merge-method, bypass, or code-owner settings in config.

## Implementation

- **Config.** `MERGE_KEY = "merge"`, `DEFAULT_MERGE`, and `resolve_merge(root)` follow `resolve_room`: `resolve_config`, error text naming `merge`, member, and source file. `approvals` is an int 0 to 10 (bool rejected); booleans must be real bools; `required_checks` is a list of distinct non-empty strings (empty allowed). An unknown member raises `ConfigError`: a typo such as `approvls` would otherwise silently weaken a security rule. Rejected: ignoring unknown members as `room` does. Add `"merge"` to `RECOGNIZED_CONFIG_KEYS` after `memory_dir`.
- **Engine module** `plugins/s/skills/build/scripts/merge_rules.py`, stdlib plus `spec_common`. Interface: `RULESET_NAME = "shipd merge rules"`; `gh_run(args, stdin=None, cwd=None) -> (code, out, err)` (real, 30 s timeout); `desired_ruleset(merge) -> dict`; `live_members(detail) -> dict` (reads the six members back out of a ruleset detail); `diff(merge, detail) -> [(member, live, wanted)]` in fixed member order, `required_checks` compared as sorted lists, plus `enforcement`, `target`, and ref-include members; `find_owned(nwo, run)`; `show(...)`, `apply(...)`, and `main(argv, run=gh_run, out=print)` returning an exit code. `doctor-ruleset-drift` reuses `find_owned`, `live_members`, and `diff` unchanged.
- **Ruleset body** (shape observed on `gh api repos/mikkel-bergmann/unkannybanny/rulesets/25150897`): `name`, `target: "branch"`, `enforcement: "active"`, `conditions.ref_name {include: ["~DEFAULT_BRANCH"], exclude: []}`, `bypass_actors: []`, a `pull_request` rule with `required_approving_review_count`, `dismiss_stale_reviews_on_push`, `require_last_push_approval`, `required_review_thread_resolution`, `require_code_owner_review: false`; and a `required_status_checks` rule with `required_status_checks: [{"context": c}]` and `strict_required_status_checks_policy`, omitted when the list is empty. Read-only response fields (`required_reviewers`, `require_extra_approval_for_unattributed_changes`) are not sent.
- **Finding the ruleset.** List `repos/<nwo>/rulesets?includes_parents=false&per_page=100` (list items carry no rules, observed), keep `source_type == "Repository"` items named exactly `shipd merge rules`; zero means create (POST), one means GET its detail then PUT `repos/<nwo>/rulesets/<id>`, more than one is an error. Other rulesets are never fetched or written. Writes pass the JSON body on stdin to `gh api -X POST|PUT ... --input -`. Rulesets stack with the existing `main` ruleset and the strictest wins, so apply cannot loosen it.
- **CLI.** `cmd_gate(args)` in `plugins/s/bin/shipd`, dispatched in `main` beside `copilot`, loads `merge_rules` lazily (like `_load_registry`) and accepts only `rules [apply] [--repo OWNER/NAME] [--root DIR]`; anything else prints usage and exits `2`. Add `gate` to `USAGE`, to the docstring's verb notes, and to the test `VERBS` tuple. The repository comes from `--repo` else `gh repo view --json nameWithOwner -q .nameWithOwner` run in `--root`.
- **Output.** Report: a header line, then one line per member `approvals: config 2, live 0 (differs)`. Apply: `created ruleset ... (id N)` or `updated ...`, then `member: live -> wanted` lines; no drift prints `nothing written`.
- **Skill.** `plugins/s/skills/gate/SKILL.md` step 5 table gains the apply row (preview first with bare `shipd gate rules`), step 6 admin note covers it, update flow unchanged.
- **Tests.** `test_merge_rules.py` uses a recording fake runner (no real GitHub); `ResolveMergeTest` in `test_spec_common.py`; the config-sample and customise-guide guards cover registration.
- Risks: GitHub rejecting a body field (guard: body mirrors the observed live shape); a 403 for non-admins (reported, exit 1).

## Questions and answers

### Q1: Pin allowed merge methods in the shipd ruleset?
- **Question:** Should the applied ruleset pin `allowed_merge_methods`? Options: (1) omit it, the shipd ruleset covers approvals and checks only; (2) pin squash; (3) add a `merge.merge_methods` member. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Omit it, option 1. The epic scopes the ruleset to the `pull_request` approvals and status checks, and the existing `main` ruleset already owns merge methods, so a second source could conflict.
- **Queued:** none
- **Relied on by:** doctor-ruleset-drift

### Q2: Bypass actors on the shipd ruleset?
- **Question:** Should `bypass_actors` be empty or include a repository-admin bypass? Options: (1) empty, nobody bypasses; (2) admin bypass in pull_request mode; (3) a `merge.bypass` member. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Empty, option 1. It matches the live `main` ruleset, which reports no bypass, and a rule that admins can skip is not an enforced rule.
- **Queued:** q-merge-rules-ruleset-bypass-actors
- **Relied on by:** team-merge-test

### Q3: Dry-run flag on apply?
- **Question:** Should `apply` take `--dry-run`? Options: (1) no, the bare verb is the preview; (2) add `--dry-run`. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** No flag, option 1. The bare verb already prints config beside the live ruleset without writing, and `/s:gate` takes consent before apply runs.
- **Queued:** q-gate-rules-apply-dry-run

## Readiness attestation

### Problem and motivation

Merge rules have no declared home and the live ruleset requires zero approvals, so nobody can make GitHub require a second identity.

Evidence:

- Live ruleset 25150897 on unkannybanny: `required_approving_review_count` 0, `dismiss_stale_reviews_on_push` false.
- Epic `merge-rules` Decisions "Rules live in config" and "One ruleset, owned by shipd".

### Scope and non-goals

The change covers the config key, the ruleset verbs, and one consent row; drift checks, approval events, and identity belong to other members.

Evidence:

- Epic member table rows `doctor-ruleset-drift`, `gate-approves`, `agent-identity`.
- Out of scope: `plugins/s/skills/review/scripts/review_gate.py` is not edited.

### Affected capabilities and files

Three capabilities and six files are affected, because the key, the engine module, the dispatcher, the skill, the docs and the version each need one edit.

Evidence:

- Capabilities: `shipd-config` (new `merge-config-key`), `shipd-cli` (`cli-dispatch` base 4fc8f276b9ac, new `gate-rules-verb`), `shipd-gate` (new `gate-rules-consent`).
- Files: `plugins/s/skills/build/scripts/spec_common.py` (`RECOGNIZED_CONFIG_KEYS`, `resolve_room`), `plugins/s/skills/build/scripts/merge_rules.py` (new), `plugins/s/bin/shipd` (`cmd_copilot`, `main`, `USAGE`), `plugins/s/skills/gate/SKILL.md`, `plugins/s/skills/build/references/shipd.config.example.json`, `docs/customise.md`, `plugins/s/.claude-plugin/plugin.json`.
- Runnable premise: `gh api repos/mikkel-bergmann/unkannybanny/rulesets` exited 0 and printed one summary item without `rules`.
- Runnable premise: `gh api repos/mikkel-bergmann/unkannybanny/rulesets/25150897` exited 0 and printed the `pull_request` and `required_status_checks` parameters used above.
- Runnable premise: `gh api 'repos/mikkel-bergmann/unkannybanny/rulesets?includes_parents=false'` exited 0 and printed the same list.

### No open task-shaping decision

Every decision is settled; none remain.

Evidence:

- Merge methods (omit): Q1, planner default after an insufficient oracle verdict.
- Bypass actors (empty): Q2, planner default.
- Dry-run flag (none): Q3, planner default.
- Module placement, unknown-member rejection, ruleset lookup, and output shape: settled by investigation of `resolve_room` and `cmd_copilot`.
