<!-- description: Run the guided nine-step shipd tour the user drives one step at a time. -->
# /s:onboard — the guided shipd walkthrough

Teach a newcomer how shipd works through a fixed nine-step tour the user
drives by hand. Render exactly one step per turn and stop at its navigation
line — never auto-advance, and never create or modify a single file in the
user's real repository.

<!-- include:preamble -->

## 1. Resolve the step from disk

Progress lives in `~/.shipd/onboarding/state.json`, shaped
`{"step": <1-9>, "sandbox": "<abs path>"}`, over a throwaway sandbox:
`SANDBOX="$HOME/.shipd/onboarding/sandbox"`. Act on the invocation argument:

- **no argument, no state file** → a fresh start: scaffold the sandbox, write
  the state at step 1, and render step 1.
- **no argument, state file present** → resume: read its `step` and render
  that step. Never re-scaffold and never restart at step 1.
- **`next`** → increment the step, never past 9, write it back, render it.
- **`back`** → decrement the step, clamped at 1, write it back, render it
  again. It is offered on the explainer steps only.

A message naming neither `next` nor `back` is neither a stop nor a restart:
answer it, re-render the current step, and restate its navigation line.

## 2. Scaffold the sandbox — fresh start only

Copying, not authoring: the tour ships a pre-built example, so this is
near-instant. Copy the plugin's sandbox template into `$SANDBOX`, run
`git init "$SANDBOX"`, then write the state file. The template brings a real
content-directory layout — an empty master library and one change,
`add-board`, already authored and lint-clean under `planned/` — that gives a
single-file kanban app two read views. Never author the example live, and
never read the user's real repository for example shapes.

## 3. Pace it as a lesson, not a batch

- Explain before doing: a sentence of intent precedes every action.
- One step per turn — render it, end on its navigation line, and stop.
- Teach in short paragraphs, and quote at most a few lines of any file.
- Never fabricate engine output: run the command and show what it printed.
- Never narrate troubleshooting or command-syntax discovery.

## 4. Render the current step
<!-- if:file-references -->
Each step's directive — what to explain, what to quote, and how to close — is
written out in {refs}/onboard.md. Read that step's entry before rendering it.
<!-- else -->
The per-step directives are not available as a separate file here. Say so at
the start of the tour, state that you would have read the onboarding reference
for each step's content, and run the tour from this outline instead: **1** what
spec-driven development is, opening with the shipd banner; **2** how shipd
turns a spec into artifacts executed inside an isolated worktree; **3** the
three artifacts — `plan.md`, the delta spec, and `tasks.md`; **4–6** short
excerpts of the sandbox change's own three artifacts, closing on why the
strongest model plans and a cheaper one executes; **7** a short recap;
**8** the real build below; **9** the handoff below.
<!-- end -->

## 5. Step 8 — build the example for real

Run the engine over the sandbox change, each command preceded by a sentence of
intent and followed by its real output. The step is idempotent: when
`$SANDBOX`'s `completed/` already holds the archived change, skip the build and
re-show the summary instead. Every invocation carries the sandbox as its root:

```sh
python3 "$S/spec_lint.py" add-board --root "$SANDBOX"
python3 "$S/spec_status.py" --root "$SANDBOX" set-status ready add-board
# copy the shipped reference implementation into the sandbox root
bash "$S/claim_task.sh" claim add-board       # claim/complete until pending=0
python3 "$S/spec_status.py" --root "$SANDBOX" set-status complete add-board
python3 "$S/spec_status.py" --root "$SANDBOX" set-status verified add-board
python3 "$S/spec_merge.py" add-board --root "$SANDBOX"
```

Then say what happened in a few sentences — the change moved from `planned/`
to `completed/` and its requirements seeded the master library — run the built
app once to show it working, and hand the learner a copy/paste block that runs
it themselves.

## 6. Step 9 — hand over their own first plan

Suggest one small enhancement to the sandbox app, explain in a sentence that
the sandbox is a real shipd library so planning there lands a new change in
its `planned/`, and print the copy/paste block that opens a session in the
sandbox and runs `/s:plan` on that enhancement. Then offer cleanup — delete
the sandbox, or keep it and report its path — and never delete without the
user choosing to.
<!-- if:question-dialogs -->
That cleanup offer is the one prompt in the tour that may be a question
dialog, because its turn carries no step content; every navigation line stays
plain text.
<!-- end -->
This is the last step: there is no `next`, though `back` still returns to
step 8.
