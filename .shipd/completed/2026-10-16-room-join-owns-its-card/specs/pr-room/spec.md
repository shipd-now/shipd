## MODIFIED Requirements

### Requirement: Join upserts the agent card
id: room-join-verb
base: 9afef40619e1

`room.py join <pr> [--agent NAME] [--skill S ...] [--description TEXT]
[--harness H]` SHALL render an `AgentCard` (`name`, `skills`, `description`,
`harness`, and `version` read from the plugin manifest adjacent to the
skill tree) with `room_schema.render_comment`. It SHALL edit in place
(`PATCH repos/<repo>/issues/comments/<id>`) only an issue comment the agent
owns: one whose sole room marker is an `AgentCard` whose `name` equals the
agent, and whose body carries neither the `<!-- shipd-semantic-review -->`
marker nor the legacy `<!-- am-semantic-review -->` marker. When no owned
comment exists, `join` SHALL create one (`POST
repos/<repo>/issues/<n>/comments`), even when the agent's card also appears
inside another comment such as the gate's review summary; `join` SHALL never
PATCH or DELETE a comment it does not own. It SHALL print one JSON object
`{"comment": <id>, "agent": <name>, "url": <html_url>}` on stdout and
`joined <context> as <name>` on stderr, and exit `0`.

#### Scenario: First join creates the card
- **WHEN** `join 7 --agent codex-a --skill review-finding --harness codex`
  runs on a PR with no cards
- **THEN** one POST is recorded whose body's first line is a
  `shipd-room-card` marker naming `codex-a` with skill `review-finding`

#### Scenario: Second join edits the same comment
- **WHEN** `join` runs again as `codex-a` with a new description
- **THEN** a PATCH on the existing comment id is recorded and no second card
  comment exists

#### Scenario: A card inside the review summary is left alone
- **WHEN** `join 14 --agent semantic-review` runs on a PR whose issue comment
  6206725970 carries both a `shipd-room-card` marker naming `semantic-review`
  and the `shipd-semantic-review` marker
- **THEN** no PATCH or DELETE is recorded, one POST creates a separate card
  comment, the printed `comment` is the new id, and comment 6206725970 is
  unchanged

#### Scenario: A rejoin after the fallback edits the new card
- **WHEN** `join --agent semantic-review` runs again on that PR
- **THEN** one PATCH is recorded on the comment the first join created, and
  none on comment 6206725970

#### Scenario: A comment with more than one room marker is not owned
- **WHEN** `join --agent codex-a` runs and the only comment naming `codex-a`
  as a card also carries a second room marker
- **THEN** a POST creates a new card comment and no PATCH is recorded
