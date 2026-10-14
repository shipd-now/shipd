<!-- doc-type: reference -->

# The shipd question brief

Every question a shipd skill puts to the user opens with a short brief. The
brief tells the user what the decision is about, why it matters, and what
each option causes. This file defines the brief, says where it goes, and
shows four worked examples.

## The four parts

Write the parts in this order.

1. **The decision.** A bold heading in plain words. Add the member and `Q<n>`
   in brackets where the skill tracks them.
2. **Why it matters.** One or two sentences on what the feature does and what
   the answer changes.
3. **An example.** One concrete command, input, or scenario. Leave it out
   only when the decision has no concrete instance.
4. **The options.** Lettered, with the recommended option first and marked
   "(recommended)". Each option says what choosing it causes.

## Where the brief goes

Use a plain-text numbered typed round when a round has more than one
question, or when any brief runs past one line. The user answers like
"1a 2b".

Use a dialog only for one self-contained question. Its brief rides in the
question text and the option descriptions. The turn carries no other prose.

## Worked examples

### An epic-grill typed round

Before: "room-cli-verb Q2 — default `--state` for a `--task` reply when
omitted?"

After:

```text
**Reply state when `--state` is left out (room-cli-verb, Q2)**

Why it matters: `shipd room message --task <id>` posts an agent's reply on
a PR task. Each reply carries a state that tells the room whose turn it is.
This decides the state when the caller omits it.

Example: `shipd room message --task t1 --to alice "Does this cover
retries?"` hands the turn to alice.

a) Use `input-required` with `--to`, otherwise `working` (recommended). A
reply addressed to someone hands them the turn.
b) Require `--state`. Every caller must name it; a missing flag exits with
a usage error.
```

### An epic scoping typed round

Before: "Include the GitHub Action wake-up in this epic?"

After:

```text
**Scope: the automatic wake-up**

Why it matters: The epic lets agents talk over PR comments. Without a
wake-up, an agent sees a comment only when someone runs `room watch`. With
one, a GitHub Action starts the agent when a comment arrives.

Example: alice comments "@claude retry this" and the agent answers within
a minute, with nobody at a terminal.

a) Plan it as its own member (recommended). It ships after the core verbs
and can be cut alone.
b) Leave it out. Record it under Out of scope for a later epic.
```

### A forget confirm dialog

Before: "Remove memory-diagram-style?"

After, in the question text: "Remove memory-diagram-style? It tells /s:plan
to draw Mermaid flowcharts, not ASCII. After removal, plans fall back to the
default style."

The options are "Keep it (Recommended)" and "Remove it: deletes the page and
its index entry".

### A workspace sync dialog

Before: "How should sync handle members?"

After, in the question text: "3 of 5 member repos are missing here, and 2
already have local checkouts. Sync can reuse them or clone fresh copies."

The options are:

- "Reuse what I have (Recommended): maps the 2 and clones only the 3
  missing"
- "Clone everything fresh: re-clones all 5 into the workspace"
- "Review one by one"

## A bad question

The original epic-grill dialog read: "room-cli-verb Q2 — default `--state`
for a `--task` reply when omitted?"

It lacked three parts:

- **The decision in plain words.** It used a flag name and a question number
  where a sentence belonged.
- **Why it matters.** It never said what the verb does or what the answer
  changes.
- **An example and lettered options.** It showed no command and no choices,
  so the user had to guess what each answer would cause.
