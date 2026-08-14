# change-failure-signal
Status: verified
Epic: delivery-metrics

## Idea

Define this pipeline's change-failure metric as post-merge remediation — a
base-branch revert or a shipped `Fixes:`-declared fix change — and derive the
DORA change-fail rate from it, surfaced beside the existing pre-merge rework
proxy.

### Motivation

The epic delegates the change-failure modelling decision to this member:
`derive()` today exposes only the pre-merge rejected/needs-human rework proxy,
and the linked research is explicit that a true DORA change-fail rate needs a
post-merge failure signal (a revert/hotfix link) that the pipeline does not
track.

### Details

- The model: a shipped change **has failed** when post-merge remediation
  exists — (a) a revert of its squash commit on the base branch, or (b) a
  later shipped change declaring `Fixes: <slug>`. Change-fail rate =
  failed / total shipped, counted once per change. The pre-merge `rework_rate`
  proxy stays, separately labelled.
- Capture: a new repeatable `Fixes:` plan-header metadata key
  (`spec_common.METADATA_KEYS`), read post-merge from the dated `completed/`
  archives' `plan.md` headers; reverts derive from git with zero new capture.
- Derivation: a pure `collect_change_failures` collector on `metrics.py`;
  `derive()` gains a `change_failures` block; the `summary` verb, em rollup,
  and exec rollup present the rate labelled post-merge (exec: the rate only,
  never a slug).

Affected capabilities: `delivery-metrics` (added `change-failure-signal`,
modified `metrics-engine`), `shipd-spec-format` (modified
`plan-header-metadata-lines`). Impact:
`plugins/s/skills/build/scripts/metrics.py`, `spec_common.py`, tests
`test_metrics.py` / `test_spec_lint.py`, plugin version bump. Stdlib-only
throughout.

### Non-goals

- No failed-deployment recovery-time metric — failure signals carry timestamps
  so a later member can derive it, but no recovery stat or headline ships here.
- No new event file or capture verb — no `failures.jsonl`, no `record-failure`;
  capture is the declarative `Fixes:` header plus git derivation.
- No removal or relabeling of the pre-merge rework proxy, and no DORA tier band
  for the change-fail rate (the linked research cites no CFR cluster
  thresholds for this pipeline to adopt).
- No lint existence-check that a `Fixes:` value names a real shipped change
  (kebab-case validation only).

## Implementation

- **Failure definition (the epic's delegated decision).** Post-merge
  remediation only: the pre-merge rejected/needs-human outcomes stay a
  separately-labelled proxy because they measure pipeline rework before
  deploy, not DORA's "deployment needing immediate intervention". Rejected:
  promoting the pre-merge proxy to the change-fail rate — the research
  classifies it as a proxy explicitly.
- **Revert detection** — `git_revert_signals(root, base_ref=None)` scans
  `git log --format` on `base_ref or "HEAD"` (the `git_change_times` idiom:
  stdlib subprocess, stderr devnulled, tolerant of no-repo/failure → `{}`,
  looked up as a module attribute at call time so tests monkeypatch it). A
  commit signals a revert of `<slug>` when its subject starts `Revert "` and
  the quoted text begins `<slug>:`; a revert-of-revert (quoted text starting
  `Revert `) never counts. Returns `{slug: [iso-utc-ts, ...]}` from committer
  dates.
- **Fix links** — `collect_fix_links(root)` scans
  `completed/<YYYY-MM-DD>-<slug>/plan.md`, parses the header with
  `sc.parse_plan_metadata`, and collects every `Fixes` pair as
  fixed-slug → [fixing slugs]. Only shipped fixes count (archives exist
  exactly for merged changes); a log-only shipped change cannot declare a fix —
  an accepted limitation. Rejected: a `fixes` field in `builds.jsonl` — the
  archive already records the header, and the epic's "derive, don't
  re-instrument" decision governs.
- **The block** — `collect_change_failures(root, ship_events, base_ref=None)`
  joins both signal maps over the shipped slugs:
  `{rate, n_failed, n_shipped, failed: [{slug, signals}]}` with signals
  `{kind: "revert", ts}` / `{kind: "fix", by}`, sorted by slug, rate `None`
  when nothing shipped, one failure per change regardless of signal count.
  `derive()` carries it as `change_failures`.
- **Surfaces** — summary prints
  `change-fail rate: X% (post-merge: reverts + declared fixes)` beside the
  rework line; the em rollup's `## rework` section gains the same line; the
  exec rollup's `headlines` gain `change_fail_rate` and its renderer the
  line — rate only, upholding the exec no-slug rule. All `_fmt_pct` /
  `n/a`-tolerant.
- **`Fixes` key** — appended to `sc.METADATA_KEYS`; the linter's
  unrecognized-key and kebab-case checks pick it up with no lint code change,
  and the key is repeatable (the metadata parser returns pairs; the
  Epic/Initiative mutual-exclusion rule is untouched).

Risk: squash subjects that stray from `<slug>: ...` make their reverts
unmatchable — accepted; the join runs over shipped slugs and an unmatched
revert is ignored rather than guessed.
