## MODIFIED Requirements

### Requirement: shipd-factory App page
id: shipd-factory-page
base: 73d49113ad82

The repository SHALL carry `docs/shipd-factory.md`, a `concept` doc that explains the `shipd-factory` GitHub App to a repo owner deciding whether to install it. The page SHALL state the App's permissions and scope, how its tokens are minted and delivered, the separate reviewer identity and how reviews run, how a repo is set up and how to remove the App, the author-fix opt-in, and what the live runs proved. The page SHALL link `shipd-factory-setup.md` in the first lines after its title, labelled Beta, invite only. The page SHALL carry exactly one Mermaid `flowchart TD` diagram with one subgraph per layer, SHALL name the host only generically, and SHALL NOT link to the App's private source repository. The `What it is for` section SHALL open by saying that the factory works where the reader works, can stay on 24/7, and takes its settings through shipd. That section SHALL present a Slack connector as in development, SHALL present connectors for Teams and other tools, and skills added to the shipd harness, as planned work, and SHALL NOT say that a connector ships today.

#### Scenario: The page lints clean
- **WHEN** `python3 -B plugins/s/skills/document/scripts/docs_lint.py docs/shipd-factory.md` runs
- **THEN** it exits 0, the file's first line is `<!-- doc-type: concept -->`, and the file is at most 100 lines

#### Scenario: The page maps to the App's homepage URL
- **WHEN** the website's `reconcileManifest` adopts `shipd-factory.md`
- **THEN** the derived slug is `shipd-factory`, the route `/docs/shipd-factory`

#### Scenario: The setup page is linked at the top
- **WHEN** a reader opens the page
- **THEN** one of the first three lines after the title links `shipd-factory-setup.md` and says Beta, invite only

#### Scenario: The purpose section states the always-on direction
- **WHEN** a reader opens the `## What it is for` section
- **THEN** its first paragraph says the factory works where you work and can stay on 24/7, names `.shipd-config.json` as today's way to set how it works, and names skills added to the shipd harness with the qualifier "once they ship"

#### Scenario: Connectors read as not yet shipped
- **WHEN** a reader reads the first paragraph of the `## What it is for` section
- **THEN** it says connectors will let the factory run by itself, says shipd is building a Slack connector and plans more for Teams and other tools, and gives a shipd Slack app that reacts to Grafana errors in a channel as an example

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

#### Scenario: Removal is stated and the setup link resolves
- **WHEN** a reader opens the `## Set up and remove` section, and follows the last link of `docs/shipd-factory-setup.md`
- **THEN** the section says uninstalling the App stops all minting and removing the `shipd-now` collaborator stops new reviews, and the link target is `shipd-factory.md#set-up-and-remove`

#### Scenario: No private name or link
- **WHEN** `grep -n -i -E 'a[x]el|100\.121\.|mikkel-bergmann/(shipd-factory|css-animation)' docs/shipd-factory.md` runs and a reader checks every link
- **THEN** grep prints nothing, the host key path is `~/.config/shipd-factory/`, no link points at the App's source repository, and every GitHub link points at a public page
