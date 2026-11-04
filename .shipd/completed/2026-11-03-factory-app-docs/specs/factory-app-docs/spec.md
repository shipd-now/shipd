## ADDED Requirements

### Requirement: factory App page
id: factory-app-page

The repository SHALL carry `docs/factory-app.md`, a `concept` doc that explains the factory GitHub App to a repo owner deciding whether to install it. The page SHALL state the App's permissions and scope, how its tokens are minted and delivered, the separate reviewer identity and how reviews run, and how to install and remove it, including the `shipd-now` collaborator that reviews need. The page SHALL carry exactly one Mermaid `flowchart TD` diagram with one subgraph per layer, and SHALL NOT link to the App's private source repository.

#### Scenario: The page lints clean
- **WHEN** `python3 -B plugins/s/skills/document/scripts/docs_lint.py docs/factory-app.md` runs
- **THEN** it exits 0, and the file's first line is `<!-- doc-type: concept -->`

#### Scenario: The page maps to the App's homepage URL
- **WHEN** the website's `reconcileManifest` adopts `factory-app.md`
- **THEN** the derived slug is `factory-app`, the route `/docs/factory-app`

#### Scenario: Permissions and scope are stated
- **WHEN** a reader opens the page
- **THEN** it names Contents read and write, Pull requests read and write, and Metadata read, says the App has no webhook and no user authorization, and says each token covers one repo and expires within an hour

#### Scenario: Reviews and their access are stated
- **WHEN** a reader opens the page
- **THEN** it says reviews run as `shipd-now`, one review job per new head commit, and that reviews need `shipd-now` added as a collaborator with push (write) access, and no text or diagram label marks a part `(planned)`

#### Scenario: The diagram follows the layer rules
- **WHEN** a reader reads the diagram source
- **THEN** every subgraph and node has an explicit unique ID, every subgraph has a matching `end`, every edge joins two nodes, and no label carries an emoji, a fill, or a text colour

#### Scenario: No private link
- **WHEN** a reader checks every link on the page
- **THEN** none points at the App's source repository, and every GitHub link points at a public page
