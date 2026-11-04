# shipd-factory-setup-page
Status: ready
Planned-at: 171e580704f2b97cb315571322b0286fb106bb3d
Gated-hash: b898e10e133b

## Idea

Scrub the private host codename from every public file, and add a beta, invite-only how-to for running your own factory host.

### Motivation

The public `shipd-factory` page names the operator's private cluster codename, a private config path and a reviewer check tied to it, so the live docs leak a private name. An invited operator also has no public page that says how to set up an ax host and point the `/shipd-factory` skill at it.

### Details

- Rewrite `docs/shipd-factory.md` with no codename in text, diagram labels or code spans, using the renamed factory names, and link the setup page in the first lines after the title.
- Add `docs/shipd-factory-setup.md`, a `how-to` doc of at most 170 lines. It states what the host needs, links Google's upstream ax and Agent Substrate repos, uses the factory's install scripts, and has each operator create their own GitHub App and reviewer account.
- Reword every tracked line and rename every tracked path that carries the codename: `.shipd/completed/*`, `.shipd/research/shipd-addons/report.md`, `.shipd/verified/shipd-factory-docs/spec.md` (through the delta) and `tools/container/Dockerfile`.
- Follow up in the website repo: unhide the adopted setup entry under `Concepts`.

Affected capabilities: `shipd-factory-docs` (one requirement modified, one added). Impact: two docs pages, archived records, one Dockerfile comment; no code or engine change.

### Non-goals

- Git history, branch names and other repos' contents, apart from the website manifest follow-up.
- Renaming anything inside the factory itself; the sibling factory rename does that.
- Removing the public `unkannybanny` proof links from the concept page.

## Implementation

**Codename notation.** No artifact of this change spells the codename. Commands match it with the regex class `a[x]el` or the shell glob `a?el`, so the guard never matches its own text and needs no exception.

**Guard (binding, before every push).** Both print nothing:

- `git grep -n -i -E 'a[x]el|100\.121\.|mikkel-bergmann/(shipd-factory|css-animation)'`
- `git ls-files | grep -i 'a[x]el'`

Exceptions: none.

**New names (from the sibling factory rename).** Room check `room-review/shipd-factory-reviewer`; agents `shipd-factory` and `shipd-factory-reviewer`; host config dir `~/.config/shipd-factory/`; systemd unit `shipd-factory-orchestrator`; host checkout `~/shipd-factory`. The App slug `shipd-factory` and `shipd-factory[bot]` stay.

**Concept page edits.** The host becomes "the factory host" (sentence: "The factory runs on a self-hosted factory host running Google's ax agent runtime"); diagram `subgraph LHost [factory host]`; key path `~/.config/shipd-factory/`, mode 0600, with the password-manager source dropped; check `room-review/shipd-factory-reviewer`. Line 3 is `> **Beta, invite only:** [Run your own factory host](shipd-factory-setup.md).` with a blank line after it. Trim prose so the file stays at most 100 lines; the existing lint and verified scenarios still hold.

**Setup page.** `<!-- doc-type: how-to -->`, title `# Run your own shipd-factory host`, then a line saying "Beta, invite only": the factory code is private and access is by invitation. Seven numbered sections in this order, placeholders `<host>`, `<user>`, `<id>`, `<reviewer-login>`, `<bind-address>`, `<owner/repo>`:

1. **What the host needs.** A short list, stated as the tested setup rather than a hard minimum: Debian 13 on x86_64 (amd64); 4 vCPU, 12 GB RAM and 64 GB disk, which runs two job workers; a default `debian` user with passwordless sudo, reached over ssh from your machine; outbound internet to GitHub, the Go and Kubernetes download sites and the Claude API. No GPU is needed; jobs run in gVisor sandboxes. Do not claim KVM is optional: the tested host has `/dev/kvm`, and it is unverified without it. Then name what the install puts on it: docker, Go, kubectl, kind and ko; one kind cluster running Agent Substrate (`ate-system`) and ax (`ax-system`) with a gVisor worker pool. Link upstream for reference: Google's ax at `https://github.com/google/ax` (its `docs/installation.md` covers a manual install) and Agent Substrate at `https://github.com/agent-substrate/substrate`. Say the factory pins both to exact commits in `server/versions.env`, so use the factory's scripts rather than the upstream quick start.
2. **Install the cluster.** From the factory checkout on your machine, with your host in `AX_HOST` and `AX_USER`: `server/provision.sh` bootstraps docker, Go, kubectl, kind and ko; `AX_HOST=<host> AX_USER=<user> server/deploy.sh` copies `server/` to `~/shipd-factory` and runs `install.sh`, which builds the cluster from the pins. Build the runner image with `server/deploy.sh --image`, then run `~/shipd-factory/server/image-smoke.sh`; prove the cluster with `~/shipd-factory/server/smoke.sh`.
3. **Orchestrator.** `server/deploy.sh --orchestrator` installs and restarts `shipd-factory-orchestrator`, ending `orchestrator: ok`; logs `journalctl -u shipd-factory-orchestrator`; it listens on port 8080 at `ORCH_BIND` (`<bind-address>:8080`). The unit runs as the host user from `~/shipd-factory`.
4. **Your GitHub App and reviewer.** Each operator creates their own; nothing is shared. Create a GitHub App (Settings, Developer settings, GitHub Apps, New GitHub App): any name, webhook off, repository permissions Contents read and write, Pull requests read and write, Metadata read. Note its App id and generate a private key. Create a separate GitHub user for reviews, and take its token with `gh auth token`. Install the App on each repo the factory works on, and invite the reviewer user there with push access. Store in `~/.config/shipd-factory/`, each file mode 0600: `github-app.pem`, `credentials.env` holding `GITHUB_APP_ID=<id>` and `REVIEWER_LOGIN=<reviewer-login>`, and `reviewer.token`. Write them over ssh stdin with `umask 077`, never as a command argument. Check with `python3 ~/shipd-factory/server/credentials/ghcreds.py check`, which ends `ok: app <your-app-slug>` and `ok: reviewer <reviewer-login>`; add `<owner/repo>` to check one install. The factory reads the bot name from the App, so any App name works.
5. **Claude token.** A long-lived token from `claude setup-token`, stored as `~/.config/shipd-factory/claude-oauth.token`, mode 0600, or a job fails at `credentials`. Then run `python3 ~/shipd-factory/server/egress/egress.py setup`, which stores it for the cluster and applies the egress setup; jobs reach only an allowlist of hosts.
6. **Network.** The API has no authentication beyond the network, so never expose it publicly. Reach it over a private network, or an ssh tunnel: `ssh -N -L 8080:<bind-address>:8080 <user>@<host>`, then use `http://localhost:8080`.
7. **Point the skill.** Install it with `skill/install.sh` (into `~/.claude/skills/shipd-factory`), set `SHIPD_FACTORY_URL=http://<host>:8080`, check `python3 ~/.claude/skills/shipd-factory/shipd_factory.py health` (exit 0 when healthy), then run `/shipd-factory onboard <owner/repo>`, linking the concept page's "Set up a repo".

The setup page never names an IP address, a personal GitHub login, a private repo name, the codename, or vault details.

**Archive rewording.** Each guard hit becomes a neutral form: the host is "the factory host"; the old App name (`shipd-` plus the codename) becomes `the factory App`, its old page path `docs/factory-app.md`, its capability `factory-app-docs`, its requirement `factory-app-page`; a private repo path becomes "the factory repo's `<file>`"; a guard pattern line is described in words. Rename the archived change directory `2026-11-03-shipd-a?el-docs` to `2026-11-03-factory-app-docs`, its title to `# factory-app-docs`, and both archived `specs/shipd-a?el-docs/` folders to `specs/factory-app-docs/` (Q6). A Gated-hash on a reworded archive goes stale; nothing rechecks archived stamps.

**Release order.** The push waits for the user's "factory rename deployed" signal, then re-verifies every setup-page command against the renamed factory's main. The website follow-up runs after merge; its merges, gate posts and workflow runs are user pauses that print the exact command and wait.

Risk: the renamed factory may change a script path or output line. The pre-push re-verification catches it, and the page is fixed before the push.

## Questions and answers

### Q1: Public concept page names
- **Question:** How should the concept page name the host and its paths and checks?
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Never say the codename; call it the factory host and use the renamed check, agents, config dir, unit and checkout listed in Implementation.
- **Queued:** none (binding instruction given with the request)

### Q2: Setup page scope
- **Question:** What does the new setup page cover?
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** A beta, invite-only how-to: the ax host and cluster, the checkout and orchestrator on port 8080, the GitHub credentials and check, the Claude token, network reach, then `SHIPD_FACTORY_URL` and onboarding, with placeholders and no private details.
- **Queued:** none (binding instruction given with the request)

### Q3: Link and line caps
- **Question:** Where is the setup page linked, and what caps apply?
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Link it in the first lines after the concept page's title, labelled Beta, invite only. The concept page keeps its 100-line cap, the setup page gets 150, and both pass the docs lint.
- **Queued:** none (binding instruction given with the request)

### Q4: Archived records
- **Question:** Do archived plans and comments get reworded?
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Yes, every tracked mention, archives and the Dockerfile included, to a neutral form; git history is out of scope.
- **Queued:** none (binding instruction given with the request)

### Q5: Website, guard and release gate
- **Question:** How do the website follow-up, the guard and the push timing work?
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** A follow-up website PR unhides the setup entry under the shipd-factory section, with each merge, gate post and workflow run a user pause. The guard runs before every push with exceptions listed. The push waits for the signal "factory rename deployed".
- **Queued:** none (binding instruction given with the request)

### Q6: Archived names that carry the codename
- **Question:** Rename archived directories, capability folders and requirement ids too, or rewrite text only? Recommendation: rename them.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** No human was available, so the recommended default stands: rename them to `factory-app-docs` and `factory-app-page`, since tracked paths are public too.
- **Queued:** q-archived-codename-paths

### Q7: Guard self-match
- **Question:** Write the codename as a bracket class in the guard, or list the plan files as exceptions? Recommendation: bracket class.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** No human was available, so the default stands: the guard uses `a[x]el` and lists no exceptions.
- **Queued:** q-guard-self-match

### Q8: Script paths on the setup page
- **Question:** Name the current script paths under `~/shipd-factory`, or wait for the rename plan? Recommendation: current paths, re-verified before push.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** No human was available, so the default stands: current paths under `~/shipd-factory`, re-verified against the renamed factory at the push pause.
- **Queued:** q-setup-page-helper-paths

### Q9: Operator GitHub credentials
- **Question:** Does an invited operator receive the App id, key and reviewer token, or create their own App? Recommendation: create their own.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Each operator creates their own GitHub App and reviewer account; the page walks through the App settings, key, install and reviewer invite, and nothing is shared.
- **Queued:** q-operator-app-credentials

### Q10: What the host needs, and upstream links
- **Question:** Should the setup page state the host requirements and link Google's upstream repos alongside the factory's install scripts?
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Yes. State exactly what the ax host needs, use the factory's install scripts for the install, and link Google's ax repo on GitHub for reference.
- **Queued:** none (binding instruction given with the request)

## Readiness attestation

### Problem and motivation

The live concept page leaks the private codename, and invited operators have no setup guide.

Evidence:

- `docs/shipd-factory.md` lines 11, 27, 57 and 74 name the codename.
- The guard regex over the tree matched 52 content lines and 4 tracked paths.

### Scope and non-goals

Two docs pages, archived records, one Dockerfile comment and a website manifest follow-up; history and the factory's own code stay out.

Evidence:

- In scope: `docs/`, `.shipd/completed/`, `.shipd/research/shipd-addons/report.md`, `tools/container/Dockerfile`.
- Out of scope: git history and the factory repo.

### Affected capabilities and files

One capability changes: the page requirement is modified and a setup requirement is added.

Evidence:

- `spec_status.py base-hash shipd-factory-docs shipd-factory-page` printed `de744f3f1207`.
- `docs_lint.py docs/shipd-factory.md` exit 0; `wc -l` printed 99.
- The running factory host reports 4 vCPU, 11 GiB usable RAM, a 63 GB root disk, and `Linux 6.12 deb13-cloud-amd64 x86_64`, Debian GNU/Linux 13 (trixie).
- The factory's `server/versions.env` pins `AX_REPO=https://github.com/google/ax` and `SUBSTRATE_REPO=https://github.com/agent-substrate/substrate`; `server/provision.sh` installs docker, Go, kubectl, kind and ko for amd64 and adds user `debian` to the docker group.
- Google's ax README requires a Kubernetes cluster with Agent Substrate in `ate-system`, Go, kubectl, docker or podman, and a gVisor WorkerPool, and points to `docs/installation.md`.
- The host has `/dev/kvm` and the `vmx` CPU flag and no GPU driver, so the page claims no GPU need but makes no claim about running without KVM.
- The factory's `ghcreds.py` reads the App slug from the GitHub API, so an operator's own App of any name works.
- `claude setup-token --help` printed "Set up a long-lived authentication token".
- The website manifest on `origin/main` has sections Start here, Reference, Concepts, Multi-agent PRs and Workspaces, and no Guides, so the entry goes under Concepts.
- `scripts/sync-docs.mjs` `rewriteLinks` sends a link to a hidden entry to its GitHub blob URL, so the top link works before the unhide.

### No open task-shaping decision

Every decision is settled: Q1 to Q5 by the user, Q6 to Q9 by recorded defaults.

Evidence:

- Q6 to Q9 each returned INSUFFICIENT from `oracle-lookup` and were queued.
