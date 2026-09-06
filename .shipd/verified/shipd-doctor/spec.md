# shipd-doctor

### Requirement: Doctor skill flow
id: doctor-skill-flow

A `/s:doctor` skill SHALL run the read-only `shipd doctor` preflight —
resolving the binary as `shipd` on PATH first, else
`${CLAUDE_PLUGIN_ROOT}/bin/shipd` — and parse its spec'd
`ok|warn|fail <check> — <detail>` lines. When every check is `ok`, the
skill SHALL report the healthy result and stop. Otherwise it SHALL present
the findings and propose one remedy per remediable finding, obtain explicit
consent through a single batched selection honoring the dialog-prose
separation rule, run only the consented remedies, re-run `shipd doctor`,
and report the before/after states. Where the doctor output is absent or
unparseable, the skill SHALL report that as its own failure rather than
proceeding. The skill SHALL run at most one remedy round per invocation.

#### Scenario: Healthy environment stops after diagnosis
- **WHEN** `/s:doctor` runs and every check reports `ok`
- **THEN** the skill reports the healthy result and runs no remedy and no
  consent dialog

#### Scenario: Consent precedes every remedy
- **WHEN** findings exist and the user consents to a subset of the proposed
  remedies
- **THEN** only the consented remedies run, and the preflight is re-run and
  reported afterwards

#### Scenario: Declining runs nothing
- **WHEN** the user declines all remedies
- **THEN** the skill runs nothing and ends with the findings and their
  manual hints

### Requirement: Remedy safety boundaries
id: doctor-remedy-boundaries

The skill's remedy table SHALL be: a `textual` warning → `python3 -m `
followed by the `pip install` command the finding's own detail names (the
preflight composes it for the environment: `-r requirements.txt` or the
pinned `textual>=8.2.8,<9` range mirrored from `requirements.txt`, with
`--user --break-system-packages` prepended on an externally managed
interpreter); a `difft` warning → the
review engine's tiered installer,
`python3 "${CLAUDE_PLUGIN_ROOT}/skills/review/scripts/semdiff.py" doctor
--fix`, with the network access it may perform stated before it runs; a
stale `snapshot` warning →
`claude plugin update s@shipd` with the restart-to-apply note; a
`statusline` warning → `shipd statusline install` (the binary resolved
exactly as the preflight resolved it); a missing `gh` or `git` → the
platform-appropriate install command, stated before it runs; a `protection`
warning naming an unprotected default branch → `gh api -X PUT
repos/<nwo>/branches/<default>/protection` with the minimal body requiring
the `semantic-review` status context (`required_status_checks: {strict:
false, contexts: ["semantic-review"]}`, `enforce_admins: false`,
`required_pull_request_reviews: null`, `restrictions: null`); a `protection`
warning naming a missing `semantic-review` context on an already protected
branch → `gh api -X POST
repos/<nwo>/branches/<default>/protection/required_status_checks/contexts`
appending `semantic-review`, never the whole-protection PUT; and an
`automerge` warning → `gh api -X PATCH repos/<nwo> -F
allow_auto_merge=true`. Each `gh api` remedy's consent option SHALL state
the exact mutation it performs, and where a `protection` or `automerge`
finding's detail states the token lacks admin permission, the finding SHALL
be report-only — the skill SHALL propose no `gh api` remedy it already
knows will be denied. Where a relayed `pip install` command carries
`--break-system-packages`, the consent dialog SHALL state that flag in the
remedy's option, so overriding the distribution's PEP 668 guard is itself
consented. An unauthenticated `gh` SHALL be handed to the user as
`! gh auth login` and never run by the skill; a `copilot-secret` warning
SHALL likewise be a hand-off and never run by the skill — the skill SHALL
relay the documented minimal-PAT creation steps (a dedicated fine-grained
token carrying only the account-level "Copilot Requests" permission, per
`docs/copilot-review.md`) and hand the storage step to the user as
`! gh secret set COPILOT_GITHUB_TOKEN`. A failing
`python` version check and a failing `config` check SHALL be report-only —
the skill SHALL never install an interpreter and never edit a
`.shipd-config.json`. A failing `pipeline` check SHALL likewise be
report-only — the skill SHALL never edit a `.shipd-config.json` to repair a
declared pipeline; no remedy row installs a package on its behalf, since
the resolver depends on none. The skill SHALL recognize `pipeline`, `difft`, `protection`, `automerge`, and
`copilot-secret` among the parsed check names. The `shipd doctor` CLI verb
itself SHALL remain unmodified by this capability.

#### Scenario: Interactive auth is handed off
- **WHEN** the findings include an unauthenticated `gh`
- **THEN** the skill instructs the user to run `! gh auth login` and does
  not execute it

#### Scenario: Config failures are never auto-edited
- **WHEN** the findings include a `config` failure naming a malformed file
- **THEN** the skill reports the file and error with no edit performed and
  proposes no remedy command for it

#### Scenario: Externally managed remedy states the override flag
- **WHEN** a `textual` finding's detail carries
  `--user --break-system-packages`
- **THEN** the consent dialog's option for that remedy states the
  `--break-system-packages` flag, and the command run on consent carries it

#### Scenario: Difft remedy runs only on consent
- **WHEN** the findings include a `warn difft` line and the user consents to
  its remedy
- **THEN** the skill runs the tiered `semdiff.py doctor --fix` installer,
  then re-runs the preflight and reports the before/after states

#### Scenario: Statusline remedy runs only on consent
- **WHEN** the findings include a `warn statusline` line and the user
  consents to its remedy
- **THEN** the skill runs `shipd statusline install`, then re-runs the
  preflight and reports the before/after states

#### Scenario: Malformed pipeline is report-only
- **WHEN** the findings include a `fail pipeline` line whose detail names
  malformed entries or an unknown preset
- **THEN** the skill reports the resolver's error with no edit performed
  and proposes no remedy command for it

#### Scenario: A pipeline failure proposes no package install
- **WHEN** the findings include a `fail pipeline` line
- **THEN** no remedy proposing a `pip install` is offered for it, and no
  config edit is proposed

#### Scenario: Unprotected branch remedy runs only on consent
- **WHEN** the findings include a `warn protection` line naming an
  unprotected default branch without an admin-missing note, and the user
  consents to its remedy
- **THEN** the skill runs the whole-protection PUT requiring
  `semantic-review`, then re-runs the preflight and reports the
  before/after states

#### Scenario: Missing context appends rather than clobbers
- **WHEN** the findings include a `warn protection` line naming a missing
  `semantic-review` context on an already protected branch, and the user
  consents to its remedy
- **THEN** the skill runs the contexts-append POST, never the
  whole-protection PUT

#### Scenario: Non-admin GitHub findings are report-only
- **WHEN** a `warn protection` or `warn automerge` finding's detail states
  the token lacks admin permission
- **THEN** the skill reports the finding with its manual hint and offers no
  `gh api` remedy for it

#### Scenario: Copilot secret is handed off
- **WHEN** the findings include a `warn copilot-secret` line
- **THEN** the skill relays the minimal-PAT creation steps and instructs
  the user to run `! gh secret set COPILOT_GITHUB_TOKEN`, executing
  nothing itself

### Requirement: Doctor skill registration
id: doctor-skill-registration

The skill SHALL live at `plugins/s/skills/doctor/SKILL.md` with `name` and
`description` frontmatter whose description carries the `/s:doctor` trigger,
SHALL carry the question-rejection recovery rule, and SHALL be listed in the
repository `README.md` skills table and in `AGENTS.md`'s skill enumeration.

#### Scenario: Skill is discoverable and documented
- **WHEN** the plugin's skills and the README table are compared
- **THEN** `doctor` appears in both, with `/s:doctor` as its invocation

#### Scenario: Recovery rule is carried
- **WHEN** `plugins/s/skills/doctor/SKILL.md` is inspected
- **THEN** it contains the question-rejection recovery rule

### Requirement: Wiki check line is report-only
id: doctor-wiki-line

The `/s:doctor` skill SHALL recognize `wiki` among the parsed check names
and SHALL treat it as report-only: no remedy row SHALL exist for it, the
skill SHALL never scaffold a wiki store on its behalf, and the line SHALL be
relayed in the diagnosis exactly as the other informational checks are.

#### Scenario: Wiki line is parsed and never remediated
- **WHEN** the doctor output carries an `ok wiki — …` line
- **THEN** the skill parses it like any other check line, proposes no remedy
  for it, and creates no store
