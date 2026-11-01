# shipd-axel-docs
Status: complete
Planned-at: 90b4ac75747c6892b128310a342d623b8b65b9f4
Gated-hash: 3672bae9be7f

## Idea

Add a public concept page, `docs/shipd-axel.md`, that explains the `shipd-axel` GitHub App to a repo owner deciding whether to install it.

### Motivation

A repo owner who finds the public `shipd-axel` App cannot see what it can touch, how its tokens are scoped, or which parts run today before granting it write access. The App's source repository is private, so the App's homepage URL needs a public page at `https://shipd.now/docs/shipd-axel`.

### Details

- Add `docs/shipd-axel.md`, a `concept` doc of at most 100 lines.
- Cover: what the App is for, its permissions and scope, how tokens are minted, the separate reviewer identity, what is live and what is planned, and how to install and remove it.
- Carry one Mermaid diagram: a `flowchart TD` swimlane with one subgraph per layer.

Affected capabilities: `shipd-axel-docs` (added). Impact: one new file under `docs/`; no code, no engine change.

### Non-goals

- No edit to the website repo `shipd-now/shipd-now-website` in this change.
- No change to the App's settings, permissions, or homepage URL on GitHub.
- No link to the private source repository.

## Implementation

- **File path `docs/shipd-axel.md`.** The website's `scripts/sync-docs.mjs` derives a slug from the path minus `.md`, with `/` replaced by `-`, and `app/docs/[slug]` serves `/docs/<slug>`. A top-level file gives exactly `/docs/shipd-axel`. Rejected: `docs/shipd-axel/index.md`, which would map to `shipd-axel-index`.
- **Doc type `concept`, 100-line cap.** The page explains what the App is and why it exists; install and remove are two short numbered lists inside it. If the draft runs long, cut prose; do not switch type.
- **Title `The shipd-axel GitHub App`.** The sync takes an adopted page's title from the first `# ` heading.
- **Live versus planned stated plainly.** Live: the App and per-job token minting on the axel host. Planned members of the `software-factory` epic: the factory job, the orchestrator, the egress policy, and the PR-room reviewers. The diagram marks planned steps `(planned)` in their labels.
- **Facts, worded as settled.** Permissions: Contents read and write, Pull requests read and write, Metadata read; no organization or account permissions; no webhook, events, or user authorization. `server/credentials/ghcreds.py mint <owner/repo>` signs a short JWT, looks up the repo's installation, and requests a token for that one repo and those three permissions. The token expires within an hour and is minted fresh per job. The private key stays on the host in `~/.config/axel/`, mode 0600, pushed from 1Password. No long-lived credential goes into a sandbox spec. Minting refuses with `shipd-axel is not installed on <repo>`. Jobs push `change/<slug>` and open a pull request as `shipd-axel[bot]`, shipped as the target repo's shipd `pr-mode` says (`auto` arms auto-merge; `draft` leaves the merge to a person); reviewers act as the `shipd-now` user, whose token is checked to belong to `shipd-now`.
- **Diagram.** `flowchart TD`; subgraphs, top to bottom: repo owner, GitHub, axel host, ax cluster, reviewer. Every subgraph and node has an explicit unique alphanumeric ID; every edge joins two nodes, never two subgraphs. Flow: install, mint, one-repo token, push branch and open pull request, review, merge when `pr-mode` is draft. No emoji, no fills, no text colour.
- **Site navigation is a follow-up in the website repo.** The hourly sync adopts the new file as a `hidden` entry, and `lib/docs.ts` `getPage` serves no hidden page. After this change merges and the sync vendors the file, someone edits the `shipd-axel.md` entry in `content/docs.manifest.json`: drop `hidden`, set `"section": "Concepts"` and a one-sentence `description`. Rejected: a website PR now, because a visible entry without the vendored file breaks the build.

Risk: the page drifts from the private source as planned members ship. Guard: the page names each planned piece as a member of the `software-factory` epic, so a later member updates one sentence and one label.

## Readiness attestation

### Problem and motivation

The App needs a public homepage that tells a repo owner what it can touch before they install it.

Evidence:

- `axel/.worktrees/github-credentials/docs/github-app.md` step 1 sets the App's installation scope to "Any account".
- `axel/.shipd/epics/software-factory/epic.md` Decisions: the App's installations bound which repos a job can touch.

### Scope and non-goals

One new page in this repo; the website manifest and the App settings stay out.

Evidence:

- In scope: `docs/shipd-axel.md` (new).
- Out of scope: `shipd-now-website/content/docs.manifest.json`, owned by the website repo.

### Affected capabilities and files

One new capability and one new file, because the page is the only artifact and the site maps it by path.

Evidence:

- Capability `shipd-axel-docs` (added), requirement `shipd-axel-page`.
- File: `docs/shipd-axel.md`.
- Runnable premise: running `reconcileManifest(['shipd-axel.md'], ...)` from `shipd-now-website/scripts/sync-docs.mjs` under node printed `{"file":"shipd-axel.md","slug":"shipd-axel",...,"hidden":true}`.
- `shipd-now-website/lib/docs.ts` `getPage` returns null when `page.hidden` is set.

### No open task-shaping decision

Every task-shaping decision is settled by investigation; none remain.

Evidence:

- File path: settled by the sync's slug rule, verified by the run above.
- Doc type: settled by the standard's doc-type definitions in `plugins/s/skills/document/references/standard.md`.
- Pull request mode: settled by the user. Factory jobs follow the target repo's `pr-mode` (epic Decision, shipd-axel PR #8).
- Website nav entry deferred: settled by `lib/docs.ts` and the website `AGENTS.md` corpus-contract section.
