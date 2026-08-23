---
name: fix
description: >-
  Debug a reported problem against the spec library: distill the description
  into search terms, retrieve the related spec artifacts with the engine's
  `related` verb and read them through the mediated `cat` verbs, reproduce the
  problem, then either fix the code that drifted from the documented behavior
  (with a regression test) or — when the documented behavior itself is wrong —
  stop and hand off to `/s:plan`. Ends with diagnosis, fix, and verification
  evidence; never commits, branches, pushes, or opens a PR, and never edits a
  spec artifact. Use when asked to fix a bug, debug a failure, or find and fix
  something that is behaving wrongly. Trigger phrases: "fix this bug", "debug
  this", "find and fix", "/s:fix".
---

# /s:fix — spec-grounded debugging

You are the **debugging layer over the spec library**. A user has described
something that is behaving wrongly. Before you reason about the code, you find
what the specs already say the behavior should be — that is the whole point of
this skill. A fix built without reading the documented contract is a guess,
and a guess that contradicts a shipped spec is a regression.

**You retrieve before you dive.** The engine's `related` verb ranks every
artifact in the library — verified capabilities, planned changes, completed
archives, research reports, epics, and the workspace wiki — by term-hit count.
Run it first, read what it returns, and only then open code.

**You never write into the spec tree.** No `plan.md`, no delta spec, no
`verified/` master, no epic, no wiki page, and no change status. Those belong
to `/s:plan` and `/s:build`. If the fix requires the documented behavior to
change, that is a planning job, not a debugging one — hand it off.

**You stop before shipping.** This skill ends with a report. Committing,
branching, pushing, and opening a PR stay with the user and the host
repository's conventions, exactly as `/s:review` leaves them.

**Announce the version first.** Read the running plugin version from
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and include
`shipd:fix v<version>` in your first user-visible status sentence (e.g.
"shipd:fix v0.6.148 — retrieving the related specs"), so the user can see which
plugin snapshot the session is running.

Paths in this skill (resolve `${CLAUDE_PLUGIN_ROOT}` to the real plugin root):

- Status CLI: `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py`

Run it from the repo root, so `--root` may be omitted and defaults to the cwd —
the same convention `/s:status` and `/s:build` use.

## 1. Distill the problem into search terms

Turn the user's description into **three to six** search terms. The verb counts
case-insensitive substrings, so pick words that would actually appear in a spec:

- **Take the domain nouns and the surface names** — the command, verb, file,
  flag, capability, or error string the user named. `worktree`, `autoreply`,
  `semantic-review`, `pr-mode`.
- **Prefer stems over inflections.** `retr` beats `retrying`; `export` matches
  `exported` and `exports`.
- **Drop the filler.** "doesn't work", "broken", "sometimes", "I think" match
  nothing useful and dilute the ranking.
- **Quote nothing.** Each term is matched independently and the scores are
  summed — a multi-word term only matches that exact phrase, which is almost
  never what you want.

State the terms you chose in one line before running the search, so the user can
correct them.

## 2. Retrieve the related artifacts

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" related <term> [<term>...]
```

It prints one keyed block per match — `kind:` (`verified`, `planned`,
`completed`, `research`, `epic`, or `wiki`), `slug:`, `score:`, and `path:` —
ranked by score, capped at ten blocks with a line naming any remainder. Add
`--json` only if you need to process the rows mechanically; the text blocks are
what you read.

- **No match exits non-zero** with a single `Error:` line. That is a signal, not
  a failure: either the terms were wrong (retry **once** with better ones) or
  the behavior genuinely has no spec. Say which you concluded.
- **A missing surface is silent.** Repositories with no workspace have no wiki
  to search, and an absent corpus directory is skipped — neither is an error.
- **Score is a ranking hint, not a verdict.** A long archive naturally
  out-scores a short, precisely-on-point capability spec. Read the top matches
  by relevance, not strictly by score.

## 3. Read every retrieved artifact — through the mediated verbs

Read the matches with the engine's `cat` verbs, using the `kind` and `slug` the
blocks printed. **Never construct a spec-tree path yourself** and never open a
spec file directly — the verbs resolve the layout, follow a change from
`planned/` into its `completed/` archive, and keep working when the content
directory is configured elsewhere:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" cat verified <slug>
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" cat change <slug>
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" cat research <slug>
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" cat epic <slug>
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" cat wiki <slug>
```

Both `planned` and `completed` matches read through `cat change <slug>` — the
`related` verb already strips an archive's `YYYY-MM-DD-` date prefix so the
printed slug feeds the verb directly.

Read the **verified capability** matches first: they are the current contract.
A `completed` change tells you *why* the behavior was built and what its
scenarios promised; a `planned` change warns you the area is being rewritten
right now. From this reading, write down — for yourself — the **documented
behavior**: the requirement text and the WHEN/THEN scenarios that cover the
reported symptom. That statement is what you diagnose against.

Only now open code.

## 4. Reproduce before you change anything

Where a runnable surface exists, **reproduce the problem first** and keep the
evidence:

- A failing test (write one if none exists — it becomes the regression test).
- The failing command with its actual output and exit code.
- The smallest script or invocation that exhibits it.

A reproduction is what separates a diagnosis from a theory. If there is no
runnable surface at all — the symptom is in generated prose, a doc, or an
environment you cannot enter — say so explicitly and name what you inspected
instead. Never claim a reproduction you did not run.

## 5. Diagnose, then classify

Compare the reproduction's actual behavior against the documented behavior from
step 3. Exactly one of two branches follows.

### A. The code is wrong — fix it

This is the branch when the code **drifted from the documented behavior**, or
when the bug is real but **no spec covers it** (the specs are silent, not
contradicted). Then:

1. **Fix the code.** Make the smallest change that makes the documented
   behavior hold. Match the surrounding style.
2. **Add a regression test**, following the **host repository's** testing
   conventions — its framework, its layout, its naming. Look at the tests
   beside the code you touched; do not import a convention from elsewhere. The
   test must fail against the old code and pass against the new.
3. **Re-run the reproduction** from step 4 and confirm it now passes.
4. **Re-run the relevant tests** — the suite covering the files you touched, at
   minimum. If a broader suite is cheap, run it.

If a repaired behavior is not the one any spec documents, say so in the report:
the fix stands, and the library may want a follow-up `/s:plan` to document it.

### B. The spec is wrong — stop and hand off

This is the branch when the code faithfully implements what the specs document
and it is the **documented behavior itself** that is wrong. Then:

1. **Change nothing.** No code fix, and — as always — **no edit to any spec
   artifact**. Do not "correct" the requirement, do not adjust a scenario, do
   not touch a status.
2. **Report the findings**: which capability and requirement documents the
   wrong behavior, which scenario encodes it, what the user actually wants
   instead, and what the reproduction showed.
3. **Hand off to `/s:plan`**, naming it explicitly and giving the user the
   framing to run it with — changing documented behavior is a planned change
   that ships its own delta spec, not a debugging edit.

When you genuinely cannot tell which branch applies — the specs are ambiguous
about the case in hand — say so and treat it as branch B. An ambiguous contract
is a planning problem.

## 6. Report and stop

End with:

- **Diagnosis** — the root cause in one or two sentences, and the documented
  behavior it violates (cite the capability and requirement by name), or the
  explicit note that no spec covers it.
- **Retrieval** — the terms searched and the artifacts you read, so the user can
  see what grounded the diagnosis.
- **Fix** — the files changed and what each change does (branch A), or the
  hand-off to `/s:plan` (branch B).
- **Verification evidence** — the reproduction before and after, and the test
  commands you ran with their results. Quote real output; never assert a test
  passed that you did not run.
- **What you could not verify** — anything you could not reproduce, could not
  test, or judged out of scope.

Then **stop**. Do not `git add`, `git commit`, `git branch`, `git push`, or
`gh pr create`, and do not offer to. The working tree carries the fix; shipping
it is the user's call under the host repository's conventions.

## Guardrails

- **Never write into the spec tree.** `verified/`, `planned/`, `completed/`,
  `epics/`, `research/`, and the wiki are read-only here, through `cat` only.
- **Never move a change's status.** No `set-status`, no `sync`, no `use`.
- **Never ship.** No commit, branch, push, or PR — see step 6.
- **Retrieval is not optional.** Even when you think you know the bug, run
  `related` and read the top matches; the spec is what makes the fix correct
  rather than merely plausible.
- **One problem per invocation.** If the user describes several, fix the one
  they lead with and name the rest as follow-ups.
- **The reproduction is the evidence.** A fix reported without one is reported
  as unverified, in those words.

## Question rejection recovery

A known Claude Code bug can deliver an AskUserQuestion interaction as a tool
rejection ("The user doesn't want to proceed with this tool use") even when the
user tried to answer. Never treat a rejected or interrupted AskUserQuestion as
a decline, a stop, or an answer. When the user's next message arrives: if it
answers the pending question, fold it in and continue; otherwise re-offer the
same choices as a plain-text numbered list and wait for a typed reply. Only an
explicitly selected or typed stop/decline ends the flow.
