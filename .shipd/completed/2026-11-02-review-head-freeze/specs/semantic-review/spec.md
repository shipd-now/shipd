## ADDED Requirements

### Requirement: Refusal of a head that adds nothing
id: empty-head-refusal

If a `<head>` is given to `semdiff diff`, `files`, or `lint` and it resolves to
the merge base of the resolved base and the head (merge-base mode), or to the
resolved base's own commit (under `--linear`), then the system SHALL exit 1,
SHALL write to stderr a message naming the head as given, the base as given,
and that the head adds nothing over the base, and SHALL write nothing to
stdout. While reviewing the working tree — no `<head>` given — the system SHALL
NOT apply this refusal.

When `semdiff` refuses a head this way, the `/s:review` skill SHALL report
"Nothing to review" with the resolved endpoints, SHALL emit no findings
verdict, and SHALL post nothing to a pull request.

#### Scenario: A head already contained in the base is refused
- **GIVEN** `feature` is an ancestor of `main`
- **WHEN** `semdiff diff main feature` runs
- **THEN** the exit code is 1, stdout is empty, and stderr names `feature`,
  `main`, and that the head adds nothing over the base

#### Scenario: Files and lint refuse the same head
- **GIVEN** `feature` is an ancestor of `main`
- **WHEN** `semdiff files main feature` and `semdiff lint main feature` run
- **THEN** each exits 1 with the same refusal message

#### Scenario: Linear mode refuses a head equal to the base
- **WHEN** `semdiff diff main main --linear` runs
- **THEN** the exit code is 1 and stderr names that the head adds nothing over
  the base

#### Scenario: Working-tree mode with no edits is not refused
- **GIVEN** a clean checkout on `main`
- **WHEN** `semdiff diff main` runs
- **THEN** the exit code is 0 and `summary.files` is 0

#### Scenario: The skill reports nothing to review
- **WHEN** `plugins/s/skills/review/SKILL.md` is inspected
- **THEN** it instructs that a `semdiff` refusal for a head adding nothing is
  reported as "Nothing to review" with no findings verdict and no post

## MODIFIED Requirements

### Requirement: Endpoint disclosure on every review
id: endpoint-disclosure
base: b900efdb95fb

The endpoint metadata `semdiff diff`, `files`, and `lint` emit SHALL additionally
carry `base_given` (the ref as invoked), `head_given` (the head ref as invoked,
null where the after side is the working tree), `base_sha`, and `head_sha`, and
SHALL carry `merge_base` in working-tree mode — where it is the fork point — as
well as in merge-base mode. Under `--linear` no `merge_base` SHALL be emitted.
Where the after side is the working tree, `head_sha` SHALL be null.

The rendered report SHALL state the resolved endpoints as commit ids before the
findings, and where the head as given differs from its commit id SHALL name the
head as given beside that commit id. The `--json` payload SHALL carry an
`endpoints` object holding the same `base_given`, `base`, `base_sha`,
`head_given`, `head`, `head_sha`, `merge_base`, and `mode` values, where
`head_given` is the head ref the invoker named before the skill froze it to a
commit id, so a reader and the poster alike can see which base and head
produced the findings. The `endpoints` object SHALL be specified identically by
every surface defining the machine payload:
`plugins/s/skills/review/references/json-output.md` and
`plugins/s/harness/references/review.md`.

#### Scenario: The endpoints are emitted as commit ids
- **WHEN** `semdiff diff main feature` runs
- **THEN** the emitted metadata carries `base_given`, `base_sha`, `head_sha`,
  and `merge_base`, each a commit id rather than a ref name

#### Scenario: The head is disclosed as given
- **WHEN** `semdiff diff main feature` runs
- **THEN** the emitted metadata carries `head_given` equal to `feature`

#### Scenario: Working-tree mode discloses a null head
- **WHEN** `semdiff diff main` runs
- **THEN** `head_sha` and `head_given` are null, and `merge_base` carries the
  fork point of the resolved base and `HEAD`

#### Scenario: Both payload surfaces specify one object
- **WHEN** `references/json-output.md` and `harness/references/review.md` are
  compared
- **THEN** both specify the same `endpoints` object with the same field names,
  `head_given` included

### Requirement: Review-start base fetch
id: review-base-fetch
base: 196586ba9d8a

The `/s:review` skill SHALL carry an inline base-freshness block instructing a
fetch of the base's remote before the first `semdiff` call, in every mode —
working-tree, two-ref, and pull-request alike — rather than only where two refs
are named. The block SHALL state that the fetch updates remote-tracking refs
only and modifies neither the working tree, the index, nor any local branch, so
the skill's no-modification guarantee is unchanged, and that the skill never
pulls, rebases, or checks anything out on the invoker's behalf.

Where a `<head>` ref is given, the block SHALL instruct resolving it to its
commit id before the fetch and passing that commit id as the head to every
`semdiff` call, so a ref the fetch rewrites (such as `FETCH_HEAD`) still names
the head the invoker meant. The block SHALL NOT freeze the base before the
fetch, so the base still resolves to its freshly fetched remote-tracking
commit.

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

#### Scenario: A named head is frozen before the fetch
- **WHEN** `plugins/s/skills/review/SKILL.md` is inspected
- **THEN** the base-freshness block instructs resolving a given head ref to its
  commit id before the fetch and passing that commit id to `semdiff`, and does
  not freeze the base

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
