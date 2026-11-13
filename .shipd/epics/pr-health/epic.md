# pr-health
Status: ready
Theme: reliability

## Introduction

An analysis of the last 50 merged pull requests (#368–#417) shows the
semantic review gate works: it caught all 3 high findings before merge, and
every high and medium finding was fixed. The same data shows five places
where shipd lets avoidable work through to that last gate:

- Pull requests over 1,000 changed lines averaged 2.2 findings; 100–500 line
  ones averaged 0.7. #378 alone collected 17 threads over two blocked rounds,
  and its fix commit drew new findings.
- Seven findings were "No test covers…": the tests arrived after review, not
  with the code, although the plan rules already order a test task first.
- About ten findings were a doc, spec, or PR body describing behaviour the
  code no longer has. Nothing checks for that drift before the PR opens.
- #407 and #409 each bumped to a plugin version another PR had just taken on
  `main`, and needed a review round to fix it. The plan fixes the number
  early, and CI checks it against a base that is stale by merge time.
- 25 of 39 fixed findings carry no reply. `review_gate.py resolve` accepts any
  later commit as evidence, even one that never touches the flagged file, so
  a thread cannot tell a fix from a push past it.

This epic moves each check earlier or makes its evidence honest. A plan that
looks oversized gets a warning while splitting is still cheap. The linter
requires a test task for every requirement. Build checks docs and specs
against the diff before the PR opens. Build picks the plugin version from
fresh `main` at ship time. `resolve` posts a "Fixed in <sha>" reply and only
counts a commit that touched the finding's file.

Success criteria: a re-run of the analysis over the 50 pull requests after
this epic lands shows no version clash, no "No test covers…" finding on a
change planned after the lint rule, a reply on every fixed finding, and fewer
doc-drift findings than the 10 in the baseline.

### Non-goals

- **No change to the semantic review itself.** Its rubric, severities, and
  posting stay as they are; this epic acts before and after it.
- **No GitHub settings change.** The "require branches to be up to date"
  rule stays off; the version fix lives in build.
- **No hard size limit.** An oversized plan is warned about, never rejected.
- **No retroactive lint.** Changes already planned or archived when the test
  rule lands do not start failing lint.
- **No per-person metrics.** The analysis and its re-run report on pull
  requests, never on who wrote them.

## References

- [PR analysis — last 50 closed PRs](../../docs/pr-analysis-last-50/doc.md) The baseline numbers this epic's success criteria compare against.

## Decisions

- **Size is a warning at plan time.** The context gate (`spec_gate.py`)
  counts the distinct paths `tasks.md` names and the tasks it lists. Over the
  threshold it prints a warning that names both counts and recommends
  `/s:plan-deep` or an epic split. It never parks the change at `rejected`.
  The member calibrates the thresholds against the archived `tasks.md` and
  merged diff size of the 50 baseline pull requests. Rejected: a gate
  rejection, and a build-time warning that arrives too late to split.
- **Every requirement needs a test task, or a stated exemption.**
  `spec_lint.py` errors when a delta requirement is named by no task that
  targets a test file. A requirement with no runtime surface is exempted in
  `tasks.md` with an explicit marker carrying a reason; the member defines the
  marker's syntax beside the existing `[req: …]` tag. The rule applies only
  to changes installed after it lands. Rejected: a lint warning, which the
  baseline shows nobody acts on.
- **Build checks docs and specs against the diff before the PR opens.** A
  stdlib-only script lists the files under `docs/` and the content
  directory's `verified/` that name a path, symbol, or CLI verb the diff
  changed. Build's verify phase reads each candidate and fixes any stale
  statement through its existing fix loop. The script finds candidates; it
  never judges them.
- **Build picks the plugin version at ship time.** Plans stop naming a
  version number; the bump task says only "advance the plugin version". Right
  before the push, build checks `plugin.json` against a freshly fetched
  `origin/main`. When the branch's version is not above main's, build sets it
  to one patch above main's. Before arming auto-merge it re-runs
  `version_guard.py` against a fresh `origin/main` and bumps again when `main`
  has moved. `AGENTS.md`'s bump rule changes to match. CI's existing guards
  stay.
- **`resolve` writes the "Fixed in" reply.** A commit counts as disposition
  evidence only when it touches at least one of the finding's locations,
  including its "Also recurs at" paths. `resolve` then posts
  `Fixed in <short sha>` on the thread before resolving it. A thread whose
  later commits touch none of its locations needs an author reply, exactly
  like a push-back. Rejected: requiring the author to reply by hand.
- **Each member bumps the plugin version once.** Members touching
  `plugins/s/` follow the repository's bump rule. Once
  `ship-time-version-bump` lands, later members inherit its ship-time bump.

## Design

```
/s:plan ──► spec_lint ──► spec_gate ──► /s:build ──────────────► PR ──► review gate ──► resolve
            │ test task   │ size         │ verify: docs/specs     │ push:         │                │ commit touched
            │ per req     │ warning      │ drift candidates       │ version from  │                │ the file?
            ▼ (error)     ▼ (warn)       ▼ (fix loop)             ▼ origin/main   ▼ re-check       ▼ "Fixed in <sha>"
     lint-requirement-  plan-size-     pre-pr-drift-check       ship-time-version-bump       resolve-fixed-in-reply
     test-coverage      warning
```

Each member owns one stage of the pipeline, and no member's code depends on
another's. Two pairs share a file: `plan-size-warning` and
`lint-requirement-test-coverage` both read `tasks.md` but live in different
engine scripts. `pre-pr-drift-check` and `ship-time-version-bump` both edit
`/s:build`'s SKILL.md, in Phase 5 and Phase 6. The members can be planned in
any order. `ship-time-version-bump` goes first in practice, because it stops
the other four from clashing on the plugin version.

## Changes

| Change | Description | Code | Integration | Unknowns | Risk | After |
| --- | --- | --- | --- | --- | --- | --- |
| ship-time-version-bump | Build sets the plugin version from fresh origin/main at push and re-checks before auto-merge; plans and AGENTS.md stop fixing a number | low | medium | low | medium | |
| resolve-fixed-in-reply | `resolve` counts only commits touching a finding's locations and posts a "Fixed in <sha>" reply | low | low | low | medium | |
| lint-requirement-test-coverage | `spec_lint.py` errors on a requirement with no test task, with a reasoned exemption marker, for newly installed changes only | medium | medium | medium | medium | |
| plan-size-warning | `spec_gate.py` warns on a plan whose path and task counts exceed calibrated thresholds, recommending `/s:plan-deep` or a split | low | low | medium | low | |
| pre-pr-drift-check | A candidate-finder script lists docs and verified specs naming what the diff changed; build's verify phase fixes stale ones | medium | medium | medium | low | |
