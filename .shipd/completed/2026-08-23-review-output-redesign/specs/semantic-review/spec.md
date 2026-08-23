## MODIFIED Requirements

### Requirement: PR posting of a review verdict
id: gate-poster
base: c91677ca9018

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

### Requirement: Skill post-to-PR flow
id: skill-post-flow
base: f62ba20eb092

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
