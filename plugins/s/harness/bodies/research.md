<!-- description: Turn a question into a cited research report, installed through the engine so an epic can link it. -->
# /s:research — question → searched, cited research report

Turn a question into a report whose every load-bearing claim is anchored to a
source you actually fetched, installed into the content directory's `research/`
folder. You search, compose, install, and stop — you plan and build nothing
from what you find.

<!-- include:preamble -->

## 1. Check the ground before searching

Confirm the layout resolves with `python3 "$S/spec_status.py" config-show`; if
no content directory resolves, report that and stop rather than invent a path.
Search with the session's built-in web-search and page-fetch tools and
**nothing else** — no API keys, no external research service. If live web
access is unavailable, say which tool is missing and stop: never write findings
from memory, because an uncited report defeats the artifact's purpose. Then
create the report's worktree (`"$S/worktree.sh" research-<slug>`) and work
inside `.worktrees/research-<slug>`.

## 2. Clarify only when the question is unresearchable

A question specific enough to research goes straight to step 3. Ask only when
you can infer no scope, audience, or success criterion at all — then one round
of 2–3 questions, concrete options, recommended default first, and converge.
<!-- if:question-dialogs -->
A single self-contained question may use a question dialog in a turn carrying
no other prose; a round that needs a scope brief alongside it stays plain text.
<!-- else -->
End the turn as plain text with the questions numbered, options lettered,
default first, and wait for a typed reply.
<!-- end -->

## 3. Decompose → search → select → extract

1. **Decompose** the question into 3–6 bounded sub-questions that together
   cover it; each is a distinct searchable angle.
2. **Search** each one and read the result surface — titles, snippets, domains
   — to judge what is worth fetching.
3. **Select** the strongest sources: primary and authoritative (official docs,
   standards, the vendor, first-party writing) over aggregators, recent ones
   where the topic moves. Drop the weak rather than pad the report.
4. **Extract** by fetching each selected source and taking only the findings
   its text supports, recorded with the source that anchors them. Corroborate
   load-bearing claims where you can, and record source disagreement rather
   than smoothing it over.

## 4. Compose the report

Line 1 is a non-empty `# <title>`. Then a `## Summary`, one `## <Theme>`
section per sub-question, a `## Gaps & caveats` section, and a numbered
`## Sources` list of the sources you actually fetched. Every load-bearing claim
carries an inline `[n]` marker whose number appears in that list. A claim you
could not anchor to a fetched source is **downgraded into gaps & caveats** —
never asserted as a finding.
<!-- if:file-references -->
Read `{refs}/research.md` for the report grammar and the citation rules the
engine's checks enforce.
<!-- else -->
This harness cannot open a companion reference file, so the full report grammar
is unavailable here. Say so, compose from the shape above, and let the install
below be the check — it validates the citation skeleton and names what to fix.
<!-- end -->

## 5. Install through the engine

Author into a staging file outside the content directory, then let the engine
install it — never write a `research/` path yourself:

```
python3 "$S/spec_emit.py" research <slug> --from <staging-file>
```

It validates in place and, on any finding, removes what it installed and exits
non-zero. Fix the staged file and re-run until it exits `0`; never finish on a
non-zero emit. Pass `--replace` only to deliberately overwrite an installed
report, and read the result back with
`python3 "$S/spec_status.py" cat research <slug>`.

## 6. Ship and hand off

Commit `research/<slug>/report.md` on `change/research-<slug>`, open a PR, let
it auto-merge, and report the PR with its full URL. Summarize the slug, the
sub-questions, the headline findings, and the open gaps, then tell the user the
report is ready to feed `/s:epic` as a `## Research` link. Stop there.
