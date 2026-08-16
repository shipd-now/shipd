## ADDED Requirements

### Requirement: Review-start difftastic auto-fix
id: review-difft-autofix

When the `/s:review` skill begins a review and `difft` is not on PATH, the
skill SHALL run the tiered installer (`semdiff doctor --fix`) once before
any analysis and re-probe for `difft` afterwards — reaching the network
solely through `--fix`, preserving the installer's network invariant. If
`difft` is still missing after that attempt, then the skill SHALL inform
the user prominently — naming the text-engine degradation and a manual
install hint — and SHALL record the degradation in the review's
could-not-verify output in both human and `--json` modes, and SHALL then
complete the review on the text engine; a missing difftastic never blocks
the review and the installer is attempted at most once per review.

#### Scenario: Successful auto-install restores the syntax-aware engine
- **WHEN** a review starts with `difft` absent and the tiered installer
  succeeds
- **THEN** the review proceeds on the syntax-aware engine with no
  degradation notice

#### Scenario: Failed auto-install informs and degrades loudly
- **WHEN** a review starts with `difft` absent and the tiered installer
  leaves it missing
- **THEN** the user is informed with the text-engine degradation and a
  manual install hint, the degradation is recorded in the could-not-verify
  output, and the review still completes on the text engine

#### Scenario: Present difft skips the installer
- **WHEN** a review starts with `difft` already on PATH
- **THEN** the installer is not invoked and the review proceeds directly
