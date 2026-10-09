# copilot-rubric-deferral
Status: verified
Theme: reliability

## Idea

### Motivation

`copilot-review-skill`'s `skill-template` requirement carries its own copy of
the severity rubric's `low` definition and impact floor, and that copy has been
wrong since v0.6.275. It demands the template say `low` is "a real defect whose
impact is contained" and that "uncertainty about a severity is not grounds for
omitting a finding". The template says neither: v0.6.275's revert restored
v0.6.260's kinds-list `low` to `SKILL.md` and aligned the template to it,
deliberately, and the same revert removed the no-omission sentence from every
surface.

So the capability has been describing a template it does not match for two
versions. The semantic review on PR 286 found it.

The cause is the second copy, not the revert. Two requirements stated the same
rubric wording, one changed, and nothing compared them. The repository already
has the remedy as an established pattern: `harness-command-bodies`'
`body-content` says "This capability owns that number: a surface that states a
rendered-body size budget SHALL reference this requirement rather than
restating the figure, so the budget has one source of truth", and
`review-skill-references` does the same for its line ceiling.

### Details

`skill-template` stops restating the rubric and defers to `review-skill`, which
owns it.

### Non-goals

- **The template itself does not change.** Its wording is correct and
  deliberate. This change moves the requirement to match the implementation,
  because the implementation is the intended one.
- **No `plugins/s/` file is touched, so no plugin version bump.** That is
  deliberate while a ReviewBench measurement is running against v0.6.276: a new
  version string would invite a `claude plugin update` on the shared
  user-scope cache mid-run. The drift guard that belongs in
  `test_skill_references.py` is queued behind that run for the same reason.
- No change to `review-skill`, which already owns the wording.
- No change to the rubric on any surface.

## Implementation

One MODIFIED requirement, `copilot-review-skill` / `skill-template`.

The paragraph restating the `low` definition, the impact floor and the
no-omission rule is replaced by a deferral: the template's rubric states the
same `low` definition, floor and concrete instances that `review-skill`
requires of `SKILL.md`; `review-skill` owns that wording and this requirement
does not restate it. The clause that the template must carry the wording
**inline** stays, since it is vendored byte-for-byte into a GitHub Actions
runner and can read no reference file — that is the one thing this requirement
knows that `review-skill` does not.

Its two rubric scenarios are replaced to match. The first compares the
template's rubric against `SKILL.md` rather than against a transcription. The
second asserts this requirement restates no rubric wording, so the drift cannot
return by someone re-adding a copy.

### What this leaves unguarded, named rather than hidden

No test yet compares the template's `low` bullet against `SKILL.md`'s. That is
the guard that would have caught this in v0.6.275, and it belongs in
`plugins/s/skills/review/tests/test_skill_references.py` beside
`ImpactFloorParityTest`. It is deliberately not in this change: that file is
under `plugins/s/`, so adding it requires a version bump, and a new version
mid-measurement risks a shared-cache update on the machine running the rounds.
Queued, not forgotten.

## Readiness attestation

### Problem and motivation

A requirement describes a template it does not match, because it holds a second
copy of wording another requirement owns.

Evidence, read in this worktree: `skill-template` demands `low` be "a real
defect whose impact is contained" and that the template state uncertainty is
not grounds for omitting a finding;
`plugins/s/integrations/copilot/SKILL.md` says `low` is "a real but minor
defect" followed by the kinds list, and carries no no-omission sentence. Its
third demand — the concrete instances — is met, by v0.6.276.

### Scope and non-goals

In scope: one MODIFIED requirement in `copilot-review-skill`, its two rubric
scenarios.

Out of scope: every file under `plugins/s/`, the plugin version, the template's
own wording, `review-skill`, and the parity test that is queued behind the
running measurement.

### Affected capabilities and files

One capability, one requirement: `copilot-review-skill` / `skill-template`,
base `dc48a0e502c3` as computed by `spec_status.py base-hash` here.

Files: `.shipd/verified/copilot-review-skill/spec.md` only, via the delta.

Runnable premises measured here: `spec_status.py base-hash` returns
`dc48a0e502c3`; the requirement's restating paragraph occurs exactly once; both
scenarios being replaced occur exactly once; and
`grep -c "impact floor" plugins/s/integrations/copilot/SKILL.md` is 0, so the
template states the floor's substance without the label — which is why the new
scenario compares meaning against `SKILL.md` rather than matching a label.

### No open task-shaping decision

- Which side changes, the requirement or the template: the requirement,
  because v0.6.275 changed the template deliberately and documented why, and
  the template is what the skill it mirrors now says — settled above.
- Whether to transcribe the current wording or defer: defer, because a second
  copy is what produced this drift, and the repository already uses
  ownership-deferral for its two line ceilings — settled above.
- Whether the parity test ships here: no, it would force a plugin version bump
  during a live measurement — settled above, and queued.
