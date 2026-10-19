# ci-review-grounded
Status: verified
Planned-at: ac9d5cd2b9c621719ddc0750b65d56ac70cbb7ea
Gated-hash: 292f93d719dd

## Idea

The Copilot CI reviewer gets its review grounding from the gate workflow, which runs the engine itself with the refs in the right order, refuses to approve a review that covered no files, and posts only the review report.

### Motivation

Repositories that require the CI reviewer's approval can merge pull requests nobody reviewed: on unkannybanny PR 24 the CLI reviewer ran the engine with the refs reversed, saw 0 files, and the gate submitted APPROVE. Readers of every CI review also have to scroll past the reviewer's raw session transcript to reach the report.

### Details

- **Grounding.** A new step in `plugins/s/integrations/copilot/copilot-review-gate.yml` runs the engine's `files` and `diff` subcommands with the base first and the head second. It saves both outputs as files in the runner temp directory and names them in the reviewer prompt, so the model never picks refs.
- **Fail closed.** The engine can fail, or report 0 files while the pull request changes at least one file. In both cases the gate submits no APPROVE or REQUEST_CHANGES. It re-posts `semantic-review` as `pending` with a "not grounded" description, and the job fails.
- **Report only.** The reviewer runs with `-s`, and the publisher cuts the captured text down to the report, from the last "## Findings" header to the verdict marker.
- **Contract.** `plugins/s/integrations/copilot/SKILL.md` tells the reviewer to read the supplied engine output when the prompt names it.
- **Room wake.** `plugins/s/integrations/copilot/room-wake.yml` strips CLI tool-call transcript blocks from the reply before it posts.
- **Docs and version.** The docs describe the grounding and the fail-closed rule, and the plugin version moves up one patch.

Affected capabilities: `copilot-review-skill`, `pr-room` (both get new requirements). Impact: the two workflow templates, the contract template, two test files, three docs, and `plugins/s/.claude-plugin/plugin.json`. Repositories that already have the gate get the fix with `/s:gate update` (or `shipd copilot add`), which re-renders the managed files at the new version.

### Non-goals

- The poll fallback and review-event paths do not change. They classify GitHub's own review and submit no review.
- No new reviewed-files marker in the contract, and no check of a file count the model claims (Q3).
- No change to `semdiff.py` itself, the verdict-marker grammar, or the `SHIPD_GATE_FAIL_OPEN` semantics for a grounded review that has no marker.
- No change to the `/s:gate update` or `shipd copilot add` mechanics.

## Implementation

### Grounding step (gate workflow)

- New step "Ground the review in the engine's own output", `id: grounding`. It sits after the difftastic install and before the reviewer step, under the same `if:` (a `pull_request` event with the CLI reviewer configured). It also checks `EVENT_NAME` and `COPILOT_CLI_REVIEWER` in its own script, like the other steps do, because the test harness runs every step body in one script and ignores `if:`. Its env binds no secret and no `github.token`: `EVENT_NAME`, `BASE_SHA`, `HEAD_SHA`, `BASE_REF`.
- **Engine source (Q2).** The step runs the base ref's copy of `.github/skills/code-review/scripts/semdiff.py`. It resolves `origin/<base ref>` exactly the way the reviewer step pins SKILL.md, then uses `git cat-file -e` and `git show` to write that copy to "shipd-copilot-review-semdiff.py" in the runner temp directory. Only when the base tree has no engine file does it fall back to the checkout's own copy, and it logs that it did. An engine that cannot be resolved or read counts as an engine failure. Rejected: running the head copy, because a pull request could then rewrite the engine to fake a non-empty grounding.
- **Engine run.** The step runs `python3 <engine> files "$BASE_SHA" "$HEAD_SHA"` and saves stdout to "shipd-copilot-review-semdiff-files.json". It runs `python3 <engine> diff "$BASE_SHA" "$HEAD_SHA"` and saves stdout to "shipd-copilot-review-semdiff-diff.json". Both files go in the runner temp directory. The order is base then head, which gives merge-base semantics.
- **Outputs.** The step writes `outcome=ok` and `files=<n>` to `$GITHUB_OUTPUT`, where n is the files JSON's summary files count. If either engine call exits non-zero, or the files JSON has no integer summary files count, it writes `outcome=failed` and `files=0`. The step always exits 0 so the later steps still run, and its failure log line names `semantic-review`.
- **Why step outputs.** The reviewer runs `--allow-all-tools` with the runner temp directory inside its sandbox, so it can rewrite any file there. It cannot change an earlier step's outputs. The publisher therefore trusts the outputs and ignores the files.

### Reviewer step

- Env adds `GROUNDING_OUTCOME` and `GROUNDING_FILES`, both bound from the grounding step's outputs.
- When `GROUNDING_OUTCOME` is not `ok`, the step skips the Copilot run, writes no body file, and logs why. This saves credits.
- The step adds `-s` to the `copilot -p` call; the rest of the invocation stays the same.
- The prompt no longer says "Diff BASE against HEAD". It gives the full paths of the two grounding files and says the workflow already ran the contract's `files` and `diff` subcommands for this pull request. It tells the reviewer to read those two files and not run `files` or `diff` itself; `context` lookups stay allowed.

### Publisher step: grounding check (Q1)

- Env adds `GROUNDING_OUTCOME` and `GROUNDING_FILES` from the grounding step's outputs. Like the strictness knob, these come from step expressions, so an earlier step cannot overwrite them through `$GITHUB_ENV`.
- On the CLI path, the paginated changed-files read moves up to the start of the step and happens once, before the body-file check. The payload builder later reuses the same file.
- **Ungrounded rule.** The review is ungrounded when `GROUNDING_OUTCOME` is not `ok`. It is also ungrounded when `GROUNDING_FILES` is `0` and the pull request's file list holds at least one entry or could not be read. An engine count of 0 on a pull request that really changes no files is grounded and is classified as usual.
- When the review is ungrounded, the step re-posts `semantic-review` as `pending` with one of these descriptions:
  - "Review not grounded: the review engine failed on this commit; no verdict posted."
  - "Review not grounded: the review engine saw 0 of N changed files; no verdict posted."
- In that case the step ignores `SHIPD_GATE_FAIL_OPEN`, never arms fast-pass, and does not use the verdict marker. If a body was captured, it publishes the cleaned body as a `COMMENT` review whose first line is a notice ("**Not a verdict.** …") naming the same cause. Then it exits 1.
- Rejected alternatives: a `failure` status with REQUEST_CHANGES, which presents an engine fault as a code defect; and posting no review, which hides from the operator what the model wrote.

### Publisher step: report extraction (Q4)

- On the CLI path, before classifying, an inline Python heredoc run by the absolute `py_bin` writes a cleaned copy of the body file to "shipd-copilot-review-report.md" in the runner temp directory. The classifier and `comment_file` both use the cleaned copy, so the status and the posted review read the same text.
- **Rule.**
  1. Find the last line equal (after trimming) to either verdict marker.
  2. Find the last line before it whose left-trimmed text starts with `## Findings`, and keep that header line through the marker line.
  3. If there is no marker, keep from the last `## Findings` line to the end.
  4. If there is no `## Findings` line, keep the whole text but drop each tool-call transcript block. A block is a line starting with `●` followed by a space, plus the lines right after it whose left-trimmed text starts with `│` or `└`.
- The fast-pass line sits above the marker, so the slice keeps it.

### Room wake (Q5)

- The reply job's existing Python block first drops tool-call transcript blocks (the same rule as step 4 above). It then trims the reply and checks for the input-required marker as before.
- The prompt and the `-s` flag stay the same, and the room gets no new marker.

### Contract and docs

- **SKILL.md.** Below the paragraph that tells the reviewer to compare base against head, add a paragraph: when the invoking prompt names files holding the engine's `files` and `diff` output, the reviewer reads them as the steps 1 and 2 output and does not run those subcommands. The gate computes them with the refs in the right order and fails closed when they cover no files.
- **Doc targets.**
  - `docs/copilot-review-reference.md`: the CLI reviewer steps, plus a fail-closed note.
  - `docs/copilot-review.md`: in section 6, note that `/s:gate update` refreshes an already-gated repository.
  - `docs/room-wake-reference.md`: one line on reply cleaning.
- All doc edits follow `plugins/s/skills/document/references/standard.md` and must pass `plugins/s/skills/document/scripts/docs_lint.py` with no new findings.

### Tests

- `plugins/s/skills/build/tests/test_copilot_verb.py` follows the existing pattern: run the extracted step bodies under bash with stubbed `gh`, `copilot`, `git`, `timeout`, and `npm`.
- New engine stub: a Python script at the checkout's engine path, which the stub `git show` also serves for the base path. It records its arguments, prints scripted files JSON (default summary files count 3), and exits with a scripted code.
- The `git` stub tells reads of the engine path apart from reads of the skill path. For the engine path it serves `base-engine` and returns exit 128 when that file is absent.
- `gate_script` copies how the runner binds step outputs: after the grounding step's body it inserts lines that export `GROUNDING_OUTCOME` and `GROUNDING_FILES` from the `$GITHUB_OUTPUT` file. `gate()` points `GITHUB_OUTPUT` at a fresh temp file.

### Risks

- If the extraction cannot find the report, the full text is posted as before, minus tool-call blocks. That is no worse than today.
- A pull request that bumps `semdiff.py` is grounded by the base's older engine. The `files` and `diff` command line has not changed, so this is accepted.
- `-s` changes what the CLI prints, but the extraction does not depend on it.

## Questions and answers

### Q1: How does the gate treat an ungrounded CLI review?
- **Question:** When the engine fails, or reports 0 files while the pull request changes at least one, what happens to the status and the review? Options: (1) re-post `pending` with a "not grounded" description, publish the cleaned body as a COMMENT review with a notice, ignore the fail-open knob, and fail the job; (2) post `failure` with REQUEST_CHANGES; (3) leave `pending` and post no review. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. It matches the existing rule that a run which judged nothing leaves `pending` and fails the job. It also matches the answered rule that only a parsed verdict submits a decision review.
- **Queued:** q-review-gate-ungrounded-semdiff

### Q2: Which copy of the engine grounds the review?
- **Question:** Run the base ref's copy of the engine, with a fallback to the head copy only when the base has none, or the reviewed commit's own copy? Options: (1) base copy, pinned like SKILL.md; (2) head copy. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1, the base copy, pinned the same way as the reviewer instructions, so a pull request cannot rewrite the engine to fake a non-empty grounding.
- **Queued:** q-ci-review-gate-semdiff-engine-copy

### Q3: Should the contract carry a reviewed-files count to cross-check?
- **Question:** Should the model also state how many files it reviewed, in a new marker, so the workflow can compare that against the engine's count? Options: (1) no, the workflow's own count decides; (2) yes, add the marker and fail closed on a mismatch. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. The workflow computes the grounding itself and the model never chooses refs. A second marker would add something to the contract that the model could leave out or fake.
- **Queued:** none

### Q4: How does the gate keep only the review in the posted body?
- **Question:** Options: (1) `-s` plus a slice from the last "## Findings" header to the verdict marker, falling back to stripping tool-call blocks, with the verdict read from the cleaned text; (2) `-s` only; (3) the slice only. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. `-s` drops the tool-call blocks and the stats. The slice drops narration whether or not `-s` does, and the posted text is the same text the verdict was read from.
- **Queued:** q-review-gate-body-cleaning

### Q5: What cleaning does the room-wake reply get?
- **Question:** Options: (1) the same tool-call block stripping, applied in the reply job before the marker check, with no new marker; (2) also a new begin marker the agent must write; (3) no change. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. The reply gets the same cleaning as the review gate's fallback, and the reply contract stays the same.
- **Queued:** q-room-wake-reply-cleaning

## Readiness attestation

### Problem and motivation

The CLI reviewer chose its own refs, reversed them, and saw 0 files, yet the gate approved; and the posted review body includes the raw session transcript.

Evidence:

- Review 5568049716 on unkannybanny PR 24 is `APPROVED` by github-actions[bot]. Its body shows `semdiff.py files <head> <base>` and then "No problems found".
- `plugins/s/integrations/copilot/copilot-review-gate.yml:349-386`: the prompt asks the model to diff the refs, and stdout is captured unfiltered.
- `plugins/s/integrations/copilot/copilot-review-gate.yml:715-723`: a parsed ship-it marker submits APPROVE.

### Scope and non-goals

The scope is the CLI path of the gate workflow, the contract template, and the room-wake reply job. The poll and review-event paths, `semdiff.py`, and the gate setup verbs are out of scope.

Evidence:

- In scope: `plugins/s/integrations/copilot/copilot-review-gate.yml:245-387` (reviewer) and `:406-1006` (publisher), `plugins/s/integrations/copilot/room-wake.yml:300-327`, `plugins/s/integrations/copilot/SKILL.md:36-37`.
- Out of scope: the poll loop at `plugins/s/integrations/copilot/copilot-review-gate.yml:488-527`, and `plugins/s/skills/review/scripts/semdiff.py`.

### Affected capabilities and files

Two capabilities each get new requirements, and seven files change besides the plugin manifest: the gate and room-wake templates and the contract, two test files, and the docs.

Evidence:

- Capability `copilot-review-skill`: new requirements `gate-review-grounding`, `gate-report-extraction`, `skill-supplied-grounding`, `ci-review-grounded-ships`. Capability `pr-room`: new requirement `room-wake-reply-cleaning`.
- Files: `plugins/s/integrations/copilot/copilot-review-gate.yml`, `plugins/s/integrations/copilot/SKILL.md`, `plugins/s/integrations/copilot/room-wake.yml`, `plugins/s/skills/build/tests/test_copilot_verb.py:1340-1835` (harness), `plugins/s/skills/room/tests/test_room_wake.py:537-614`, `docs/copilot-review-reference.md:40-61`, `docs/copilot-review.md:134-143`, `docs/room-wake-reference.md:80-91`, `plugins/s/.claude-plugin/plugin.json`.
- Runnable premise: on this repo, `python3 plugins/s/skills/review/scripts/semdiff.py files HEAD~2 HEAD` gave summary `{'files': 18, 'cohorts': 4}`. Swapping the refs gave `{'files': 0, 'cohorts': 0}` with exit 0. An unknown base ref exited 1 with "semdiff: unknown base ref".
- Runnable premise: `copilot --version` reports 1.0.80, and `copilot --help` lists `-s, --silent`: "Output only the agent response (no stats), useful for scripting with -p".
- Runnable premise: `docs_lint.py` on both copilot-review docs exits 0, with one existing passive-voice warning.

### No open task-shaping decision

All five task-shaping decisions are settled by planner defaults pending the user's review; none remain open.

Evidence:

- Ungrounded handling: Q1. Engine copy: Q2. File-count cross-check: Q3. Report extraction: Q4. Room cleaning: Q5. All five were settled by PLANNER after the oracle returned INSUFFICIENT.
- Where the status is posted from (step outputs, not files): settled by investigation of the trust boundary at `plugins/s/integrations/copilot/copilot-review-gate.yml:389-405`.
