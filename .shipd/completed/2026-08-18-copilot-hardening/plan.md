# copilot-hardening
Status: verified

## Idea

Harden the Copilot integration around what dogfooding surfaced: a
repo-configurable strictness knob for the gate, a fail-soft setup checkout
that stops GitHub's new PR-visible failure notices on private repositories,
and the two verified semdiff engine defects from the selftest review.

### Motivation

A strict repository has ruled that a marker-less review must never green
the required check — its operators patched the installed workflow locally,
which the next `shipd copilot add` would revert — and GitHub now posts a
visible `ccr-setup-step-failure` notice on every Copilot-reviewed pull
request whose setup checkout fails, which is every review on a private
repository. Alongside these, two selftest-review findings against the
engine were verified live: an emptied-but-existing file classifies
`deleted` and a filled previously-empty file classifies `added`, and the
release-tarball installer would extract a non-regular archive member.

### Details

- `integrations/copilot/copilot-review-gate.yml`: the classification step
  reads the repository Actions variable `SHIPD_GATE_FAIL_OPEN`; unset or
  anything but `false` keeps today's fail-open `success`, while `false`
  turns every no-marker outcome into log-and-exit with the status left
  `pending`, on all three classify paths.
- `integrations/copilot/copilot-code-review.yml`: the checkout step becomes
  `continue-on-error`, the difftastic/ripgrep steps run only when it
  succeeded, and the difftastic step fails with a clear message when the
  archive holds no `difft` binary.
- `plugins/s/skills/review/scripts/semdiff.py`: distinguish empty-at-ref
  from absent-at-ref in blob reads so kinds classify correctly, and refuse
  a non-regular archive member in the release-binary installer.
- `docs/copilot-review.md`: document the knob and the fail-soft setup
  behavior on private repositories.
- Version bump `0.6.133` -> `0.6.134`.

Affected capabilities: `copilot-review-skill` (modified),
`semantic-review` (modified), `project-readme` (modified). Impact: the two
workflow templates, `plugins/s/skills/review/scripts/semdiff.py`,
`plugins/s/skills/build/tests/test_copilot_verb.py`, the review engine's
test suite, `docs/copilot-review.md`,
`plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No change to the fail-open **default** — strictness is opt-in per repo;
  the standing decision stands.
- No removal of the setup checkout (the public-repo test proved CCR skill
  loading depends on the checkout this step produces) — fail-soft only.
- No rework of the CRLF strip's bash-3.2 pathology (the workflow declares
  `ubuntu-latest`, where it classifies in under a second).
- No change to the CLI reviewer or poll mechanics beyond the knob.

## Implementation

- **The knob is a repository Actions variable, read at classify time.**
  `env: SHIPD_GATE_FAIL_OPEN: ${{ vars.SHIPD_GATE_FAIL_OPEN }}` on the
  gate job; in the shared classification block the no-marker branch tests
  `[[ "${SHIPD_GATE_FAIL_OPEN:-true}" == "false" ]]` — strict: log that no
  verdict was parsed and exit 0 leaving `pending` (the session flow
  `review_gate.py post` stays the manual out); default: today's fail-open
  `success` with the no-verdict description. One knob, one branch, all
  three paths (CLI output, polled review, review event) because they share
  the classifier. Rejected: a workflow-file edit per repo — it dies on
  every template refresh, which is the problem being solved.
- **Fail-soft setup checkout.** In `copilot-code-review.yml` the checkout
  step gains `id: checkout` and `continue-on-error: true`; the difftastic
  and ripgrep steps gain `if: steps.checkout.outcome == 'success'`. On a
  private repository the setup job then completes green — which is what
  GitHub's `ccr-setup-step-failure` notice keys on — while public
  repositories keep the working checkout that CCR skill loading reads
  from. Whether the notice actually disappears is GitHub-side behavior;
  the change is correct either way and the dogfooding repo verifies it on
  its next review run. The difftastic step also guards its `find` result:
  an archive with no `difft` binary fails that step with a clear message
  instead of invoking `install` with an empty path.
- **Engine fix: empty is not absent.** The blob reader returns a sentinel
  distinguishing "absent at ref" from "present with empty content"
  (verified live: emptying a tracked file misreports `deleted`, filling a
  previously-empty file misreports `added`); kind classification uses
  presence, not emptiness, so those cases classify `modified`. The
  whitespace-only filter's behavior is preserved.
- **Engine fix: extract regular files only.** The release-tarball
  installer selects the `difft` member by name; it now also requires the
  member to be a regular file (`isreg()`), refusing symlinks or other
  non-regular members with a clear error.
- **Docs:** the merge-gate section gains the knob (name, default, strict
  semantics, `gh variable set SHIPD_GATE_FAIL_OPEN --body false` as the
  enable path) and the prerequisites note gains the fail-soft setup
  behavior (private repos: setup completes, installs skipped, reviews
  classify per gate mode).
- **Version bump** `plugins/s/.claude-plugin/plugin.json` `0.6.133` ->
  `0.6.134`, per the cache-snapshot rule in `AGENTS.md`.
