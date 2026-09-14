<!-- doc-type: reference -->

# Semantic review reference

[The semantic review](semantic-review.md) is the concept guide: what the
review reads, what it looks for, and how it blocks a merge. This page lists
the `--json` payload, the `lint` configuration key, and the `prior` verb's
output.

## The `--json` payload

`--json` emits one object: `verdict`, `effort`, `findings`, `spec_coverage`,
and `could_not_verify`. `verdict` is `changes-requested` when any finding is
`high` or `medium`, and `pass` otherwise. `spec_coverage` appears only when a
planned change is in scope, and an unmet scenario also posts as a
`spec-coverage` finding in `findings` rated `high`.

Each entry in `findings` carries these fields:

| field | holds |
|---|---|
| `id` | a short label, unique within the payload |
| `severity` | `high`, `medium`, or `low` |
| `category` | one of the ten values below |
| `location` | `path/to/file.ext:LINE` |
| `what` | a one-line statement of the defect |
| `why` | why it matters |
| `fix` | a concrete fix |
| `status` | `open` |
| `note` | reviewer commentary, or an empty string |
| `suggestion` | optional; see below |

`category` is one of: `bug`, `contract`, `edge-case`, `untouched-caller`,
`spec-coverage`, `test-coverage`, `security`, `performance`, `stability`, or
`data-integrity`.

### The optional `suggestion` object

A finding carries `suggestion` only when the reviewer trusts the fix enough
to let GitHub apply it unread. The poster commits it as a GitHub suggestion
only when every one of these holds. Any other shape degrades the finding to
prose, never an error:

- `confident` is exactly `true`.
- `start_line` and `end_line` are integers, with `start_line <= end_line`.
- `lines` is a non-empty list of whole replacement lines, with no
  `start_column` or `end_column`.
- `location` anchors to a right-side line of the diff, and every line in
  `start_line..end_line` is in that diff too.

Source: `plugins/s/skills/review/references/json-output.md`.

## The `lint` configuration key

`lint` is an optional top-level key in `.shipd-config.json`. It configures the
`semdiff lint` subcommand.

| member | type | default | meaning |
|---|---|---|---|
| `run_scripts` | boolean | `false` | Permits `lint` to execute a repository-defined lint script (for example, a `package.json` `lint` script) instead of only reporting it as detected. |
| `disable` | list of strings | `[]` | Names detected linters `lint` skips, even where a marker and a binary are both present. |

Omitting `lint` runs no repository script and disables no detected linter.

Source: the `// lint` entry in
`plugins/s/skills/build/references/shipd.config.example.json`.

## The `prior` verb

`review_gate.py prior <pr>` reports every gate-authored review thread on a
pull request, without dispositioning or mutating any of them. Each entry
carries:

| field | holds |
|---|---|
| `hash` | the finding's identity hash, or `null` |
| `path` | the file the finding names |
| `severity` | `high`, `medium`, or `low` |
| `what` | the finding's one-line statement |
| `thread_id` | the review thread's ID |
| `resolved` | whether the thread is resolved |
| `disposition` | one of the four classes below |

`disposition` is one of:

| disposition | assigned when |
|---|---|
| `replied` | a reply exists, and it is not one of the canonical `autoreply` bodies |
| `autoreplied` | every reply is one of the canonical `autoreply` bodies |
| `commit-only` | no reply exists, but a commit landed after the thread opened |
| `none` | no reply exists, and no commit landed after the thread opened |

Only `replied` suppresses a recurrence of the same finding: `replied` is the
only disposition that shows a person read the finding and answered it. The
other three carry no such evidence, so a matching finding posts again.

A thread posted before the identity marker shipped reports `hash` as `null`.
A `null` hash matches nothing, so such a finding always posts again — that
reads as the marker's start date, not as a bug.

Reposting the gate after a new push creates a new thread rather than updating
the old one. Running `prior` on such a pull request can return more entries
than the review has open findings, because one finding's history now spans
two `thread_id`s.

Source: the `prior` docstring in
`plugins/s/skills/review/scripts/review_gate.py`.
