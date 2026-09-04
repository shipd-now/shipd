<!-- description: Read a shipd epic through the engine and explain it in under 100 lines — with a diagram only where one carries structure. -->
# /s:explain — explain an epic

Every other epic surface reports *state*; none of them says what an epic is
*for*. Turn one epic's artifact and its live delivery state into a short
explanation a person reads in one pass. You are **read-only**: you run two read
verbs and print prose. No file is created or edited, no artifact is emitted, no
status-changing verb runs, and the explanation is never offered as a document.

<!-- include:preamble -->

Both reads below run as `python3 "$S/spec_status.py" <verb …>` from the
repository root, so `--root` can be omitted. The invocation carries the epic
slug (`/s:explain <slug>`); without one, take step 4 straight away.

1. **Read the epic through the engine, and only through it.** Run
   `cat epic <slug>` for the artifact — its `## Introduction` and `### Non-goals`,
   `## Decisions`, `## Design`, and the `## Changes` member table with each
   member's description and Code / Integration / Unknowns / Risk ratings — then
   `epic-show <slug>` for live state: status, theme, a `shipped <n>/<m>` count,
   and every member sorted into the UNPLANNED / READY / BUILDING / SHIPPED
   lanes. Never open an epic path in the spec tree yourself, and never
   reconstruct an epic from recall. A non-zero exit from `cat epic` sends you to
   step 4 — not to reading files by hand. Those two outputs are the whole
   evidence base; read them fully before writing a word.
2. **Explain it, as response text, in under 100 lines of prose.** Fenced
   diagram blocks fall outside the count, and the 100 is a ceiling rather than a
   target — a two-member epic with a short introduction earns a few paragraphs
   and an ending. Padding toward the cap is a failure. Cover four things, in
   order:
   - **what the epic is and why it exists**, from the introduction (and the
     non-goals, where they sharpen the boundary) — the problem it exists to
     solve, not only the solution it chose;
   - **the load-bearing decisions**, from the decisions section: the ones the
     rest of the epic rests on, each with its reason. Skip incidental taste;
   - **how the members compose**, from the design and the member table — what
     each member contributes, what depends on what, which seam each one owns,
     rather than a row-by-row restatement;
   - **where delivery stands now**, from `epic-show`: status, shipped progress,
     which members sit in which lane, what is in flight and what is unplanned.
   Write light headings and plain prose for someone who has never opened the
   epic, and prefer the epic's own vocabulary to your paraphrase so the
   explanation stays searchable by the same terms.
3. **Add a diagram only when one is earned.** A picture belongs here when the
   structure is genuinely faster to read than the equivalent prose: members
   ordered along a dependency chain, a pipeline the work flows through stage by
   stage, or hand-offs between actors where who-calls-whom is the point. A flat
   list of independent members gets **no diagram** — a decorative architecture
   picture spends length and carries nothing. When one is earned, draw at most
   one, as swimlane-style ASCII in a fenced block or as a mermaid block, and
   only over relationships the design, decisions, or member table actually
   state: every node is a member change, actor, or stage those sections name.
   Never invent an ordering the artifact does not assert.
4. **No slug, or a slug the engine cannot resolve — list the roster and stop.**
   This covers both a bare invocation (nothing to explain, no error to report)
   and a `cat epic` that exited non-zero. Report the engine's error line
   verbatim when there was one, then run `config-show` and read its
   `content-dir: <dir>` line; list the available epic slugs as the child
   directory names of `<content-dir>/epics/`, taken from a plain directory
   listing — a read, so the read-only contract holds. Where that directory is
   absent or empty, say no epics are installed here. Do **not** use the bare
   board as the roster: a selected change preempts it, so it is not a reliable
   list of epics. Then stop — on a bare invocation, ask the user to pick a slug
   and re-run; on an unresolvable slug, stop after the error and the roster.
   Never fuzzy-match a near neighbour, and never explain an epic you did not
   read. An epic authored in another worktree and not yet merged is invisible
   from here, which is exactly why the roster is reported instead of guessed.
