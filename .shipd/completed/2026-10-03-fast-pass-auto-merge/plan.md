# fast-pass-auto-merge
Status: verified

## Idea

Arm GitHub auto-merge on a pull request whose diff carries a completed shipd
change and whose review verified every one of that change's scenarios.

### Motivation

An operator shipping a spec-driven change cannot let a pull request merge on
the strength of its own spec: the required `semantic-review` status reports
only that a review passed, never that the diff satisfied the archived change's
scenarios. Every spec-verified pull request therefore still waits on a person
to read the review and judge conformance.

### Details

- Carry the reviewed change's slug and location into `/s:review --json`, on
  both documented payload surfaces.
- Add the fast-pass eligibility rule and the arming call to
  `review_gate.py post`.
- Teach the two copilot templates to emit and act on a fast-pass marker.
- Add a `fast-pass` doctor check line and a `/s:gate` consent row for the
  `SHIPD_FAST_PASS` repository variable.

Affected capabilities: `semantic-review`, `copilot-review-skill`, `shipd-gate`,
`shipd-doctor` (each added to) and `shipd-cli` (modified). Impact: the poster
`review_gate.py`, the review skill and its two JSON payload references, the two
copilot templates under `integrations/copilot/`, the doctor checks in
`plugins/s/bin/shipd`, and the `doctor`/`gate` skills with the `gate` harness
body. No new dependencies.

### Non-goals

- No change to what `/s:review` judges — the rubric, the severities and the
  verdict rule are untouched.
- No change to `review_gate.py protect`, to the `semantic-review` protection
  write, or to `SHIPD_GATE_FAIL_OPEN`.
- No fifth managed file: `shipd copilot add` keeps owning exactly four.
- No origin check on the verdict — a status posted from the author's machine
  arms the fast-pass like one the workflow posted.

## Implementation

### The eligibility rule

A pull request is eligible only while all of these hold; any miss arms nothing
and leaves the pull request to a human:

1. The repository variable `SHIPD_FAST_PASS` reads exactly `true`.
2. The review resolved a change whose `location` is `completed`.
3. The review's `verdict` is `pass`.
4. `spec_coverage` is non-empty and every entry's `state` is `met`.
5. On the workflow path, the verdict came from a real `ship-it` marker.

Eligible means one call: `gh pr merge --auto --squash --delete-branch`.

### Decisions

- **Read `verdict`, never the posted status state.** `status_state()` returns
  `success` unconditionally under `--disposition none`, so keying the fast-pass
  to the status would merge a review with findings left open. Rejected:
  reusing the status state, which is shorter to write and wrong.
- **A `cant-tell` scenario blocks the fast-pass.** The spec-aware reference
  makes it a first-class outcome that never blocks a human-facing review; a
  merge nobody reads is the opposite case, so ambiguity takes the slow path.
- **`completed` only.** A `planned/` directory in the diff claims the change
  was specified, not that it was built, and the build flow archives to
  `completed/` before it opens the pull request.
- **Both status paths implement it.** Only the poster can act here today, and
  the workflow is what consumer repositories install, so either alone leaves
  the feature unreachable for half its users.
- **The variable is read through the existing injectable `gh` runner** as
  `gh variable get SHIPD_FAST_PASS`; a non-zero exit means off.
- **The marker rides directly above the verdict marker.** `skill-template`
  requires the verdict marker to be the body's last line, and the workflow's
  backwards scan breaks on the first verdict marker it meets, so a
  `<!-- shipd-fast-pass: eligible -->` line above it changes no existing
  classification.
- **The doctor line is report-only**, modeled on `doctor-wiki-line`:
  recognized among the parsed check names, never remediated.
  `doctor-remedy-boundaries` is left alone for the same reason the wiki, store
  and store-sync lines each earned their own requirement.
- **`doctor-github-checks` is modified rather than layered over**: its "three
  GitHub-side checks" count becomes false the moment a fourth line ships, and a
  master requirement that miscounts its own output is exactly the drift the
  engine exists to prevent.

Risk: a fast-pass armed on a spec the same pull request authored proves
internal consistency, not correctness. Accepted deliberately — the trust
boundary is the operator who ran the review.

## Questions and answers

### Q1: Which status path arms the fast-pass?
- **Question:** Two paths set the `semantic-review` status — the installed
  `copilot-review-gate.yml` (bash, marker-based) and `review_gate.py post`
  (local, JSON-based). Which implements the arming? Options: (1) both; (2) the
  poster only; (3) the workflow only. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Both paths. The poster is the only one that can act in this
  repository today, and the workflow is the path consumer repositories get, so
  implementing one alone would ship a feature half its users cannot reach.
- **Queued:** q-fast-pass-arming-path

### Q2: Does the doctor gain a fast-pass check line?
- **Question:** Should `shipd doctor` report `SHIPD_FAST_PASS` as a check
  line, given that `protection`, `automerge` and `copilot-secret` have lines
  while `SHIPD_GATE_FAIL_OPEN` has none? Options: (1) add a `fast-pass` line;
  (2) follow the fail-open precedent. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Add the `fast-pass` line. The variable authorizes merging without
  a human, which is the same blast radius as `automerge`, and that check is
  probed; a strictness knob that only holds a check pending is not comparable.
- **Queued:** q-fast-pass-doctor-check-line

## Readiness attestation

### Problem and motivation

An operator cannot let a pull request merge on the strength of its own spec:
the required status reports that a review passed, never that the diff satisfied
the change's scenarios.

Evidence:

- `plugins/s/skills/review/scripts/review_gate.py:205` — `status_state()` maps
  verdict and disposition to the status with no spec-coverage input at all.
- `plugins/s/skills/review/references/json-output.md` already emits
  `spec_coverage`, and no consumer reads it.
- `plugins/s/skills/build/SKILL.md:647` — the build flow arms auto-merge at
  pull-request open, before any review has run.

### Scope and non-goals

The eligibility rule, both status-setting paths, the variable, the doctor line
and the gate consent row are in scope; the review's own judgement, the
protection write and `SHIPD_GATE_FAIL_OPEN` stay out.

Evidence:

- In scope: `review_gate.py` (`cmd_post`), `copilot-review-gate.yml`,
  `integrations/copilot/SKILL.md`, `plugins/s/bin/shipd`, `skills/gate/SKILL.md`.
- Out of scope: `semantic-review` requirement `required-check-protect` and
  `shipd-doctor` requirement `doctor-remedy-boundaries` are both left as they
  are.

### Affected capabilities and files

Five capabilities and five requirement entries, landing on the poster, the two
copilot templates, the doctor's GitHub-side checks, the gate skill, and the two
JSON payload references.

Evidence:

- Capabilities: `semantic-review`, `copilot-review-skill`, `shipd-gate`,
  `shipd-doctor` (added to); `shipd-cli` requirement `doctor-github-checks`
  (base f6b6e168c591, hash from `spec_status.py base-hash`).
- Files: `plugins/s/skills/review/scripts/review_gate.py:205`,
  `plugins/s/integrations/copilot/copilot-review-gate.yml:607`,
  `plugins/s/bin/shipd:1087`, `plugins/s/skills/gate/SKILL.md`,
  `plugins/s/skills/review/references/json-output.md`,
  `plugins/s/harness/references/review.md:36`.
- Runnable premise: `gh variable get SHIPD_FAST_PASS` exited 1, empty stdout,
  `variable SHIPD_FAST_PASS was not found` on stderr — an absent variable is
  detectable by exit code.
- Runnable premise: `gh api repos/shipd-now/shipd` reported `allow_auto_merge`,
  `allow_squash_merge` and `delete_branch_on_merge` all true, so the arming
  flags are available here.
- Runnable premise: `shipd doctor` printed `protection`, `automerge` and
  `copilot-secret` last, with `copilot-secret — skipped: no
  .github/workflows/copilot-review-gate.yml` — fixing the new line's placement
  and showing only the poster can set the status here.
- Runnable premise: `review_gate.py post --help` listed exactly `--from`,
  `--disposition` and `--model` — no merge option exists to extend.
- Runnable premise: `semdiff.py change --help` resolves `planned/` first, else
  the newest `completed/<date>-<name>/`, and its payload carries `change`,
  `location`, `dir` and `status`.

### No open task-shaping decision

Every task-shaping decision is settled.

Evidence:

- Which status paths arm the fast-pass: settled by the user, Q1.
- Whether the doctor gains a check line: settled by the user, Q2.
- Eligibility reads `verdict`, not the status state: settled by
  `review_gate.py:205`, where `--disposition none` returns `success`
  unconditionally.
- Marker placement above the verdict marker: settled by `skill-template`,
  which pins the verdict marker as the body's last line.
- Leaving `doctor-remedy-boundaries` alone: settled by the `doctor-wiki-line`,
  `doctor-store-line` and `doctor-store-sync-line` precedent.
