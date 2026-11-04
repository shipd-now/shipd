## MODIFIED Requirements

### Requirement: shipd-factory App page
id: shipd-factory-page
base: de744f3f1207

The repository SHALL carry `docs/shipd-factory.md`, a `concept` doc that explains the `shipd-factory` GitHub App to a repo owner deciding whether to install it. The page SHALL state the App's permissions and scope, how its tokens are minted and delivered, the separate reviewer identity and how reviews run, how a repo is set up and how to remove the App, the author-fix opt-in, and what the live runs proved. The page SHALL link `shipd-factory-setup.md` in the first lines after its title, labelled Beta, invite only. The page SHALL carry exactly one Mermaid `flowchart TD` diagram with one subgraph per layer, SHALL name the host only generically, and SHALL NOT link to the App's private source repository.

#### Scenario: The page lints clean
- **WHEN** `python3 -B plugins/s/skills/document/scripts/docs_lint.py docs/shipd-factory.md` runs
- **THEN** it exits 0, the file's first line is `<!-- doc-type: concept -->`, and the file is at most 100 lines

#### Scenario: The page maps to the App's homepage URL
- **WHEN** the website's `reconcileManifest` adopts `shipd-factory.md`
- **THEN** the derived slug is `shipd-factory`, the route `/docs/shipd-factory`

#### Scenario: The setup page is linked at the top
- **WHEN** a reader opens the page
- **THEN** one of the first three lines after the title links `shipd-factory-setup.md` and says Beta, invite only

#### Scenario: Permissions and scope are stated
- **WHEN** a reader opens the page
- **THEN** it names Contents read and write, Pull requests read and write, and Metadata read, says the App has no webhook and no user authorization, and says each token covers one repo and expires within an hour

#### Scenario: Reviews and their access are stated
- **WHEN** a reader opens the page
- **THEN** it says reviews run as `shipd-now`, one gate job and one room review job per new head commit, that setup invites `shipd-now` with push access, and that the ruleset checks `room-review/shipd-factory-reviewer`, and no text or diagram label marks a part `(planned)`

#### Scenario: The diagram follows the layer rules
- **WHEN** a reader reads the diagram source
- **THEN** every subgraph and node has an explicit unique ID, every subgraph has a matching `end`, every edge joins two nodes, the host subgraph is labelled `factory host`, and no label carries an emoji, a fill, or a text colour

#### Scenario: Setup, opt-in and proofs are stated
- **WHEN** a reader opens the page
- **THEN** it names `/shipd-factory onboard`, `/shipd-factory new` and `factory.author_fixes`, and states each live proof that passed in one dated sentence

#### Scenario: No private name or link
- **WHEN** `grep -n -i -E 'a[x]el|100\.121\.|mikkel-bergmann/(shipd-factory|css-animation)' docs/shipd-factory.md` runs and a reader checks every link
- **THEN** grep prints nothing, the host key path is `~/.config/shipd-factory/`, no link points at the App's source repository, and every GitHub link points at a public page

## ADDED Requirements

### Requirement: shipd-factory setup page
id: shipd-factory-setup-page

The repository SHALL carry `docs/shipd-factory-setup.md`, a `how-to` doc of at most 170 lines that walks an invited operator through running their own factory host. The page SHALL say near the top that it is Beta, invite only, because the factory code is private and access is by invitation. It SHALL cover, in order: what the host needs, with links to Google's upstream ax and Agent Substrate repositories; installing the cluster with the factory's scripts; the `~/shipd-factory` checkout and the `shipd-factory-orchestrator` service on port 8080; creating the operator's own GitHub App and reviewer account, with the App key, App id and reviewer token in `~/.config/shipd-factory/` at mode 0600, checked with the credential helper; the Claude token for jobs; network reach to the orchestrator API; and `SHIPD_FACTORY_URL` followed by onboarding a repo. The page SHALL use placeholders such as `<host>` and SHALL NOT carry an IP address, a personal GitHub login, a private repo name, the host codename or password-vault details.

#### Scenario: The setup page lints clean
- **WHEN** `python3 -B plugins/s/skills/document/scripts/docs_lint.py docs/shipd-factory-setup.md` runs
- **THEN** it exits 0, the first line is `<!-- doc-type: how-to -->`, and the file is at most 170 lines

#### Scenario: Beta status is stated up front
- **WHEN** a reader opens the setup page
- **THEN** within five lines of the title it says Beta, invite only, that the factory code is private, and that access is by invitation

#### Scenario: The steps run in order
- **WHEN** a reader follows the setup page
- **THEN** the sections cover what the host needs, installing the cluster, orchestrator, the operator's GitHub App and reviewer, Claude token, network, and pointing the skill, in that order, and name `shipd-factory-orchestrator`, port 8080, `~/.config/shipd-factory/`, mode 0600, `ghcreds.py check`, `SHIPD_FACTORY_URL=http://<host>:8080` and `/shipd-factory onboard`

#### Scenario: Host needs and upstream links are stated
- **WHEN** a reader reaches the first section
- **THEN** it names Debian 13 on x86_64, 4 vCPU, 12 GB RAM and 64 GB disk as the tested setup, passwordless sudo over ssh, outbound internet, and no GPU; names Agent Substrate, ax and a gVisor worker pool on one kind cluster; and links `https://github.com/google/ax` and `https://github.com/agent-substrate/substrate`

#### Scenario: Each operator creates their own App
- **WHEN** a reader reaches the GitHub section
- **THEN** it says nothing is shared, and walks through creating a GitHub App with webhook off and Contents read and write, Pull requests read and write and Metadata read, generating its key, creating a separate reviewer user and its token, installing the App and inviting the reviewer with push access

#### Scenario: Network reach is explained
- **WHEN** a reader reaches the network section
- **THEN** it says the API has no authentication beyond the network, must not be exposed publicly, and is reached over a private network or an ssh tunnel, with the tunnel command shown

#### Scenario: No private detail
- **WHEN** `grep -n -i -E 'a[x]el|[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+|mikkel-bergmann|1password|vault' docs/shipd-factory-setup.md` runs
- **THEN** it prints nothing

#### Scenario: Nothing tracked names the codename
- **WHEN** `git grep -n -i -E 'a[x]el|100\.121\.|mikkel-bergmann/(shipd-factory|css-animation)'` and `git ls-files | grep -i 'a[x]el'` run over the tree
- **THEN** both print nothing
