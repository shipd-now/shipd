<!-- description: Debug a reported problem against the spec library, fix the code, and stop at the report. -->
# /s:fix — spec-grounded debugging

Find what the specs already say the behavior should be, then diagnose the code
against it. Retrieval comes before code, reproduction before any edit, and the
flow ends at a report — it never commits, pushes, or opens a pull request, and
it never writes into the spec tree.

<!-- include:preamble -->

## 1. Distill the description into search terms

Turn the reported problem into three to six terms the specs would actually
contain: the command, verb, file, flag, or error string that was named. Prefer
stems (`retr`) over inflections (`retrying`), drop filler like "broken" or
"sometimes", and keep each term a single word — terms are matched independently
and their hit counts summed, so a multi-word phrase matches almost nothing.
State the chosen terms in one line so the user can correct them.

## 2. Retrieve the related artifacts

Run `python3 "$S/spec_status.py" related <term> [<term>...]`. It ranks every
artifact in the library — verified capabilities, planned changes, completed
archives, research reports, epics, and the workspace wiki — by
case-insensitive term-hit count, printing a keyed block per match with its
`kind`, `slug`, `score`, and `path`, top ten first plus a remainder line.

A non-zero exit with a single `Error:` line means nothing matched: either the
terms were wrong — retry once with better ones — or the behavior genuinely has
no spec. Say which you concluded. A repository with no workspace has no wiki to
search and an absent corpus directory is skipped; neither is a failure. Score
ranks, it does not decide: a long archive naturally out-scores a short,
precisely on-point capability spec.

## 3. Read the matches through the mediated verbs

Read each match with `python3 "$S/spec_status.py" cat <kind> <slug>`, using the
kind and slug the blocks printed — `verified`, `change` (for both `planned` and
`completed` matches, whose slug is already date-stripped), `research`, `epic`,
or `wiki`. Never assemble a spec-tree path by hand: the verbs resolve the
layout, follow a change into its archive, and keep working when the content
directory is configured elsewhere.

Read the verified capabilities first — they are the current contract. A
completed change explains why the behavior was built and what its scenarios
promised; a planned one warns that the area is being rewritten right now. Write
down the documented behavior — the requirement text and the WHEN/THEN scenarios
covering the reported symptom. That statement is what you diagnose against.
Only then open code.

## 4. Reproduce before changing anything

Where a runnable surface exists, reproduce the problem and keep the evidence: a
failing test (write one if none exists — it becomes the regression test), or
the failing command with its real output and exit code. If nothing runnable
exists, say so plainly and name what you inspected instead. Never claim a
reproduction you did not run.

## 5. Classify, then act

Compare the reproduction against the documented behavior. Exactly one branch
follows.

**The code drifted from the spec, or no spec covers the bug.** Make the
smallest change that restores the documented behavior, in the surrounding
style. Add a regression test following the host repository's own testing
conventions — its framework, layout, and naming, read from the tests beside the
code you touched — and confirm it fails against the old code. Re-run the
reproduction, then the suite covering the files you touched.

**The documented behavior itself is wrong.** Change nothing: no code fix, and
no edit to any spec artifact — do not correct the requirement, adjust a
scenario, or move a status. Report which capability and requirement document
the wrong behavior, which scenario encodes it, and what is wanted instead, then
hand off to the planning workflow, naming it explicitly. Changing documented
behavior is a planned change that ships its own delta spec. When the specs are
too ambiguous to tell the branches apart, treat it as this one.

## 6. Report, then stop

Close with the diagnosis and the documented behavior it violates (cited by
capability and requirement), the terms searched and artifacts read, the files
changed or the hand-off, the verification evidence — reproduction before and
after, plus the test commands and their real output — and an explicit list of
what you could not verify. Then stop: no `git add`, no commit, no branch, no
push, no pull request, and no offer to do any of them. The working tree carries
the fix; shipping it is the user's call under this repository's conventions.
