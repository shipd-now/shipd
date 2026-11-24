# Verbatim review text

Each block below is inserted exactly as written. The task that applies a block
names its target file and position.

## Block A — `SKILL.md` step 3 bullet

One line, added directly after the `**Uneven sibling sites**` bullet:

```
- **Consumers in another repository** — read each at a named ref, linked pull request heads first.
```

## Block B — `references/call-site-tracing.md` section

Inserted between the `## Downstream impact` section and the
`## Call-site values — reachability and comment accuracy` section:

```
## Consumers in another repository

`context` searches the reviewed repository only. A consumer in another repository needs its own lookup, and that lookup needs a ref.

- **Name the ref on every read.** A `gh api repos/<owner>/<repo>/contents/<path>` call with no `ref` answers from the default branch. Resolve the default branch to a commit id first, and pass `?ref=<commit id>` on every read.
- **List the linked pull requests first.** Where a pull request is in scope, run `python3 "$CLAUDE_PLUGIN_ROOT/skills/review/scripts/review_gate.py" linked <pr> --repo <owner>/<repo> --search <symbol>`. It prints each pull request linked to the reviewed one, and each open pull request in the consumer repository matching the symbol, with its state and head commit.
- **No pull request in scope.** Skip `linked` and run `gh pr list --repo <owner>/<repo> --state open --search <symbol> --json number,url,headRefOid` yourself.
- **Read the consumer at each listed head, then at the default branch.** A migration often waits in an open pull request while the default branch still holds the old code.
- **A head that migrates the consumer ends the check.** Raise no un-updated-consumer finding. Name that pull request in the walkthrough, so the reader sees that the two changes merge together.
- **No ref migrates it: report it, with the refs.** Rate it by the rubric as usual. The finding's `why` names every ref you read, as `<owner>/<repo>@<commit id>`, and every pull request the listing returned.
- **A failed lookup is a could-not-verify entry.** Where `linked` or a read fails, or you lack access to the repository, name the consumer and the failed call under what you could not verify. A consumer read at the default branch alone supports no `high` or `medium` finding.
```

## Block C — `references/posting.md` step 2 paragraph

Appended to flow step 2 ("Fetch both resolved commits, then review by commit
id"), as a new paragraph indented to the step's body:

```
   Where the review checks a consumer in another repository, list the
   linked pull requests before judging it:
   `review_gate.py linked <number> --repo <owner>/<repo>`. The target pull
   request's own commits never show a migration that waits in another
   repository. `references/call-site-tracing.md` gives the procedure.
```

## Block D — `integrations/copilot/SKILL.md` section 3 bullet

Added as the last bullet of `### 3. Check downstream impact`:

```
- A consumer in **another repository** is never judged from its default
  branch alone. Read it with an explicit `?ref=<commit id>`: first at the
  head of each pull request GitHub cross-references on this one
  (`gh api repos/<owner>/<repo>/issues/<number>/timeline`), then at the
  default branch. A head that migrates the consumer means no finding. Where
  a lookup fails, say you could not verify that consumer and raise nothing
  blocking for it.
```

## Block E — `harness/bodies/review.md` step 4 sentences

Two lines only: the rendered body must stay under its 150-line ceiling
(`plugins/s/skills/build/tests/test_harness_bodies.py`).

Appended to the end of step 4 ("Chase every changed signature to its call
sites"), indented to the step's body:

```
   A consumer in another repository: read it with `?ref=<sha>` at each head
   from `gh api repos/<o>/<r>/issues/<n>/timeline`; a failed read never blocks.
```
