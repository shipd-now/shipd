## REMOVED Requirements

### Requirement: Related-file context subcommand
id: related-context
base: 2b52c172e564
Reason: Nothing consumes it. The `/s:review` step that called `semdiff related` was removed in v0.6.275's revert, and no prompt surface has named the subcommand since — verified across `SKILL.md`, the harness body and all eight reference files. Its one measurement was unattributable: on the two PRs it ran against it scored 22.0 where v0.6.260 scored 21.7, and it never received a three-PR set. So 446 lines of engine and 675 lines of tests sat reachable only by hand-typing a subcommand no instruction mentions.
Migration: None. No caller exists to migrate. Cohort classification keeps `_is_manifest` and its two manifest constants, which `COHORT_RULES` uses for the `contracts` cohort, and `cmd_context` keeps `_grep_matches` — both verified live before removal. `git` history holds the implementation if a later change wants it back, and this requirement's text with it.
