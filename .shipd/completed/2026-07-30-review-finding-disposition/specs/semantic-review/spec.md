## ADDED Requirements

### Requirement: Finding-thread reply verb
id: thread-reply-verb

`review_gate.py reply <pr> <comment-id> --body <text>` SHALL post a reply
onto the finding thread rooted at the given review comment, through the
same injectable `gh` seam as the poster, and SHALL print the created
reply's URL. An unknown PR or comment id SHALL exit non-zero.

#### Scenario: Push-back lands on the thread
- **WHEN** `reply 54 12345 --body "Deferred: pagination cap is documented"`
  runs
- **THEN** the thread rooted at comment 12345 gains that reply and its URL
  prints

### Requirement: Evidence-gated thread resolution
id: thread-resolution-verb

`review_gate.py resolve <pr>` SHALL resolve only review threads whose root
comment the gate authored, and only those carrying disposition evidence —
a reply exists on the thread, or the PR gained a commit after the thread
was created. Threads without evidence SHALL be listed as undispositioned
and the verb SHALL exit non-zero, resolving nothing else silently.
`resolve <pr> --check` SHALL mutate nothing, print `unresolved=<n>`
counting unresolved gate-authored threads, and exit zero only when the
count is zero. Human-authored threads SHALL never be touched.

#### Scenario: Replied thread resolves
- **GIVEN** a gate-authored thread carrying a push-back reply
- **WHEN** `resolve` runs
- **THEN** that thread is resolved

#### Scenario: Undispositioned thread refuses
- **GIVEN** a gate-authored thread with one comment and no later commit
- **WHEN** `resolve` runs
- **THEN** the thread is listed as undispositioned, left unresolved, and
  the exit code is non-zero

#### Scenario: Check counts without mutating
- **GIVEN** two unresolved gate-authored threads
- **WHEN** `resolve --check` runs
- **THEN** `unresolved=2` prints, nothing is resolved, and the exit code
  is non-zero

#### Scenario: Human threads are untouched
- **WHEN** `resolve` runs on a PR carrying an unresolved human-authored
  thread
- **THEN** that thread is neither resolved nor counted

## MODIFIED Requirements

### Requirement: Required-check protection verb
id: required-check-protect
base: 1b6776afd793

`review_gate.py protect` SHALL read the default branch's protection,
union `semantic-review` into the required status check contexts, set
`required_conversation_resolution` to true, and write back preserving
`strict` and every other protection field; `protect --remove` SHALL
remove the context and clear the conversation-resolution requirement the
same way. Both directions SHALL be idempotent — already in the desired
state means no write and exit zero — and the verb SHALL print the
resulting contexts and conversation-resolution state.

#### Scenario: Protect adds the check and the resolution requirement
- **GIVEN** required contexts `["ci"]` and conversation resolution off
- **WHEN** `protect` runs
- **THEN** contexts become `ci` and `semantic-review`, conversation
  resolution is required, and `strict` is preserved

#### Scenario: Remove restores the prior gate
- **WHEN** `protect --remove` runs on a protected branch
- **THEN** `semantic-review` leaves the contexts and conversation
  resolution is no longer required

### Requirement: Skill post-to-PR flow
id: skill-post-flow
base: a2135938f89f

Where the user explicitly asks for a review to be posted, the `/s:review`
skill SHALL run the review, emit the machine verdict, publish it via the
poster, and then run the disposition loop over every posted finding
regardless of severity: implement the suggestion (edit, commit, push) when
it is correct, otherwise reply on the finding's thread with the concrete
reason via the gate's reply verb — never leaving a finding with neither.
The flow SHALL finish by running the gate's resolve verb and reporting the
posted status state, the summary comment URL, and the unresolved count,
which SHALL be zero on a completed disposition. The skill SHALL NOT post
as a side effect of a plain review request.

#### Scenario: Sensible suggestion is implemented before merge
- **GIVEN** a posted low finding whose fix is correct
- **WHEN** the disposition loop reaches it
- **THEN** the fix is committed and pushed rather than left as advice

#### Scenario: Disagreement is answered, not ignored
- **WHEN** the session judges a posted finding not worth implementing
- **THEN** the finding's thread gains a reasoned reply and is then
  resolved

#### Scenario: Flow ends with zero unresolved
- **WHEN** the posting flow completes
- **THEN** the report includes `unresolved=0` from the resolve verb
