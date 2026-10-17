# merge-rules
Status: complete
Theme: reliability

## Introduction

Today a shipd pull request merges when two checks are green and its threads
are resolved. Nothing on GitHub requires that anyone other than the author
approved it, and the PR-room tests showed why that matters: the author's agent
and the reviewer's agent both posted as one GitHub login, so GitHub saw one
person, and the "two agents agreed" story was enforced only by the agents'
own good behaviour.

This epic makes auto-merge rules a repository fact GitHub enforces, shaped
like a real team. The author's agent works under the author's account. A
reviewer's agent works under a second account, a teammate. A CI reviewer runs
as the GitHub Actions bot. The repository declares its merge rules once, in
config, and shipd applies them to the GitHub ruleset: by default two
approvals from accounts other than the author, approvals dismissed when new
code lands, the latest push approved by someone who did not push it, and
every required check green on the head commit. No GitHub App is required.

Success criteria:

- A rerun of the unkannybanny test merges only after GitHub itself records
  two approvals from two identities other than the author, and a push after
  an approval visibly removes that approval until it is given again.
- `shipd doctor` reports any drift between the configured rules and the live
  ruleset, and reads rulesets as protection rather than calling `main`
  unprotected.

### Non-goals

- No GitHub App per reviewer; identity comes from separate accounts and the
  built-in Actions bot.
- No strict "up to date with main" requirement by default, and no merge
  queue; strict mode is an opt-in setting only.
- No creation of GitHub accounts or tokens on the user's behalf; shipd
  documents and verifies them.
- No change to review findings, severities, or the review engine itself.

## References

- [GitHub merge enforcement without a GitHub App](../../docs/github-merge-enforcement/doc.md) — what rulesets can enforce and who counts as an approver, with sources.

## Decisions

- **Rules live in config, GitHub enforces them.** A new recognized config key
  `merge` declares the rules: `approvals` (int, default 2), `dismiss_stale`
  (bool, default true), `last_push_approval` (bool, default true),
  `required_checks` (list, default `["ci", "semantic-review"]`),
  `thread_resolution` (bool, default true), and `strict` (bool, default
  false). A typed resolver in `spec_common.py` validates it and raises a
  `ConfigError` naming `merge` and the file on a bad value. The repository is
  the source of truth; the ruleset is its applied form.
- **One ruleset, owned by shipd.** `shipd gate rules apply` creates or updates
  a single repository ruleset named `shipd merge rules` targeting the default
  branch, mapping the config to its `pull_request` and
  `required_status_checks` rules. It never edits another ruleset, and it
  prints the diff it applied. `shipd gate rules` with no verb prints the
  live ruleset next to the config and changes nothing.
- **Approvals, not comments.** The review gate's poster submits a review with
  event `APPROVE` when its verdict is pass and `REQUEST_CHANGES` when it is
  fix-required, replacing today's `COMMENT`, so a reviewer's verdict counts
  toward required approvals. This deliberately reverses the `COMMENT`-only
  rule documented on `REVIEW_EVENT` in `review_gate.py` and in the installed
  workflow, which avoided a second block that a human must dismiss by hand.
  The reversal holds because the same account's next review on the new head
  supersedes its earlier one, so a stale `REQUEST_CHANGES` clears when the
  gate re-posts. The `REVIEW_EVENT` constant, the workflow's review payload,
  and the test that pins `COMMENT` change together. The `semantic-review`
  status and summary comment are unchanged. An approval by the PR's author is
  never attempted.
- **Identity is the account, one per role.** The author's agent posts under
  the PR author's account. The reviewer's agent posts under a second account
  with write access, selected per session by `GH_TOKEN` (or a `gh` config
  directory) and never by switching the shared `gh` login. The room skill and
  the review flow refuse to approve when the acting login equals the PR's
  author, with a one-line explanation.
- **The CI reviewer is the GitHub Actions bot.** The installed review
  workflow submits its verdict as an `APPROVE` or `REQUEST_CHANGES` review
  using the workflow's own `github.token`, so github-actions[bot] is a third
  identity. `/s:gate` asks consent to enable the repository setting that lets
  GitHub Actions approve pull requests.
- **Doctor verifies, never silently fixes.** `shipd doctor` reads repository
  rulesets (replacing the classic-protection-only check), reports drift
  between `merge` config and the live ruleset line by line, and reports
  whether Actions may approve. Fixes run only through `/s:gate` with consent.
- **Every member bumps the plugin version and ships tests.** Tests use the
  existing fake `gh` runner seams; no test calls GitHub.

## Design

```
  .shipd-config.json  merge: {approvals, dismiss_stale, last_push_approval, ...}
            │
            ├── shipd gate rules apply ──► GitHub ruleset "shipd merge rules"
            └── shipd doctor ── drift ──►        │
                                                 ▼
   author agent  (author's account)   ──► pushes ──► PR head
   reviewer agent (second account)    ──► APPROVE / REQUEST_CHANGES
   CI reviewer   (github-actions[bot]) ──► APPROVE / REQUEST_CHANGES
                                                 │
                         GitHub: 2 approvals, none stale, checks green ──► merge
```

Four seams. The config key and the ruleset apply verb come first, since the
others are judged against them. The gate's approval event is independent of
the ruleset and can run alongside it. The CI reviewer's approval builds on
the gate's event. Per-agent identity touches the room skill and the review
flow, and lands after the approval event so its refusal rule has something to
refuse. The doctor check needs the config key and the ruleset shape. A final
member runs the unkannybanny test end to end with three identities.

## Changes

| Change | Description | Code | Integration | Unknowns | Risk | After |
| --- | --- | --- | --- | --- | --- | --- |
| merge-rules-config | The `merge` config key with a typed resolver, and `shipd gate rules` / `rules apply` mapping it onto one shipd-owned GitHub ruleset | medium | high | medium | medium | |
| gate-approves | The review poster submits APPROVE on pass and REQUEST_CHANGES on fix-required instead of COMMENT, never as the PR author | low | medium | low | medium | |
| ci-reviewer-approval | The installed review workflow approves or requests changes as github-actions[bot]; `/s:gate` offers the setting that lets Actions approve | medium | high | medium | medium | gate-approves |
| agent-identity | Per-session account selection for agents, documented second-account setup, and a refusal to approve one's own PR in the room and review flows | medium | medium | medium | medium | gate-approves |
| doctor-ruleset-drift | `shipd doctor` reads rulesets, reports drift against `merge` config, and reports whether Actions may approve | low | medium | low | low | merge-rules-config |
| team-merge-test | Apply the rules to unkannybanny and rerun the two-agent test with author, second-account reviewer, and CI reviewer | low | high | medium | medium | merge-rules-config, ci-reviewer-approval, agent-identity, doctor-ruleset-drift |
