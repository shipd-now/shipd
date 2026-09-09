<!-- description: Interrogate a product idea into a lint-clean workspace PRD, installed through the engine's staged emit. -->
# /s:prd — interrogation into a workspace PRD

A PRD is the discover rung of Initiative → PRD → Epic → Change: what problem,
for whom, and what success looks like, recorded before anything is decomposed.
PRDs live in the workspace, not the repo. Investigate, grill the user section
by section, install through the engine — never hand-write the store's path or a
`Status:` line, and never decompose the PRD yourself.

<!-- include:preamble -->

## Resolve the workspace first

Run `shipd workspace` before anything else: it prints the workspace root, the
declared project slugs, and every initiative with its status and scope — not
PRDs, which only the search below surfaces. If no workspace resolves, report
the error verbatim, say that PRDs live in the workspace rather than the
repository, point the user at `/s:workspace init`, and write nothing — there is
no repo-local fallback.

## Investigate before you ask

Retrieve against the idea's terms with `shipd search <term> [term...]`, which
ranks the spec library, the wiki, the workspace's initiative briefs and PRDs,
and this repo's git-tracked code files. Read the top hits and the roster, then
bring what you found into the interview as **stated context, never as a
question** — anything discoverable is never asked. Where the search surfaces a
PRD already covering this ground, say so and let the user choose between
extending it (`--replace`, below) and a distinct slug.

## Pick the tier, announce it, keep it correctable

The tiers nest additively: `basic` is `## Problem`, `## Solution`,
`## Success criteria`; `standard` adds `## Users`, `## Requirements`,
`## Non-goals`; `comprehensive` adds `## Risks`, `## Rollout`,
`## Open questions`. **Start at `standard`** and state the choice and its
reason in one sentence. Escalate to `comprehensive` on multi-project blast
radius, regulatory weight, a phased rollout, or several user classes;
de-escalate to `basic` for a small self-contained idea. Announce a switch when
it happens — it never restarts the interview, since answered sections survive
an escalation and extra answers stay legal after a de-escalation.

## Grill, one section per round

Work the active tier's sections in order, 2–4 focused questions per round,
folding the answers in before opening the next. This multi-round interrogation
is deliberate: a PRD is only as good as the thinking it records. Ground every
round in what you read, offer concrete options with the recommended default
first, and press again on an answer too thin to write down — "faster" is not a
success criterion. Never author filler for a section the user gave you nothing
for.
<!-- if:question-dialogs -->
Put each round in a single question dialog.
<!-- else -->
End each round as plain text with its questions numbered, options lettered,
default first, and wait for a typed reply.
<!-- end -->
Confirm the kebab-case slug in the first round — it becomes the PRD's directory
and its `# ` title.

## Compose and install

Fill the tier's template: the title placeholder takes the slug, and each italic
guidance line is replaced wholesale by the section's content. Keep
`Status: draft` and the `Template:` line naming the active tier. Add
`Initiative: <slug>` only when the user names a parent initiative that actually
resolves; it is the only other recognized header key.
<!-- if:file-references -->
Read `{refs}/prd.md` for the header grammar, the tiers' section lists, and the
install rule.
<!-- else -->
This harness cannot open a companion reference file, so the linter's full rule
set is unavailable here. Say so, author from the shape above, and let the
install below be the check — it names exactly what to fix.
<!-- end -->
Author into a staging file — never the workspace path, which the engine owns —
and install through the engine, which validates and on any finding restores
what it replaced and exits non-zero:

```
python3 "$S/spec_emit.py" prd <slug> --from <staging-file>
```

Fix the staged file and re-run until it exits `0` (add `--replace` to overwrite
an existing PRD), then read it back with `python3 "$S/spec_status.py" cat prd
<slug>`. This lands in the workspace, outside the repo, so there is no PR.

## End at the installed PRD

Summarize the slug, where the engine installed it, the tier and why, and what
each section settled. Approval is a later re-install carrying
`Status: approved` through the same verb with `--replace` — never a hand-edited
header. Then point the user at `/s:epic` on its own line: an epic born from
this PRD carries `PRD: <slug>`. Stop there — this command never decomposes the
PRD itself.
