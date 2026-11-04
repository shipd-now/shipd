# shipd-factory-docs
Status: verified
Planned-at: 624603afb43981b2335818d34a6a20bb1cd3a644
Gated-hash: f1c189e96eb1

## Idea

Rename the public App page to `docs/shipd-factory.md` and rewrite it for the renamed `shipd-factory` GitHub App, its setup verbs, the author opt-in and the live proofs.

### Motivation

A repo owner who finds the renamed `shipd-factory` App has no public page that tells them what it touches, how a repo is set up for it, or what has run live. The merged page still uses the old App name and "only draft tested", so the App's homepage URL cannot point at it.

### Details

- `git mv docs/factory-app.md docs/shipd-factory.md`, then rewrite it as a `concept` doc of at most 100 lines.
- Move the page requirement from capability `factory-app-docs` (REMOVED) to the new capability `shipd-factory-docs` (ADDED).

Affected capabilities: `factory-app-docs` (removed requirement), `shipd-factory-docs` (added). Impact: `docs/shipd-factory.md`; the website sync adopts it as a hidden page.

### Non-goals

- No name or link of the private source repository or any private repository on the page.
- No redirect from `/docs/factory-app`, which was never published.
- No change to code, and no agent merge of the pull request.

## Implementation

- The page states setup (`/shipd-factory onboard`, `/shipd-factory new`), the `factory.author_fixes` opt-in read from the default branch, and one sentence per live proof that passed. Rejected: a second how-to page, which needs a second manifest entry and URL.
- The merged capability `factory-app-docs` loses its only requirement, so the merge leaves an empty master that is `git rm`-ed in the same commit.
- A guard: a grep of `docs/shipd-factory.md` for the retired App name, the factory repo's path, a sibling repo name and an installation-settings URL prints nothing.

Risk: the page drifts from the private source; each fact is one sentence, so a later change edits one sentence.

## Readiness attestation

### Problem and motivation

The merged page names the old App and an outdated test caveat.

Evidence:

- `docs/factory-app.md` on `main`: title `The factory GitHub App` and "Only `draft` mode has an end-to-end test so far".

### Scope and non-goals

One page, one removed requirement and one added requirement.

Evidence:

- Non-goals above; no code changes.

### Affected capabilities and files

Capabilities `factory-app-docs` and `shipd-factory-docs`, and one page.

Evidence:

- `spec_status.py base-hash factory-app-docs factory-app-page` printed `a545bcdd6fc3`.
- Runnable premise: `docs_lint.py docs/shipd-factory.md` exits 0 at 99 lines.

### No open task-shaping decision

Every decision is settled.

Evidence:

- The page text is already written and linted; tasks record it.
