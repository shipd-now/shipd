# shipd-evals-port
Status: verified
Epic: shipd-port
Theme: spec-engine

## Idea

Port the eval harness — its three cases, their fixtures, and the runner — onto
the `.shipd` layout and the `/s:` namespace, and prove it with a live run.

### Motivation

The unit suites cover the engine scripts; the LLM-facing skills are only
exercised by real sessions, which is exactly what `evals/` exists to close. A
ported plugin whose skills have never been run against a fixture is unverified
where it matters most.

### Details

- Port `evals/` at the pinned ref: `run.py`, `tests/test_runner.py`, and the three
  cases under `cases/` with their fixtures.
- Confirm each fixture's content directory landed as `.shipd/` with its
  `README.md`, `verified/`, `planned/`, and — for the video case — `video/`.
- Confirm the runner launches the ported plugin directory and grades against the
  ported layout.
- Run the runner's own unit tests, then a live eval run.

Affected capabilities: `shipd-port` (added). Impact: the shipd repo (`evals/`);
shipd unchanged.

### Non-goals

- No new eval cases. The three that exist port across; adding coverage is
  separate work.
- No wiring of evals into shipd's `ci`. They cost real model spend and need
  credentials, so they stay local and on demand, exactly as in shipd.
- No change to the runner's grading logic, resume behavior, or its `--runs` /
  `--max-resumes` contract beyond the namespace rewrite.

## Implementation

- **The fixtures are the reason this member is not a no-op.** Each case's fixture
  is a miniature repo carrying its own content directory — `.shipd/README.md`,
  `.shipd/verified/`, `.shipd/planned/`, and for the video case `.shipd/video/`. Those are
  *paths*, so the path map renames them; but the runner also joins the directory
  name as a bare quoted segment when it copies the host `README.md` into the
  scratch fixture and when it globs for the emitted change. The quoted-segment
  rule added to the port tool is what makes those land correctly, and this member
  verifies the result rather than assuming it.

- **The runner's plugin directory must point at `plugins/s`.** `run.py` launches
  each headless session against the host repo's plugin directory. After the port
  that path is `plugins/s`, and the skill it drives is `/s:plan`. Both come from
  the token map; both are asserted here, because a runner pointed at a
  nonexistent plugin fails in a way that looks like a model failure rather than a
  path failure.

- **Two levels of verification, cheap first.** `evals/tests/` exercises the
  runner's discovery and grading with no live session, so it runs first and
  catches a broken glob or a stale path for free. Only then does a live run spend
  model budget. Rejected: going straight to a live run — a path bug would burn a
  real session to report something a unit test finds instantly.

- **A live run is the acceptance bar, with model variance accounted for.** Eval
  outcomes are model-dependent, so a single failing case is not automatically a
  port regression. The member's bar is a passing run; a lone failure is re-run
  with `--runs` before being treated as a defect, matching shipd's own
  guidance.

Risk: the live run needs the `s@shipd` plugin working, so this member depends on
`shipd-identity` having landed. Running it earlier would fail for reasons that
have nothing to do with the evals.
