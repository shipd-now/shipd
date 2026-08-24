# shipd-gate

### Requirement: Gate setup skill flow
id: gate-skill-flow

A `/s:gate` skill SHALL set up the shipd semantic review gate in a
repository, in this order. It SHALL announce the running plugin version in
its first user-visible status sentence, then preflight: the working
directory MUST be a git repository resolving a GitHub remote, and `gh` MUST
be present and authenticated — when any of these fail the skill SHALL report
what is missing (handing `gh auth login` to the user, never running it) and
stop. It SHALL then run `shipd copilot add` — resolving the binary as
`shipd` on PATH first, else `${CLAUDE_PLUGIN_ROOT}/bin/shipd` — and relay
the verb's own report. It SHALL propose committing and pushing the four
installed files on the current branch; if the push is rejected, it SHALL
fall back to a `shipd-gate-install` branch shipped as an auto-merging PR
and say so. It SHALL then collect explicit consent in a single batched
selection honoring the dialog-prose separation rule over exactly these
runnable steps: requiring the `semantic-review` check via
`review_gate.py protect`; enabling repository auto-merge via
`gh api -X PATCH repos/<nwo> -F allow_auto_merge=true`, this option omitted
with a note when the layered configuration resolves `pr-mode: draft`; and
optionally setting the repository Actions variable `SHIPD_GATE_FAIL_OPEN` to
`false`, its option stating the trade-off that a marker-less review then
leaves the required check pending. Only consented steps SHALL run, and a
step's API denial SHALL be reported with a manual hint without blocking the
other consented steps. The skill SHALL relay the minimal-PAT reviewer-token
recipe from `docs/copilot-review.md` and hand the storage step to the user
as `! gh secret set COPILOT_GITHUB_TOKEN`, never running it; where the user
skips the token, the skill SHALL state that the gate remains fail-open
advisory until the secret exists. The skill SHALL close by running
`shipd doctor` and reporting the `protection`, `automerge`, and
`copilot-secret` lines as the verification of what was set up and what
remains.

#### Scenario: Consent precedes every mutation
- **WHEN** the flow reaches the batched selection and the user consents to a
  subset of the runnable steps
- **THEN** only the consented steps run, and the closing `shipd doctor`
  report still runs

#### Scenario: Declining runs nothing
- **WHEN** the user declines every runnable step
- **THEN** no protection write, no repository PATCH, and no variable set is
  performed, and the skill ends with the doctor lines and the manual hints

#### Scenario: Draft pr-mode omits the auto-merge option
- **WHEN** the layered configuration resolves `pr-mode: draft`
- **THEN** the consent selection carries no auto-merge option and the skill
  notes that the draft flow never arms auto-merge

#### Scenario: Unauthenticated gh stops at preflight
- **WHEN** `gh` is absent or `gh auth status` fails
- **THEN** the skill reports the missing prerequisite with its hand-off and
  runs no install and no mutation

#### Scenario: Skipped token is named advisory
- **WHEN** the user does not complete the `COPILOT_GITHUB_TOKEN` hand-off
- **THEN** the skill's closing report states the gate stays fail-open
  advisory until the secret exists

### Requirement: Gate skill registration
id: gate-skill-registration

The skill SHALL live at `plugins/s/skills/gate/SKILL.md` with `name` and
`description` frontmatter whose description carries the `/s:gate`
trigger, SHALL carry the question-rejection recovery rule, and SHALL be
listed in the repository `README.md` skills table and in `AGENTS.md`'s
skill enumeration. A body template SHALL exist at
`plugins/s/harness/bodies/gate.md` opening with a
`<!-- description: … -->` marker, so the bodies/skills id-set equality the
harness-command-bodies capability enforces holds.

#### Scenario: Skill is discoverable and documented
- **WHEN** the plugin's skills and the README table are compared
- **THEN** `gate` appears in both, with `/s:gate` as its invocation

#### Scenario: Body template keeps the id-set equality
- **WHEN** the bodies directory listing is compared to the skills directory
  listing
- **THEN** `gate` appears in both sets

#### Scenario: Recovery rule is carried
- **WHEN** `plugins/s/skills/gate/SKILL.md` is inspected
- **THEN** it contains the question-rejection recovery rule

### Requirement: Gate update flow
id: gate-update-flow

When invoked with the argument `update`, the `/s:gate` skill SHALL run a
refresh-only flow in the current repository: announce the running plugin
version, run the same three preflight checks as setup (a git repository,
`gh` authenticated, a GitHub remote — stopping with the hand-off on any
failure), and read the per-file managed states from the bare `shipd copilot`
report. Where all four managed files are `installed` at the running version,
the skill SHALL report the repository as already current and stop without
writing, committing, or pushing. Otherwise it SHALL refresh with
`shipd copilot add` — refusing when the verb reports a foreign managed path,
never passing `--force` on its own judgment — commit exactly the four
managed paths, and push the current branch without a further consent round,
the invocation itself being the consent for this scoped refresh. Where the
push is rejected, the skill SHALL fall back to a `shipd-gate-update` branch
shipped as a pull request, attempt to arm auto-merge on it, and report the
full pull-request URL, stating that the pull request awaits a human merge
where arming is rejected. The update flow SHALL touch no repository
setting — no branch-protection write, no auto-merge PATCH, no Actions
variable, no secret hand-off — and SHALL close by relaying the verb's
post-refresh per-file state lines.

#### Scenario: An already-current repository is untouched
- **WHEN** `/s:gate update` runs and the bare report shows all four managed
  files `installed` at the running plugin version
- **THEN** the skill reports the repository as current and performs no
  write, no commit, and no push

#### Scenario: Stale files are refreshed and shipped
- **WHEN** any managed file is `stale` or `absent`
- **THEN** the skill runs `shipd copilot add`, commits the four managed
  paths, pushes, and closes with the post-refresh state lines

#### Scenario: A rejected push becomes an auto-merging pull request
- **WHEN** the push is rejected
- **THEN** the refresh ships from a `shipd-gate-update` branch as a pull
  request with auto-merge attempted, and the report carries the full
  pull-request URL

#### Scenario: A foreign file still refuses
- **WHEN** the verb reports a managed path as foreign
- **THEN** the update flow stops without `--force`, naming the file

#### Scenario: No repository setting is touched
- **WHEN** the update flow completes on any path
- **THEN** no branch-protection write, no auto-merge PATCH, no variable
  set, and no secret storage has been performed
