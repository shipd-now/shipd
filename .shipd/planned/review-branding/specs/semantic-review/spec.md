## ADDED Requirements

### Requirement: Room-reviewer posting options
id: gate-poster-room-mode

`review_gate.py post` SHALL accept three optional flags: `--status {set,off,auto}` (default `set`), `--room-agent <name>`, and `--room-to <name>`. A post with `--status set` and neither room flag SHALL produce output byte-identical to today's.

Where `--status off` is passed, `post` SHALL set no `semantic-review` commit status, SHALL make no `SHIPD_FAST_PASS` read and no merge call, SHALL render no `**Fast-pass:**` line in the summary, and SHALL print `semantic-review status: not set (<reason>)` in place of the status line, the reason being `--status off`, `gate workflow present`, or `gate workflow unreadable`. It SHALL still upsert the summary comment, post the anchored inline comments, and submit the review with the event the `gate-review-event` requirement maps from the status state the disposition scope selects.

Where `--status auto` is passed, `post` SHALL read `gh api repos/<repo>/contents/.github/workflows/copilot-review-gate.yml?ref=<baseRefOid>` once, before its first write. If that read exits `0`, the gate workflow is present on the pull request's base and `post` SHALL behave as `--status off`. If it fails with `HTTP 404`, the gate is absent and `post` SHALL behave as `--status set`, setting the status and running fast-pass as today. If it fails any other way, `post` SHALL behave as `--status off` and print one warning line naming the failed read, so an unreadable repository never has its gate's status overwritten.

Where `--room-agent <name>` is passed, each anchored finding's room Message (the `gate-finding-room-task` line) SHALL carry `agent` `<name>` instead of `semantic-review`. The submitted review's body SHALL be the heading `### ☕ shipd · <name> · reviewer (for @<login>)`, one blank line, then the full summary as `render_summary` renders it for this post: brand line, verdict header, effort and provenance lines, findings table or `No problems found.`, any Additional findings section, and the `Reviewed …` footer. That review body SHALL carry no hidden marker line (no `<!-- shipd-semantic-review -->`, head, or card line), no Earlier-reviews block, and no fast-pass line. When the inline review is rejected and retried without inline comments, the retry's body SHALL carry the folded summary. The summary comment SHALL still be the one shared, marker-keyed comment, edited in place on every post. Its card line SHALL still name `semantic-review`, so the posting agent's own room card is never replaced. Where `--room-to <name>` is also passed, each finding Message's `metadata` SHALL carry `"to": "<name>"`. If `--room-to` is passed without `--room-agent`, then `post` SHALL exit `2` with a usage error and make no `gh` call.

The `/s:review` posting reference (`references/posting.md`) SHALL name three more review stage options passed straight through to the poster: `status=<set|off|auto>` as `--status`, `room-agent=<name>` as `--room-agent`, and `room-to=<name>` as `--room-to`.

#### Scenario: Auto with the gate present sets no status
- **WHEN** `post --status auto` runs and the contents read of `.github/workflows/copilot-review-gate.yml` at the base commit exits `0`, on an eligible `pass` payload with `SHIPD_FAST_PASS` enabled
- **THEN** no `statuses` call and no `pr merge` call is made, the summary carries no `**Fast-pass:**` line, the output says `not set (gate workflow present)`, and the submitted event is `APPROVE`

#### Scenario: Auto with the gate absent sets the status
- **WHEN** `post --status auto` runs, the contents read fails with `HTTP 404`, and the payload is `changes-requested` with one anchored high finding
- **THEN** the head's `semantic-review` status is set to `failure` and the review event is `REQUEST_CHANGES`

#### Scenario: An unreadable workflow path sets no status
- **WHEN** `post --status auto` runs and the contents read fails with `HTTP 403`
- **THEN** no status call is made and one warning line names the failed read

#### Scenario: Off never reads the workflow path
- **WHEN** `post --status off` publishes a `changes-requested` review
- **THEN** no contents read and no status call is made, and the event is `REQUEST_CHANGES`

#### Scenario: Room flags address the finding task
- **WHEN** `post --room-agent reviewer-b --room-to author-a` publishes one anchored finding
- **THEN** the inline comment's room Message parses with `agent` `reviewer-b`, `to` `author-a`, skill `review-finding`, state `input-required`, and the summary's card is named `semantic-review`

#### Scenario: The room review body carries the full summary
- **WHEN** `post --room-agent reviewer-b` publishes a `changes-requested` review with one anchored and one unanchorable finding and a readable file list
- **THEN** the submitted review body's first line is `### ☕ shipd · reviewer-b · reviewer (for @<login>)`, it contains the brand line, `## Findings: ❌ Fix required`, the findings table row, the Additional findings section, and the `Reviewed …` footer, and it contains no `<!-- shipd-semantic-review` text

#### Scenario: A re-review after a head move keeps one summary and adds a full review
- **WHEN** `post --room-agent reviewer-b` runs on head `aaaaaaa…` with a `changes-requested` review and then on head `bbbbbbb…` with a `pass` review
- **THEN** one summary comment exists, edited in place, holding an Earlier-reviews entry for `aaaaaaa`, and two reviews were submitted, the second carrying `## Findings: ✅ Ship it` and no Earlier-reviews block

#### Scenario: The author's watch surfaces the finding and the reviewer's does not
- **WHEN** `room.actionable_tasks` reads the task built from that inline comment for agent `author-a` and for agent `reviewer-b`, each with skill `review-finding`
- **THEN** it returns the task for `author-a` and nothing for `reviewer-b`

#### Scenario: --room-to alone is refused
- **WHEN** `review_gate.py post 7 --from x.json --room-to author-a` runs
- **THEN** it exits `2` and no `gh` call is made

#### Scenario: Without the flags the post is unchanged
- **WHEN** the existing `PostTest`, `FastPassPostTest`, and `RoomPostTest` suites run
- **THEN** they pass unedited

#### Scenario: The posting reference names the options
- **WHEN** the skill reference test reads `references/posting.md`
- **THEN** it finds `status=`, `--status`, `auto`, `room-agent=`, `--room-agent`, `room-to=`, and `--room-to`

### Requirement: Review branding tests, docs, and version
id: review-branding-ships

The change SHALL cover its behaviour in `test_review_gate.py`, `test_copilot_verb.py`, `test_room_run.py`, `test_room_skill.py`, and `test_skill_references.py`. `docs/semantic-review-reference.md` SHALL document the three room-reviewer flags, including the `--status auto` detection rule. `docs/copilot-review-reference.md` SHALL say the posted gate body opens with the brand line. Both SHALL pass `docs_lint.py`. `plugins/s/.claude-plugin/plugin.json` SHALL carry version `0.6.343`.

#### Scenario: Suites pass offline
- **WHEN** the review, room, and copilot verb suites run
- **THEN** each reports `OK`

#### Scenario: Docs lint clean
- **WHEN** `docs_lint.py` runs on `docs/semantic-review-reference.md`, `docs/copilot-review-reference.md`, and `docs/room-run.md`
- **THEN** each exits `0`
