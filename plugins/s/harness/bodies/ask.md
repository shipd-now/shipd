<!-- description: Consult the ask-mikk oracle before interrupting a person — one compact question answered from durable knowledge, or queued for a human. -->
# /s:ask — one compact question → mikk's standing verdict

Turn the user's request into one compact question, answer it from durable
knowledge — the workspace wiki and this repo's spec surfaces — and relay the
verdict. You never answer from your own opinion, and you never act on the
answer.

<!-- include:preamble -->

Every wiki verb below runs as `python3 "$S/spec_status.py" --root <repo-root>
<verb …>`, where `<repo-root>` is the invoking repo.

1. **Shape one compact question** — a decision-ready unit with exactly three
   parts: **Decision** (the one thing to be decided, stated as a question),
   **Options** (the concrete choices under consideration), and
   **Recommendation** (your lean, for the durable sources to confirm or
   overturn). Infer all three from the request and the repo; run no clarifying
   round. A request too thin to shape into a decision is refused, not guessed
   at — ask the user to restate it as a decision and stop there.
2. **Consult durable knowledge**, in this order:
<!-- if:subagents -->
   Delegate the search to a non-interactive helper agent, handing it the
   compact question, the repo's absolute root, and `$S/spec_status.py`; it
   returns a verdict and asks nothing back. Run the search yourself when no
   helper is available.
<!-- end -->
   - `wiki-show` — the store's root and health. It fails naming a missing
     workspace or store: there is no durable knowledge, so go to step 4.
   - `cat wiki index`, then `cat wiki <slug>` for every page bearing on the
     decision.
   - widen with read-only `grep` under the store root, then to the repo's own
     surfaces — `shipd epic <slug>`, `cat verified <capability>`, `cat change
     <slug>`. Read only; never edit a store file.
3. **Answer only from a cited position.** A source qualifies when it states a
   position on *this* decision — a neighbouring decision does not count. Relay
   it with a `Cited:` line naming the wiki page (`[[slug]]`), answered queue
   block (`q-<slug>`), or repo artifact behind it, and an `Evidence:` line
   quoting that source verbatim. Take the stance the source takes; do not
   dilute it into a menu of alternatives. An answer with no citation or no
   verbatim quote is an ungrounded opinion — say plainly that you demoted it,
   and go to step 4.
4. **Insufficient — queue the decision, then ask the user.** Queue it first, so
   the next run can cite the reply (scaffold with `wiki-init` when the store is
   missing; skip the queue entirely when no workspace is discoverable):
   ```sh
   python3 "$S/spec_status.py" --root <repo-root> wiki-queue-add <slug> \
     --question "<decision>" --options "<options>" \
     --recommendation "<lean>" --origin "ask"
   ```
   Then put the question to the user, once — never a multi-round interview.
<!-- if:question-dialogs -->
   Ask it as a single self-contained AskUserQuestion dialog carrying the
   decision and enough context to stand on its own, with the recommendation
   listed first so accepting the lean is the cheapest reply. Never treat a
   rejected or interrupted dialog as a decline — re-offer the same options as
   a numbered list and wait for a typed reply.
<!-- else -->
   Ask it as a plain-text numbered list of the options, the recommendation
   first, and read the answer from the user's typed reply.
<!-- end -->
5. **Capture the reply against the queued block.** Distill it into one or two
   durable sentences — the position chosen and the reason given, stripped of
   session chatter — then:
   ```sh
   python3 "$S/spec_status.py" --root <repo-root> wiki-queue-answer <slug> \
     --answer "<the distilled answer>"
   ```
   Pass the bare `<slug>`; the verb prefixes `q-` itself. A non-zero exit is
   reported, never fatal — capture never blocks the reply. Where nothing was
   queued, relay the answer for **this session only** and say plainly that
   nothing durable was captured; `/s:workspace` is what makes the next answer
   stick.
6. **Report the verdict and stop.** You relay and capture; you do not act on
   the decision. Correcting an already-captured answer is `/s:teach`'s job, and
   a decision you now want built goes to `/s:plan`.
<!-- if:file-references -->
   The verdict grammar, the demotion rule, and the capture edge cases are
   written out in {refs}/ask.md.
<!-- else -->
   The verdict grammar, the demotion rule, and the capture edge cases are not
   available as a separate file here. Say so if the user asks for them, state
   that you would have read the ask reference for that detail, and answer from
   the cited source's own text — it is quoted in the verdict you relayed.
<!-- end -->
