# pr-conversations
Status: ready
Theme: developer-experience

## Introduction

A person who opens a pull request built and reviewed by shipd agents cannot
tell what happened on it. The end-to-end test on
https://github.com/mikkel-bergmann/unkannybanny/pull/14 showed five faults at
once. The pull request's own description reads like a stray comment. Every
agent posts under the same GitHub account, so four comments look like one bot
repeating itself. The review summary vanished, because the reviewer agent's
`room join` overwrote the gate's summary comment with a one-line card. The
author's agent agreed with a finding but, being prose-only, could not fix it,
so the flaw merged. And a finding had to be closed twice, once as a room task
and again on its inline review thread, before the merge would go through.

This epic makes a shipd pull request read like a conversation between two
named parties, about a change that explains itself. The pull request opens
with a short `☕ Shipd Pull Request` description written to the documentation
standard, under a title that can carry a ticket number. Every agent comment
names its agent, its role, and the person it acts for. The author's agent fixes
what the reviewer finds and answers on the finding's own thread, which closes
it. The verbs and the room skill stop tripping on working directories and on a
merge that lands mid-conversation.

Success criteria:

- A rerun of the PR 14 test leaves a pull request whose description, review
  summary, and every agent comment a person can attribute and follow without
  reading markers.
- A finding the author's agent fixes ends with a commit on the pull request and
  a resolved inline thread, with no second close.
- No room verb overwrites a comment it did not author for that purpose.

### Non-goals

- No separate GitHub App or bot accounts per agent; identity lives in the
  comment text. App identities are a later epic if wanted.
- The reviewer's agent never edits the author's branch.
- No change to the review gate's findings, severities, or verdict logic.
- No migration of comments already posted on existing pull requests.

## Decisions

- **Identity lives in the comment.** Every agent comment opens with a visible
  heading `☕ shipd · <agent> · <role> (for @<login>)`, where `<role>` is the
  card's role (`author`, `reviewer`, or `ci`) and `<login>` is the GitHub login
  the verb posts as, read once per verb from `gh api user`. The addressee and
  task state follow on the heading's next line. A card gains an optional
  `role` field; `room join --role <role>` sets it. Rejected: GitHub App
  identities, which need an App install and token handling per repository.
- **A room verb edits only what it owns.** `join` updates a comment only when
  that comment's sole room marker is this agent's own card. A card that lives
  inside another comment, such as the gate's card in the review summary, is
  never rewritten by `join`; `join` then posts the agent's card as its own
  comment. No verb PATCHes or DELETEs a comment that carries the
  `shipd-semantic-review` summary marker.
- **Finding replies go on the finding's thread.** A reply to a
  `review-finding` task, whose task id is the inline review comment's id, posts
  as a reply in that review thread, carrying the same room marker. A
  `completed` reply resolves that thread through the same GraphQL mutation
  `review_gate.py resolve` uses, so `resolve --check` already counts it. Every
  other task's traffic stays issue comments. This supersedes the `pr-room`
  epic's issue-comments-only rule for findings; the merge-blocking concern
  behind that rule does not apply to a thread the gate already opened.
- **Only the author's agent changes code, and only its own pull request.** A
  card with role `author` may, while working a `review-finding` task, edit,
  commit, and push to the pull request's head branch, then reply `completed`
  naming the commit. Every other role stays prose-only and hands code work to
  `/s:fix` or `/s:plan` as today.
- **A pull request describes itself.** `/s:pr` writes the title and body of a
  shipd pull request. The body opens with the heading `## ☕ Shipd Pull
  Request`, then a why-first paragraph and a short list of what changed,
  written to the documentation standard through `/s:document`'s rules and lint,
  and ends with the generated-by line. `/s:build`, the autopilot, and every
  skill that opens a pull request call `/s:pr` instead of `gh pr create
  --fill`.
- **Titles follow a configurable template.** A new config key `pr` holds
  `title` (default `"{summary}"`) and `ticket_pattern` (a regular expression,
  default unset). Placeholders are `{ticket}`, `{summary}`, and `{change}`. The
  ticket comes from `/s:pr --ticket <id>`, else from the first
  `ticket_pattern` match in the branch name; with no ticket, `{ticket}` and the
  whitespace after it drop out. The existing `pr-mode` key is unchanged.
- **Verbs resolve the repository the same way everywhere.** Every room verb
  already resolves through one function, `_resolve_room`, which reads the
  repository from `gh repo view` in the working directory, so a verb run
  outside the checkout fails. Every room verb accepts a pull request URL or
  `--repo <owner/name>`, and that function takes the repository from them
  first and falls back to the working directory.
- **A merge does not strand a conversation.** The reviewer's agent merges only
  when the room holds no task in `working` or `input-required`. When `watch`
  sees the pull request closed, its `closed` line lists any such tasks, and the
  room skill reports them as unresolved.
- **Every member bumps the plugin version and ships tests.**

## Design

```
  /s:pr ── title template (pr.title, ticket) ── body: ## ☕ Shipd Pull Request
     │
  pull request
     │
     ├── review summary  (gate; never rewritten by join)
     ├── inline finding thread ── author's reply + fix commit ── resolved
     └── issue comments: cards and messages, each headed
           ☕ shipd · <agent> · <role> (for @login)
```

Five seams. The join fix and the identity heading touch the room schema and
`join`, so the fix lands first and the heading builds on it. Threaded finding
replies need both: they post into the gate's threads, which `join` must leave
alone, and they carry the new heading. Turn hygiene changes repository
resolution and the merge rule across every verb, so it follows the threaded
work. `/s:pr` touches only pull-request creation and the config, and runs in
parallel.

## Changes

| Change | Description | Code | Integration | Unknowns | Risk | After |
| --- | --- | --- | --- | --- | --- | --- |
| room-join-owns-its-card | `join` edits only a comment whose sole marker is its own card; never touches the review summary | low | medium | low | medium | |
| room-speaker-identity | Every agent comment opens with `☕ shipd · agent · role (for @login)`; cards gain `role`; the review submission body is branded | medium | medium | low | low | room-join-owns-its-card |
| room-threaded-findings | Finding replies post on the inline thread and a completed reply resolves it; the author's agent may commit fixes to its own pull request | high | high | medium | high | room-speaker-identity |
| room-turn-hygiene | One repository resolver for every verb, merge only with no open tasks, and the `closed` line lists open tasks | medium | medium | low | medium | room-threaded-findings |
| pr-writer-skill | `/s:pr` writes a titled, branded, standard-checked pull request; the `pr` config key; build and autopilot call it | medium | medium | medium | medium | |
