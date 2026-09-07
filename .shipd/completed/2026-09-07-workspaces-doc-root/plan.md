# workspaces-doc-root
Status: verified

## Idea

Teach `docs/workspaces.md` the `workspaces_root` config key that shipped in
v0.6.188, so the guide's recommended directory convention is documented as
mandatable.

### Motivation

The guide standardizes a `~/workspaces/<job>/` parent-directory convention but
never mentions `workspaces_root`, the key that mandates exactly that convention
— the `workspaces-root` change (archived at
`.shipd/completed/2026-09-07-workspaces-root/`) explicitly deferred the doc
rewrite as a non-goal, leaving the sample-config entry as the only
documentation.

### Details

- In §1 (one-time machine setup), document `workspaces_root` as a third
  optional `~/.shipd-config.json` key: declaring it mandates the convention —
  bare names to `shipd workspace init` resolve to `<root>/<name>` with the
  leaf created, explicit init targets and clone destinations outside the root
  are refused naming the target, the root, and the key, `--nested` job
  workspaces inside the root stay legal, and undeclared means no behavior
  change.
- In §2 (create a job workspace), show the bare-name shortcut the key enables
  alongside the existing explicit-path flow.
- Mention that `shipd config` reports the raw declared value (`~` unexpanded),
  that the installed sample config documents the key, and that doctor's
  existing `config` check fails on a malformed value and warns when the
  declared root directory is missing.
- Extend the `workspaces-doc` requirement in the `shipd-workspace` capability
  to require this coverage.

Affected capabilities: `shipd-workspace` (modified). Impact:
`docs/workspaces.md` only; no code, no dependencies, no plugin version bump.

### Non-goals

- No change to any engine script, skill, sample config, or doctor check — the
  behavior all shipped in v0.6.188; this documents it.
- No plugin version bump: nothing under `plugins/s/` changes (precedent: the
  docs-only `oracle-docs-advisory` change, commit 1842dc9, shipped without
  one).
- No restructuring of the guide — its voice, section order, and
  `shipd`-binary command style stay as they are; every other section is
  untouched.

## Implementation

- **Placement: §1 and §2, not a new section.** The key is machine-level
  user-layer config, so it joins `clone_sources` and `wiki_base` in §1's
  `~/.shipd-config.json` discussion, and §2 gets the bare-name convenience it
  enables — matching where the guide already introduces the convention the
  key mandates. Rejected: a dedicated section — the key is one paragraph of
  semantics, and the guide's other config keys (`store_root` aside, which
  owns workspace-level §7) are covered inline.
- **Semantics are copied from the merged contracts, not paraphrased loosely:**
  `shipd-config` req `workspaces-root-key`
  (`.shipd/verified/shipd-config/spec.md:872` — non-empty string, `~`
  expands, expanded value must be absolute, undeclared = unchanged),
  `shipd-workspace` init requirement (`spec.md:197` — bare-name re-target
  with leaf creation, out-of-root refusal naming target/root/key,
  root-and-descendants containment so `--nested` inside stays legal), the
  workspace skill's clone flow (`plugins/s/skills/workspace/SKILL.md:176` —
  no dest lands at `<root>/<derived-name>`, out-of-root dest refused before
  cloning), and doctor's `config` check
  (`.shipd/verified/shipd-cli/spec.md:969` — fail malformed, warn missing
  root).
- **Reporting claim verified by running the verb:** `spec_status.py
  config-show` in this repo prints
  `workspaces_root = "~/workflows"  [/Users/mikkelbergmann/.shipd-config.json]`
  — the raw declared value with `~` unexpanded, plus provenance — so the doc
  states exactly that, surfaced to readers as `shipd config` per the guide's
  binary-only command rule.
- **Delta shape:** one MODIFIED entry for `workspaces-doc` in
  `shipd-workspace`, appending the coverage mandate to the requirement text
  and two inspection scenarios, keeping every existing sentence and scenario
  verbatim — the same docs-catch-up delta shape `oracle-docs-advisory` used
  for `docs/oracle.md`.
- **Risk:** doc drift from the shipped behavior. Guarded by sourcing every
  stated behavior from the merged verified requirements above rather than
  memory, and by the delta scenarios pinning the coverage for future lints.
