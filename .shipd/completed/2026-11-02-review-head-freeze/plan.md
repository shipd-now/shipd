# review-head-freeze
Status: verified
Planned-at: 90b4ac75747c6892b128310a342d623b8b65b9f4
Gated-hash: 1d5f4c616d4f

## Idea

Stop `/s:review` from passing an empty comparison as a clean review: the engine refuses a head that adds nothing over the base, the endpoints name the head as given, and the skill freezes a named head to its commit before the base fetch.

### Motivation

A caller who hands `/s:review` a head ref the review's own base fetch rewrites (FETCH_HEAD) gets the base compared against itself and a `✅ Ship it` verdict on zero files, with no error. Nobody reading the output can tell the review compared nothing, because the endpoints line shows two bare commit ids and the verdict says clean.

### Details

- `semdiff diff`, `files`, and `lint` exit 1 with a "head adds nothing over base" message when the head resolves to the merge base (merge-base mode) or the base commit (`--linear`).
- The endpoint metadata gains `head_given`, the head ref as invoked (null in working-tree mode); both payload docs and the rendered endpoints line carry it.
- The `/s:review` base-freshness block resolves a given head ref to its commit id before the fetch, passes that commit id to every `semdiff` call, and keeps the name for `head_given`.
- On the engine's refusal the skill reports "Nothing to review" with the endpoints, emits no verdict, and posts nothing.

Affected capability: `semantic-review` (modified: `endpoint-disclosure`, `review-base-fetch`; added: `empty-head-refusal`). Impact: `plugins/s/skills/review/scripts/semdiff.py`, `plugins/s/skills/review/SKILL.md`, `plugins/s/skills/review/references/json-output.md`, `plugins/s/harness/references/review.md`, two review test files, and `plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- The plain-git harness body `plugins/s/harness/bodies/review.md` is unchanged: it renders 149 lines against a ceiling under 150 (Q1).
- The base-freshness fetch stays in SKILL.md prose; moving it into the engine is out of scope.
- Working-tree mode gains no refusal: an empty working-tree diff is a legitimate "no local changes".
- The base is never frozen before the fetch, so base promotion to the freshly fetched remote-tracking commit is unchanged.

## Implementation

- **Guard location: `resolve_endpoints`** (`semdiff.py:258`). `diff`, `files`, and `lint` all call it and spread its meta into their output (`semdiff.py:661`, `:785`, `:1105`), so one check covers all three. Rejected: a check in `cmd_diff` only, which leaves `files`, used by the CI gate (`copilot-review-gate.yml:338`), passing empty.
- **Guard condition, per mode.** Merge-base mode: refuse when `head_sha == mb`. Linear mode: refuse when `head_sha == base_sha`. Working-tree mode: no check. The refusal calls the existing `die()` with the default exit code 1 and the message `head '<head>' (<head_sha short>) adds nothing over base '<base_given>' (<base_sha short>) — nothing to review; check the head ref`. Rejected: a distinct exit code — every current caller already treats any non-zero exit as failure, and the message carries the meaning.
- **`head_given`.** `resolve_endpoints` records `head` as invoked into `meta["head_given"]` in every mode (null in working-tree mode), beside the existing `base_given`. In the `--json` payload's `endpoints` object, the skill fills `head_given` with the name the user gave, before it froze that name to a commit id; every other endpoints field still comes straight from `semdiff`'s meta.
- **Freeze order in SKILL.md.** Before the fetch, when a head ref is given, run `git rev-parse --verify <head>^{commit}` and use the printed commit id as `<head>` in every `semdiff` call. Only the head is frozen; the base resolves after the fetch, so `base-resolution` promotion still reads the fresh remote-tracking commit. The named-PR path already passes commit ids and needs no extra step.
- **Rendered endpoints line** (`SKILL.md:222-226`): where `head_given` differs from `head_sha`, name it beside the commit id, e.g. `head FETCH_HEAD → 8d2e59e`.
- **Refusal handling in SKILL.md.** When `semdiff` exits 1 with "adds nothing over base", print `Nothing to review` plus the endpoints line, emit no `## Findings` verdict, and post nothing to a pull request.
- **Version bump.** `plugins/s/.claude-plugin/plugin.json` takes the next patch version above main's at build time (AGENTS.md: every `plugins/s/` change bumps it).

Risk: a pull request whose head is already merged into its base now fails the CI gate as "not grounded" instead of passing empty; that is the intended loud failure. Risk: the bundled Copilot `semdiff.py` copy in user repos picks the guard up only on `shipd copilot update`, which already flags a stale copy.

## Questions and answers

### Q1: Does the harness review body gain the new rules?
- **Question:** The harness review body renders 149 lines worst case against a ceiling under 150. Should it gain the freeze-the-head and nothing-to-review rules? Options: (1) leave it unchanged as a non-goal; (2) add them and raise the ceiling to 155; (3) add them, freeing lines by mechanical rewrap only. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1 — the harness body stays unchanged and the gap is recorded as a non-goal of this change.
- **Queued:** q-review-harness-body-head-freeze

## Readiness attestation

### Problem and motivation

When a caller passes a head ref the review's own base fetch rewrites, `/s:review` compares the base against itself and reports a clean verdict on an empty diff, with nothing signalling the mistake.

Evidence:

- `plugins/s/skills/review/SKILL.md:47-63` orders the fetch before the first `semdiff` call; `semdiff.py:288` resolves the head only afterwards.
- `plugins/s/skills/review/SKILL.md:242` renders `## Findings: ✅ Ship it` and "No problems found." when there are no findings.
- Requirement `review-base-fetch` (capability `semantic-review`) mandates the fetch in every mode.

### Scope and non-goals

In scope are the engine guard, `head_given`, and the SKILL.md freeze and refusal steps; the harness body, moving the fetch, and working-tree mode stay out.

Evidence:

- In scope: `semdiff.py:258-312`, `SKILL.md:47-75`, `SKILL.md:222-246`, `json-output.md:10-20`, `harness/references/review.md:20-30`.
- Out of scope: `plugins/s/harness/bodies/review.md` (Q1); requirement `base-resolution` is not modified.

### Affected capabilities and files

One capability and seven files are affected, because the guard and metadata live in the engine while the order and rendering live in the skill prose and its payload docs.

Evidence:

- Capability `semantic-review`: `endpoint-disclosure` (base b900efdb95fb), `review-base-fetch` (base 196586ba9d8a), from `spec_status.py base-hash`; `empty-head-refusal` added.
- Files: `plugins/s/skills/review/scripts/semdiff.py`, `plugins/s/skills/review/tests/test_semdiff_diff.py`, `plugins/s/skills/review/tests/test_skill_references.py`, `plugins/s/skills/review/SKILL.md`, `plugins/s/skills/review/references/json-output.md`, `plugins/s/harness/references/review.md`, `plugins/s/.claude-plugin/plugin.json`.
- Runnable premise: in a scratch clone, `git fetch origin feat` then `git fetch origin main`, then `semdiff.py diff main FETCH_HEAD` → exit 0, `summary.files` 0, `head_sha == merge_base`; the same call with the head commit captured before the second fetch → `summary.files` 1; `--linear` → 0 files with `head_sha == base_sha`.
- Runnable premise: rendering `review` across every harness with `harness_bodies.render` measured 149 lines at worst against the `< 150` assertion in `plugins/s/skills/build/tests/test_harness_bodies.py`.
- Runnable premise: `semdiff.py files main FETCH_HEAD` in that clone → exit 0, so `files` passes the empty case today too.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- Refuse rather than render a distinct verdict, and the freeze-head-only order: settled by the user accepting the recommendation before this plan.
- Exit code 1, the per-mode condition, and the guard living in `resolve_endpoints`: settled by investigation of `semdiff.py:49`, `:258`, and `copilot-review-gate.yml:338`.
- `head_given` source when the skill passes a frozen commit id: settled by investigation of `json-output.md:63`.
- Harness body left unchanged: settled by the user, Q1.
