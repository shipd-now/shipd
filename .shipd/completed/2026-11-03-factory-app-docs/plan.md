# factory-app-docs
Status: verified
Planned-at: 90b4ac75747c6892b128310a342d623b8b65b9f4
Gated-hash: 3672bae9be7f

## Idea

Add a public concept page, `docs/factory-app.md`, that explains the factory GitHub App to a repo owner deciding whether to install it.

### Motivation

A repo owner who finds the public factory App cannot see what it can touch, how its tokens are scoped, or how reviews reach their repo before granting it write access. The App's source repository is private, so the App's homepage URL needs a public page at `https://shipd.now/docs/factory-app`.

### Details

- Add `docs/factory-app.md`, a `concept` doc of at most 100 lines.
- Cover: what the App is for, its permissions and scope, how tokens are minted and delivered, the separate reviewer identity and how reviews run, and how to install and remove it, including the `shipd-now` collaborator that reviews need.
- Carry one Mermaid diagram: a `flowchart TD` swimlane with one subgraph per layer.

Affected capabilities: `factory-app-docs` (added). Impact: one new file under `docs/`; no code, no engine change.

### Non-goals

- No edit to the website repo `shipd-now/shipd-now-website` in this change.
- No change to the App's settings, permissions, or homepage URL on GitHub.
- No link to the private source repository.

## Implementation

- **File path `docs/factory-app.md`.** The website's `scripts/sync-docs.mjs` derives a slug from the path minus `.md`, with `/` replaced by `-`, and `app/docs/[slug]` serves `/docs/<slug>`. A top-level file gives exactly `/docs/factory-app`. Rejected: `docs/factory-app/index.md`, which would map to `factory-app-index`.
- **Doc type `concept`, 100-line cap.** The page explains what the App is and why it exists; install and remove are two short numbered lists inside it. If the draft runs long, cut prose; do not switch type.
- **Title `The factory GitHub App`.** The sync takes an adopted page's title from the first `# ` heading.
- **Everything described is live.** The App, token minting, the factory job, the orchestrator, the egress policy, and the PR-room reviewers all run today, so the page carries no planned framing and the diagram no `(planned)` labels.
- **Facts, worded as settled.** Permissions: Contents read and write, Pull requests read and write, Metadata read; no organization or account permissions; no webhook, events, or user authorization. `server/credentials/ghcreds.py mint <owner/repo>` signs a short JWT, looks up the repo's installation, and requests a token for that one repo and those three permissions. The orchestrator mints a fresh token when a job starts and re-mints it every 40 minutes while a long job runs; each token expires within an hour. The private key stays on the host in `~/.config/shipd-factory/`, mode 0600, pushed from 1Password. No long-lived credential goes into a sandbox spec. The orchestrator applies the job's egress policy, then writes the one-repo GitHub token and the Claude token as files inside the sandbox over `ax ssh`; egress injection (the gateway adds the real credential, the sandbox holds a placeholder) is proven but not yet the delivery mode. Minting refuses with a message that the factory App is not installed on `<repo>`. Jobs push `change/<slug>` and open a pull request as the factory App's bot, shipped as the target repo's shipd `pr-mode` says (`auto` arms auto-merge; `draft` leaves the merge to a person). Only `draft` mode has an end-to-end test so far, and GitHub won't arm auto-merge on a repo with no required checks. Reviewers act as the `shipd-now` user, whose token the host checks belongs to `shipd-now`. The orchestrator watches each PR a succeeded change job opened, or one registered through `POST /reviews`, and runs one short review job per new head commit until the PR merges or closes. Reviews need the repo owner to add `shipd-now` as a collaborator with push (write) access; the App alone gives factory PRs but no reviews, and removing the collaborator stops new reviews.
- **Diagram.** `flowchart TD`; subgraphs, top to bottom: repo owner, GitHub, factory host (mint, orchestrator), ax cluster (egress policy, factory job, review job). Every subgraph and node has an explicit unique alphanumeric ID; every edge joins two nodes, never two subgraphs. Flow: install, grant `shipd-now` push, one-repo token, orchestrator applies the egress policy and starts the Task and writes tokens over `ax ssh`, push branch and open pull request, one review job per head, merge when `pr-mode` is draft. The job-to-repo and review-to-repo edges are two-way (`<-->`) so the GitHub layer stays above the cluster. No emoji, no fills, no text colour.
- **Site navigation is a follow-up in the website repo.** The hourly sync adopts the new file as a `hidden` entry, and `lib/docs.ts` `getPage` serves no hidden page. After this change merges and the sync vendors the file, someone edits the `factory-app.md` entry in `content/docs.manifest.json`: drop `hidden`, set `"section": "Concepts"` and a one-sentence `description`. Rejected: a website PR now, because a visible entry without the vendored file breaks the build.

Risk: the page drifts from the private source as the factory changes, for example when egress injection becomes the delivery mode or `auto` mode gets its end-to-end test. Guard: each such fact sits in one sentence, so a later change updates that sentence.

## Readiness attestation

### Problem and motivation

The App needs a public homepage that tells a repo owner what it can touch before they install it.

Evidence:

- the factory repo's `docs/github-app.md` step 1 sets the App's installation scope to "Any account".
- the factory repo's `.shipd/epics/software-factory/epic.md` Decisions: the App's installations bound which repos a job can touch.

### Scope and non-goals

One new page in this repo; the website manifest and the App settings stay out.

Evidence:

- In scope: `docs/factory-app.md` (new).
- Out of scope: `shipd-now-website/content/docs.manifest.json`, owned by the website repo.

### Affected capabilities and files

One new capability and one new file, because the page is the only artifact and the site maps it by path.

Evidence:

- Capability `factory-app-docs` (added), requirement `factory-app-page`.
- File: `docs/factory-app.md`.
- Runnable premise: running `reconcileManifest(['factory-app.md'], ...)` from `shipd-now-website/scripts/sync-docs.mjs` under node printed `{"file":"factory-app.md","slug":"factory-app",...,"hidden":true}`.
- `shipd-now-website/lib/docs.ts` `getPage` returns null when `page.hidden` is set.

### No open task-shaping decision

Every task-shaping decision is settled by investigation; none remain.

Evidence:

- File path: settled by the sync's slug rule, verified by the run above.
- Doc type: settled by the standard's doc-type definitions in `plugins/s/skills/document/references/standard.md`.
- Pull request mode: settled by the user. Factory jobs follow the target repo's `pr-mode` (epic Decision, factory App PR #8).
- Website nav entry deferred: settled by `lib/docs.ts` and the website `AGENTS.md` corpus-contract section.
