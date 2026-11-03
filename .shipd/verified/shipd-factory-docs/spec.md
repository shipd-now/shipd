# shipd-factory-docs

### Requirement: shipd-factory App page
id: shipd-factory-page

The repository SHALL carry `docs/shipd-factory.md`, a `concept` doc that explains the `shipd-factory` GitHub App to a repo owner deciding whether to install it. The page SHALL state the App's permissions and scope, how its tokens are minted and delivered, the separate reviewer identity and how reviews run, how a repo is set up and how to remove the App, the author-fix opt-in, and what the live runs proved. The page SHALL carry exactly one Mermaid `flowchart TD` diagram with one subgraph per layer, and SHALL NOT link to the App's private source repository.

#### Scenario: The page lints clean
- **WHEN** `python3 -B plugins/s/skills/document/scripts/docs_lint.py docs/shipd-factory.md` runs
- **THEN** it exits 0, and the file's first line is `<!-- doc-type: concept -->`

#### Scenario: The page maps to the App's homepage URL
- **WHEN** the website's `reconcileManifest` adopts `shipd-factory.md`
- **THEN** the derived slug is `shipd-factory`, the route `/docs/shipd-factory`

#### Scenario: Permissions and scope are stated
- **WHEN** a reader opens the page
- **THEN** it names Contents read and write, Pull requests read and write, and Metadata read, says the App has no webhook and no user authorization, and says each token covers one repo and expires within an hour

#### Scenario: Reviews and their access are stated
- **WHEN** a reader opens the page
- **THEN** it says reviews run as `shipd-now`, one gate job and one room review job per new head commit, and that setup invites `shipd-now` with push access, and no text or diagram label marks a part `(planned)`

#### Scenario: The diagram follows the layer rules
- **WHEN** a reader reads the diagram source
- **THEN** every subgraph and node has an explicit unique ID, every subgraph has a matching `end`, every edge joins two nodes, and no label carries an emoji, a fill, or a text colour

#### Scenario: Setup, opt-in and proofs are stated
- **WHEN** a reader opens the page
- **THEN** it names `/shipd-factory onboard`, `/shipd-factory new` and `factory.author_fixes`, and states each live proof that passed in one dated sentence

#### Scenario: No private name or link
- **WHEN** a reader checks every link and every line of the page
- **THEN** no text names `shipd-axel` or a private repository, no link points at the App's source repository, and every GitHub link points at a public page
