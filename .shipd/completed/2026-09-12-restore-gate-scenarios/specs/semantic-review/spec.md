## MODIFIED Requirements

### Requirement: PR posting of a review verdict
id: gate-poster
base: 7c45b96f6514

`review_gate.py post <pr> --from <json|->` SHALL publish a `/s:review --json`
object to the named pull request via `gh`: upserting a single summary comment
identified by the hidden marker `<!-- shipd-semantic-review -->` (editing the
existing marker comment in place on re-runs, and recognizing the legacy marker
`<!-- am-semantic-review -->` on lookup while writing only the current one),
posting inline comments only for findings whose `location` anchors to a
RIGHT-side commentable line of the pull request diff, folding unanchorable
findings into the summary, retrying once with no inline comments if the review
POST is rejected, submitting that review with the event `COMMENT`, and setting
a commit status with context `semantic-review` on the pull request's head SHA.

Where a finding declares its fix confident and supplies a replacement covering
one or more contiguous whole lines that anchor to a RIGHT-side commentable
line, its inline comment SHALL carry that replacement as a committable
`suggestion` block so the fix can be applied without retyping. A finding whose
replacement is absent, covers part of a line, spans a discontiguous range, or
does not anchor SHALL render as prose instead. Emitting a suggestion SHALL NOT
change the comment's leading severity marker, and the `--json` mode SHALL stay
free of emoji and prose.

#### Scenario: A confident whole-line fix becomes committable
- **WHEN** a finding declares its fix confident with a replacement covering
  contiguous whole lines that anchor to the diff
- **THEN** its inline comment contains a `suggestion` fenced block carrying
  that replacement

#### Scenario: A multi-line replacement is supported
- **WHEN** a confident finding's replacement covers more than one contiguous
  whole line
- **THEN** the suggestion block carries every one of those lines

#### Scenario: An unanchorable fix stays prose
- **WHEN** a finding declares its fix confident but its location does not
  anchor to a RIGHT-side commentable line
- **THEN** it is folded into the summary and carries no suggestion block

#### Scenario: A partial-line fix stays prose
- **WHEN** a confident finding's replacement covers part of a line rather than
  whole lines
- **THEN** its comment carries no suggestion block

#### Scenario: The review is submitted as a comment
- **WHEN** the poster publishes a review for any verdict
- **THEN** the submitted event is `COMMENT`

#### Scenario: The severity marker is unchanged by a suggestion
- **WHEN** an inline comment carries a suggestion block
- **THEN** its body still opens with the shared severity marker that
  `parse_severity` reads

#### Scenario: Pass verdict posts green
- **WHEN** `post` publishes a `pass` verdict to a pull request that carries no
  marker comment yet
- **THEN** a summary comment carrying the marker is created and the head SHA's
  `semantic-review` status state is `success`

#### Scenario: Red verdict anchors findings inline
- **GIVEN** a `changes-requested` verdict carrying one finding that anchors to
  the diff and one that does not
- **WHEN** `post` publishes it
- **THEN** the anchoring finding becomes an inline comment, the other is folded
  into the summary, and the status state is `failure`

#### Scenario: Re-post updates instead of stacking
- **WHEN** `post` runs twice against the same pull request
- **THEN** exactly one marker comment remains, the second run having edited the
  first rather than adding another

#### Scenario: Legacy-marker summary is updated, not duplicated
- **GIVEN** a pull request whose summary comment carries the legacy marker
  `<!-- am-semantic-review -->`
- **WHEN** `post` runs against it
- **THEN** that comment is edited in place, its new body carries the current
  marker, and exactly one summary remains

#### Scenario: High-only greens over mediums
- **WHEN** `post --disposition high-only` publishes a verdict whose findings
  are medium and low only
- **THEN** the status state is `success`, its description names the acting
  scope, and the summary carries both findings and a `Disposition:` line

#### Scenario: High-only stays red on a high
- **WHEN** `post --disposition high-only` publishes a verdict carrying a
  high-severity finding
- **THEN** the status state is `failure`

#### Scenario: None is always green and stays honest
- **WHEN** `post --disposition none --model <tier>` publishes a verdict
  carrying a high-severity finding
- **THEN** the status state is `success` and the summary still carries that
  finding, a `Disposition:` line, and a `Model:` line naming the tier verbatim

### Requirement: Skill post-to-PR flow
id: skill-post-flow
base: 586808a10517

Where the user explicitly asks for a review to be posted, the `/s:review`
skill SHALL run the review, emit the machine verdict, and publish it via the
poster, passing through the disposition scope and model tier when the invoker
supplied them (defaults: scope `all`, no tier). The skill SHALL then
disposition findings by scope. Under `all`, the flow SHALL run the full loop
over every posted finding regardless of severity: implement the suggestion
when it is correct — by editing, committing and pushing, or by the finding's
committable suggestion having been applied on the pull request, which counts
as the same implement branch and needs no separate reply — otherwise reply on
the finding's thread with the concrete reason via the gate's reply verb, never
leaving a finding with neither. Under `high-only`, the flow SHALL implement (or
push back with a reasoned reply) only the high-severity findings, re-reviewing
and re-posting after any push, and SHALL then run the gate's autoreply verb so
the remaining threads carry disposition evidence. Under `none`, the flow SHALL
perform no per-finding judgment and SHALL run the autoreply verb over every
gate thread. Every scope SHALL finish by running the gate's resolve verb and
reporting the posted status state, the summary comment URL, the acting scope
when it is not `all`, and the unresolved count, which SHALL be zero on a
completed disposition.

#### Scenario: An applied suggestion needs no reply
- **WHEN** a posted finding's committable suggestion has been applied on the
  pull request and the disposition loop runs under scope `all`
- **THEN** that finding is treated as implemented, no reply is required on its
  thread, and the completed disposition still reports an unresolved count of
  zero

#### Scenario: An unimplemented finding still needs a reason
- **WHEN** a posted finding is neither implemented nor carries an applied
  suggestion
- **THEN** the flow replies on its thread with the concrete reason before
  resolving

#### Scenario: Sensible suggestion is implemented before merge
- **WHEN** a posted finding's fix is correct and the disposition loop runs
  under scope `all`
- **THEN** the fix is edited, committed and pushed, and the review is re-run
  and re-posted against the new head

#### Scenario: High-only spends judgment only on highs
- **GIVEN** a posted review carrying one high finding and two medium findings
- **WHEN** the disposition loop runs under scope `high-only`
- **THEN** the high finding is implemented or answered individually, the
  autoreply verb covers the medium threads, and the resolve verb reports an
  unresolved count of zero

#### Scenario: None costs no disposition judgment
- **WHEN** the disposition loop runs under scope `none`
- **THEN** no finding receives an individually authored disposition, the
  autoreply verb covers every gate thread, and the resolve verb reports an
  unresolved count of zero
