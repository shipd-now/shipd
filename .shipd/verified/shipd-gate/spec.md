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
