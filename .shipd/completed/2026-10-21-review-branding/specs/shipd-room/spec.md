## ADDED Requirements

### Requirement: A reviewer answers a review request with the shipd review
id: room-skill-reviewer-review

When an agent whose card role is `reviewer` works a surfaced task that is addressed to it and asks it to review or re-review the pull request, the `/s:room` skill SHALL have it, after claiming the task `working`, run `shipd room whoami <pr>`. On a non-zero exit it SHALL relay the `Error:` line and stop without posting a review. On a zero exit it SHALL run `/s:review <pr-url> status=auto room-agent=<to> room-to=<last_agent>`, where `<to>` and `<last_agent>` are the surfaced task's own `to` and `last_agent` fields. That review posts through `review_gate.py post --status auto` as:

- the shared branded summary comment;
- anchored inline comments, each opening a `review-finding` task addressed to the asker;
- an `APPROVE` or `REQUEST_CHANGES` review by the acting login whose body carries the full branded summary.

The skill SHALL state the status rule: where `.github/workflows/copilot-review-gate.yml` exists on the pull request's base commit, the CI gate owns `semantic-review` and the reviewer sets no status; where that file is absent (the contents read returns 404), the reviewer's post sets `semantic-review` itself; on any other read failure it sets none. The skill SHALL then close the request task `completed` with a reply naming the verdict and the summary comment URL. The reviewer SHALL NOT submit a separate freeform `gh pr review`. A re-review request after the head moved SHALL run the same command, so the one summary comment is edited in place with the earlier verdict in its Earlier-reviews block, and a new full review lands on the new head. Posting that review is not a code change: the no-code rule for non-author roles still holds. The harness body `plugins/s/harness/bodies/room.md`, its reference `plugins/s/harness/references/room.md`, and `docs/room-run.md` SHALL carry the same rule.

#### Scenario: Skill names the review command and its options
- **WHEN** the room skill test reads `plugins/s/skills/room/SKILL.md`
- **THEN** it finds `/s:review`, `status=auto`, `room-agent=`, `room-to=`, `last_agent`, and `shipd room whoami` named before the `/s:review` line

#### Scenario: Skill states both status cases
- **WHEN** the room skill test reads the skill
- **THEN** it finds `.github/workflows/copilot-review-gate.yml`, `semantic-review`, the case where the file is present (no status set), and the case where it is absent (the post sets it)

#### Scenario: Skill forbids a freeform review
- **WHEN** the room skill test reads the skill
- **THEN** it finds `gh pr review` named as one the reviewer never submits

#### Scenario: Harness body and reference carry the rule
- **WHEN** `harness_bodies.render("room", ("background-tasks",), refs_dir="R")` runs and the reference is read
- **THEN** each names `/s:review`, `status=auto`, `room-to=`, and `copilot-review-gate.yml`

#### Scenario: The how-to names the branded review and both status cases
- **WHEN** the room skill test reads `docs/room-run.md`
- **THEN** it finds `/s:review`, `semantic-review`, and `copilot-review-gate.yml` in the reviewer section
