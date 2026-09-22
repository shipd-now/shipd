# review-gate-integrity
Status: verified

## Idea

Repair five defects in the Copilot review gate and make a missing difftastic
fail the review loudly instead of degrading to the text engine.

### Motivation

The gate silently reports judgements it never made: its difftastic download
404s, its reviewer cannot reach the pinned instructions it is told to follow,
and its verdict parse falls open whenever the reviewer narrates after its
report. A review whose engine varies silently is equally unauditable, because
`semdiff` stamps the engine it used and nothing reads it.

### Details

- Pin the difftastic release version in the gate workflow and in the engine's
  own installer, and fail the gate step when the download fails.
- Pin the reviewer's instructions by overwriting the checkout's skill file
  with the base ref's copy, and pass `--add-dir` for the findings file.
- Read the verdict by scanning backwards for a line equal to a marker.
- Make `semdiff diff` exit non-zero when `difft` is absent.
- Install difftastic in `ci` so the difft-gated assertions run there.

Affected capabilities: `semantic-review` and `copilot-review-skill` (both
modified). Impact: `plugins/s/integrations/copilot/copilot-review-gate.yml`,
`plugins/s/skills/review/scripts/semdiff.py`,
`plugins/s/skills/review/SKILL.md`, `plugins/s/skills/review/tests/`,
`.github/workflows/ci.yml`, `plugins/s/.claude-plugin/plugin.json`. No new
dependencies.

### Non-goals

- The text engine is not removed. The per-file parse-failure retry keeps it
  reachable, so it stays supported and tested.
- The poll-fallback path's own Copilot review is not changed; only the
  verdict classifier it shares is.
- No `--require-difft` flag or config key. The hard failure is unconditional.
- The residual verdict window is documented, not closed.

## Implementation

- **The verdict scan walks backwards, bounded at 200 lines.** It takes the
  last line *equal* to a marker rather than requiring the last line to be
  one. Equality against a whole line preserves the anti-quoting property the
  current rule exists for: a marker quoted mid-sentence, or inside the
  transcript's `│`-prefixed tool-call log, is not a line equal to one. The
  bound stops a 65,536-character body from making the scan walk the whole
  text. Trailing-whitespace tolerance uses `%%` (prefix removal), never `##`,
  whose quadratic retry the workflow's existing commentary measured at 64
  seconds. Rejected: instructing the reviewer to emit nothing after the
  marker — a prompt cannot constrain the CLI's own transcript output, which
  is what lands after it.
- **One residual window is accepted and documented.** A bare marker standing
  alone on its own line inside trailing narration is still read as the
  verdict. That is a far smaller window than failing open on narration, but
  it is real and the workflow says so rather than leaving it implicit.
- **Instruction pinning is enforced, not requested.** The base ref's
  `.github/skills/code-review/SKILL.md` overwrites the checkout's own copy,
  so the CLI's skill discovery finds the pinned contract without being asked
  to prefer it. Rejected: keeping the copy in `$RUNNER_TEMP` and adding
  `--add-dir` alone — that makes the file reachable, not used, leaving the
  pinning advisory while removing the permission-denied lines that made the
  failure visible. The reviewer diffs base against head through git objects,
  so overwriting a working-tree file does not hide the reviewed change from
  the diff; it only stops that change from governing its own review. The
  existing `base_commit` resolution and its hard failure are unchanged.
- **`--add-dir` is still required, for the findings file alone.** The
  reviewer writes it into `$RUNNER_TEMP`, a sibling of the checkout that
  `--allow-all-tools` does not bring inside the CLI's path sandbox.
- **Difftastic is pinned in both places.** `0.71.0` publishes
  `difft-0.71.0-x86_64-unknown-linux-gnu.tar.gz`; the unversioned name the
  workflow and `semdiff.py` request stopped being published after `0.65.0`.
  Pinning matches the template's own reasoning for `@github/copilot@1.0.80` —
  a vendor's release schedule must not change what the gate runs. Rejected:
  resolving the newest tag from the API, which reintroduces exactly the
  un-pinning the template argues against.
- **The hard failure uses the existing exit convention.** `semdiff`'s `die()`
  exits 1 and `doctor` already returns 1 for a missing required tool, so the
  absent-difft failure reuses that rather than inventing a code.
- **`ci` installs difftastic before the review suite.** Five assertions are
  gated behind `@unittest.skipUnless(HAVE_DIFFT, …)` and are skipped in CI
  today; with `semdiff diff` hard-failing they would otherwise take the whole
  suite down. Those five have never run in the pipeline, so expect them to
  need repair.

Risk: pinning difftastic means a manual bump to adopt a newer release. That
is the intended trade — the gate's engine version becomes a reviewed
decision rather than whatever shipped this morning.

## Questions and answers

### Q1: Where does a missing difftastic become a hard failure?
- **Question:** Should the hard failure sit at the review and gate layer,
  leaving `semdiff diff` degrading; in `semdiff diff` itself, reversing
  `text-fallback` wholesale; or behind a `--require-difft` flag defaulted on
  for the gate? Recommendation: the review and gate layer.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** In `semdiff diff` itself. The engine exits non-zero when
  `difft` is absent, reversing `text-fallback`. This strands the difft-free
  CI scenario, so installing difftastic in `ci` joins this change.
- **Queued:** q-difft-missing-hard-failure-site

### Q2: One change for the defects and the behaviour change, or split?
- **Question:** Should five defects and one behaviour change ship as one
  change, as two (defects first), or as an epic? Recommendation: split, since
  the instruction-pinning defect is a live security hole and the behaviour
  change contradicts a verified requirement.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** One change for all six. They share the difftastic thread and
  one worktree.
- **Queued:** q-change-scope-defect-bundle-with-behaviour-change
