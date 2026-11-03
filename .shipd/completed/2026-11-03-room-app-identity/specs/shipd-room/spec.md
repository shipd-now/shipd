## MODIFIED Requirements

### Requirement: Room skill posts prose, and only the author's agent fixes findings
id: room-skill-no-code
base: 193e5d33be90

The skill SHALL read the agent's role as the `role` on its own card in
`shipd room list <pr> --json`. While working a surfaced `review-finding`
task, an agent whose role is `author` MAY edit, commit, and push code, only
when `shipd room whoami <pr> --author` exits `0` (the acting login is the pull
request's author, a GitHub App's `app/<slug>` and `<slug>[bot]` counting as
one account), the pull request is not cross-repository (`gh pr view <pr>
--json isCrossRepository` is `false`), the working tree is on the pull
request's head branch (`gh pr view <pr> --json headRefName` equals `git
branch --show-current`), and the tree is clean: it SHALL make the smallest
change that addresses the finding, run the tests covering the touched files,
commit, push with plain `git push` and never with `--force`, and close the
task `completed` naming the commit's short SHA. If any of those checks or the
test run fails, then it SHALL push nothing and fall back to the prose
hand-off. The skill, its harness body and its reference SHALL NOT ask the
agent to compare `author.login` with `gh api user` by hand. Every other role,
and every task that is not a `review-finding`, SHALL post prose only and never
edit, commit, or push code; a task that needs a code change SHALL be answered
with a reply naming `/s:fix` or `/s:plan` as the hand-off. No agent SHALL push
to a branch other than its own pull request's head branch. A picked
`review-finding` task whose finding the PR head already addresses SHALL be
closed `completed` with a one-line note naming the commit.

#### Scenario: Skill forbids code edits
- **WHEN** the room skill test reads the skill
- **THEN** it finds the no-code rule naming `/s:fix` and `/s:plan`, and the
  text `never edits, commits, or pushes code`

#### Scenario: Skill states the author's fix rule and its guard
- **WHEN** the room skill test reads the skill
- **THEN** it finds `author`, `review-finding`, `shipd room whoami <pr>
  --author`, `isCrossRepository`, `headRefName`, `git push`, and the rule
  never to push with `--force`, and does not find `gh api user`

#### Scenario: Harness body carries the same rule
- **WHEN** `harness_bodies.render("room", ("background-tasks",),
  refs_dir="R")` runs
- **THEN** the output names `author`, `whoami <pr> --author`,
  `isCrossRepository`, `headRefName`, `/s:fix`, and `/s:plan`, and the
  reference names `whoami <pr> --author` and not `gh api user`
