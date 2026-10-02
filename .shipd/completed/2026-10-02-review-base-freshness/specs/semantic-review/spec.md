## ADDED Requirements

### Requirement: Base resolution to the remote-tracking counterpart
id: base-resolution

Where a `<base>` given to `semdiff diff`, `files`, or `lint` names a short local
branch carrying a remote-tracking counterpart — the branch's configured
upstream, else `refs/remotes/origin/<base>` — the system SHALL resolve the base
to that counterpart's commit, so a local branch behind its remote is never read
as a review's base. Where the base is a fully-qualified ref, a commit id, a tag,
or an already-remote ref, the system SHALL take it as given and SHALL NOT
resolve it further, which is the invoker's unambiguous opt-out.

While reviewing the working tree — no `<head>` given — the system SHALL anchor
the before side on the merge base of the resolved base and `HEAD`, never on the
resolved base's tip, so the base's own advance is never rendered as reversions.

The system SHALL perform no fetch, no checkout, and no write of any kind while
resolving: it reads already-fetched refs and reads every base-side blob from the
object database, so no worktree is materialized.

#### Scenario: A stale local base no longer sweeps in the base's own commits
- **GIVEN** local `main` is three commits behind `origin/main` and `feature`
  branches from `origin/main`
- **WHEN** `semdiff diff main feature` runs
- **THEN** only the files `feature` changed are reported, and the emitted base
  names the remote-tracking counterpart rather than the local branch

#### Scenario: Working-tree mode anchors on the fork point
- **GIVEN** the checkout sits on a local `main` three commits behind
  `origin/main`, with one edited file
- **WHEN** `semdiff diff main` runs
- **THEN** only the edited file is reported, and none of the files those three
  commits changed

#### Scenario: An explicitly qualified base is taken as given
- **GIVEN** local `main` is behind `origin/main`
- **WHEN** `semdiff diff refs/heads/main feature` runs
- **THEN** the base resolves to the local branch's own commit

#### Scenario: A base with no counterpart resolves unchanged
- **WHEN** `semdiff diff <commit-id> feature` runs in a repository with no
  remote
- **THEN** the base resolves to that commit and the run reports it unchanged

### Requirement: Endpoint disclosure on every review
id: endpoint-disclosure

The endpoint metadata `semdiff diff`, `files`, and `lint` emit SHALL additionally
carry `base_given` (the ref as invoked), `base_sha`, and `head_sha`, and SHALL
carry `merge_base` in working-tree mode — where it is the fork point — as well as
in merge-base mode. Under `--linear` no `merge_base` SHALL be emitted. Where the
after side is the working tree, `head_sha` SHALL be null.

The rendered report SHALL state the resolved endpoints as commit ids before the
findings, and the `--json` payload SHALL carry an `endpoints` object holding the
same `base_given`, `base`, `base_sha`, `head`, `head_sha`, `merge_base`, and
`mode` values, so a reader and the poster alike can see which base produced the
findings. The `endpoints` object SHALL be specified identically by every surface
defining the machine payload: `plugins/s/skills/review/references/json-output.md`
and `plugins/s/harness/references/review.md`.

#### Scenario: The endpoints are emitted as commit ids
- **WHEN** `semdiff diff main feature` runs
- **THEN** the emitted metadata carries `base_given`, `base_sha`, `head_sha`,
  and `merge_base`, each a commit id rather than a ref name

#### Scenario: Working-tree mode discloses a null head
- **WHEN** `semdiff diff main` runs
- **THEN** `head_sha` is null, and `merge_base` carries the fork point of the
  resolved base and `HEAD`

#### Scenario: Both payload surfaces specify one object
- **WHEN** `references/json-output.md` and `harness/references/review.md` are
  compared
- **THEN** both specify the same `endpoints` object with the same field names

### Requirement: Review-start base fetch
id: review-base-fetch

The `/s:review` skill SHALL carry an inline base-freshness block instructing a
fetch of the base's remote before the first `semdiff` call, in every mode —
working-tree, two-ref, and pull-request alike — rather than only where two refs
are named. The block SHALL state that the fetch updates remote-tracking refs
only and modifies neither the working tree, the index, nor any local branch, so
the skill's no-modification guarantee is unchanged, and that the skill never
pulls, rebases, or checks anything out on the invoker's behalf.

If the fetch fails, then the review SHALL continue and SHALL record a
could-not-verify entry naming that the base went unchecked against its remote —
in the rendered report's could-not-verify list and in `--json`'s
`could_not_verify` array alike — rather than ending the review.

Where the endpoints given to `semdiff lint` name two refs, the review SHALL
record a could-not-verify entry naming that the linters read the checkout rather
than the reviewed head, since `lint` passes changed paths to linter binaries that
read them from disk.

`plugins/s/harness/bodies/review.md`, which cannot read a file under
`skills/review/references/`, SHALL state the same fetch rule in its own body.

#### Scenario: The fetch rule covers the default mode
- **WHEN** `plugins/s/skills/review/SKILL.md` is inspected
- **THEN** the base-freshness block instructs a fetch before the first `semdiff`
  call in every mode, and states that the fetch writes remote-tracking refs only

#### Scenario: A failed fetch is disclosed, not fatal
- **WHEN** the review-start fetch fails
- **THEN** the review proceeds and its could-not-verify list names the base as
  unchecked against its remote

#### Scenario: Two-ref lint discloses that it read the checkout
- **WHEN** a review runs `semdiff lint <base> <head>` with two refs
- **THEN** its could-not-verify list names that the linters read the checkout
  rather than the reviewed head

#### Scenario: The harness body carries the rule
- **WHEN** `plugins/s/harness/bodies/review.md` is inspected
- **THEN** it states the same fetch-before-every-mode rule in its own body

### Requirement: Doctor base-freshness probe
id: doctor-base-probe

`semdiff doctor` SHALL additionally report a base-freshness line comparing the
repository's default base branch — `main`, else `master` — against its
remote-tracking counterpart, naming the behind and ahead counts when the two
differ and naming the remedy. Without `--fix` the probe SHALL compare
already-fetched refs and SHALL reach the network not at all; where `--fix` is
given, the probe SHALL fetch that remote before comparing.

The probe SHALL be report-only: a diverged or unresolvable base SHALL NOT change
`doctor`'s exit code, which stays non-zero only when a required tool is missing.

#### Scenario: A diverged base is reported without failing the doctor
- **GIVEN** local `main` is behind `origin/main` and every required tool is
  present
- **WHEN** `semdiff doctor` runs
- **THEN** the base line names the behind count and the remedy, no fetch occurs,
  and the exit code is zero

#### Scenario: A repository with no counterpart reports cleanly
- **WHEN** `semdiff doctor` runs in a repository whose default branch has no
  remote-tracking counterpart
- **THEN** the base line says there is nothing to compare and the exit code is
  unchanged

### Requirement: Pull-request base guard
id: post-base-guard

Before its first GitHub write, `review_gate.py post` SHALL resolve the pull
request's `baseRefOid` and `headRefOid` through the `gh` seam, compute their
merge base through an injectable `git` runner, and compare it with the review
payload's `endpoints.merge_base`. If the two differ, or if the payload carries no
`endpoints.merge_base`, then `post` SHALL abort before upserting the summary
comment, posting any inline comment, or setting the `semantic-review` status,
SHALL name both merge bases — or the missing field — and SHALL exit non-zero.

Where the review's target is a named pull request, the `/s:review` skill SHALL
resolve that pull request's base through GitHub rather than through a local
branch name, fetching the pull request's head ref and its base branch so both
commits are present, reviewing as the two resolved commit ids, and stating the
base commit it used.

#### Scenario: A mismatched base aborts the post
- **GIVEN** a review payload whose `endpoints.merge_base` differs from the merge
  base of the pull request's own base and head
- **WHEN** `review_gate.py post` runs
- **THEN** no summary comment, inline comment, or commit status is written, the
  failure names both merge bases, and the exit code is non-zero

#### Scenario: A payload with no endpoints aborts the post
- **GIVEN** a review payload carrying no `endpoints.merge_base`
- **WHEN** `review_gate.py post` runs
- **THEN** no GitHub write occurs and the failure names the missing field

#### Scenario: A matching base posts as before
- **GIVEN** a review payload whose `endpoints.merge_base` equals the pull
  request's own merge base
- **WHEN** `review_gate.py post` runs
- **THEN** the summary comment, the inline comments, and the `semantic-review`
  status are written exactly as they were before the guard existed

#### Scenario: The skill resolves the pull request's base through GitHub
- **WHEN** `references/posting.md` is inspected
- **THEN** it resolves the base through the pull request's own base commit id
  rather than its base ref name, and names the fetch that makes both commits
  present

## MODIFIED Requirements

### Requirement: Skill reference loading
id: review-skill-references
base: 756ed4ea29eb

The `/s:review` skill SHALL carry its condition-gated guidance in reference
files under `plugins/s/skills/review/references/` rather than inline in its
`SKILL.md`, and `SKILL.md` SHALL name every file in that directory by its
`${CLAUDE_PLUGIN_ROOT}` path beside the condition under which the skill reads
it. The spec-aware verification guidance, the `--json` machine output guidance,
and the PR posting guidance SHALL each occupy one such file, read only when a
planned change is in scope, when `--json` is requested, and when a pull request
is in scope for the review, respectively. The posting reference SHALL carry the
resolution of a named pull request into a base and a head, so `SKILL.md` names
that flow rather than restating it.

Guidance that runs on every review SHALL stay inline in `SKILL.md`: the
workflow steps, the severity rubric, the presentation shape, the review-start
difftastic probe and its degradation ladder, the base-freshness block, and the
guardrails. `SKILL.md` SHALL stay under 330 lines.

Each reference file SHALL open with a level-1 title and state its own load
condition, so a file read on its own explains why it was read. Moving guidance
into a reference SHALL NOT change that guidance's substance.

#### Scenario: Every reference is reachable from the skill
- **WHEN** `plugins/s/skills/review/SKILL.md` is inspected
- **THEN** it names every file under `plugins/s/skills/review/references/` by
  path, and every reference path it names resolves to an existing file

#### Scenario: The posting reference is loaded on a pull request
- **WHEN** the References table row for `posting.md` is compared with that
  file's own condition sentence
- **THEN** both state that the file is read when a pull request is in scope for
  the review, rather than when posting was explicitly requested

#### Scenario: Conditional guidance left the skill body
- **WHEN** `plugins/s/skills/review/SKILL.md` is inspected
- **THEN** it carries no `## Machine output mode`, `## Posting to a PR`, or
  `## Spec-aware review` section, and the three reference files carry that
  guidance instead

#### Scenario: Hot-path guidance stayed inline
- **WHEN** `plugins/s/skills/review/SKILL.md` is inspected
- **THEN** the workflow steps, the high/medium/low severity rubric, the
  `command -v difft` probe, and the base-freshness block are present in the file
  itself, behind no reference

#### Scenario: The skill body fits the ceiling
- **WHEN** `plugins/s/skills/review/SKILL.md` is measured
- **THEN** it is under 330 lines

#### Scenario: A reference states its own trigger
- **WHEN** a file under `plugins/s/skills/review/references/` is read on its own
- **THEN** its opening lines give a level-1 title and the condition under which
  the skill loads it

#### Scenario: The other rubric surfaces are untouched
- **WHEN** `plugins/s/integrations/copilot/SKILL.md` and
  `plugins/s/harness/bodies/review.md` are inspected
- **THEN** neither references a file under `plugins/s/skills/review/references/`,
  since neither runs where `${CLAUDE_PLUGIN_ROOT}` resolves
