# guardrail-hook
Status: verified

## Idea

Ship a PreToolUse guardrail hook in the `s` plugin that intercepts Edit/Write
tool calls whose added lines match a registry of unwanted patterns — starting
with useless narrating code comments — and denies them with a corrective
instruction telling the agent what to do instead.

### Motivation

Execution agents (Opus 5 in particular) keep writing narrating, change-log,
and placeholder comments that reviewers then strip by hand, and nothing
intercepts the habit at write time. A deny-with-reason hook redirects the
agent in-flight, before the junk ever lands in a file.

### Details

- New stdlib-only engine script `plugins/s/skills/build/scripts/guardrails.py`:
  reads the PreToolUse JSON from stdin, extracts the added lines, matches them
  against the resolved rule registry, and denies with each violated rule's
  message.
- New `plugins/s/hooks/hooks.json` registering the script as a PreToolUse hook
  with matcher `Edit|Write` — auto-enabled wherever the user-scope plugin is
  enabled, so enforcement is on everywhere by default.
- Registry = three built-in comment rules merged with an optional `guardrails`
  key in the layered `.shipd-config.json` (disable rules, add rules, or turn
  the hook off per repo/user).
- Document the key in `.shipd/README.md` and the copyable config example.

Affected capabilities: `guardrail-hook` (added), `shipd-config` (modified).
Impact: `guardrails.py` (new), `hooks/hooks.json` (new),
`tests/test_guardrails.py` (new), `.shipd/README.md`,
`references/shipd.config.example.json`, `plugins/s/.claude-plugin/plugin.json`
(version bump to 0.6.152); no new dependencies.

### Non-goals

- No LLM or semantic judgment in the hook — deterministic regex only; nuanced
  comment quality stays with `/s:review` and the semantic-review gate.
- No PostToolUse, Stop, or prompt-level hooks — one PreToolUse event only.
- No changes to the review skill, the gate, or any existing engine script
  other than the new module.
- No rule authoring UI or CLI verb — the registry is edited as config JSON.

## Implementation

- **PreToolUse deny, not PostToolUse.** PreToolUse can deny with a
  `permissionDecisionReason` that is fed back to the model so it retries
  differently (Claude Code hooks reference, fetched 2026-08-25); PostToolUse
  cannot block — the junk would already be in the file. The deny reason is the
  redirect channel: it carries each violated rule's corrective message.
- **Hook ships in the plugin's `hooks/hooks.json`** (plugin root), command
  `python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/guardrails.py"`.
  Plugin hooks auto-register when the plugin is enabled, and the plugin is
  installed at user scope, so enforcement covers every repo by default — the
  user's explicit choice (Q1). Hooks fire for subagent tool calls too, so
  `/s:build` executors are covered. Matchers are unanchored regex, so
  `Edit|Write` also fires for `NotebookEdit`; the script exits 0 for any
  `tool_name` other than exactly `Edit` or `Write`.
- **Script lives with the engine**, not under `hooks/`: it is stdlib-only per
  the constitution, imports its sibling `spec_common` for config resolution,
  and is tested by the ordinary suite. Verified premise: `spec_common.
  resolve_config(start)` returns a `(merged-config, provenance)` tuple, merged
  dict first (run 2026-08-25 from the repo root; observed
  `tuple [{"dir": ".shipd", ...}, {...provenance...}]`). Rejected: a script
  under `hooks/` — outside the tests-per-engine-change convention.
- **Registry resolution**: start from the built-in rules in order; for each
  config rule, replace a built-in bearing the same `name` in place, else
  append; then drop every name listed in `disable`. The `guardrails` value
  itself resolves through the standard layered per-key merge — nearest layer
  wins the key wholesale, no deep merge (existing `layered-key-merge`
  behavior, kept deliberately).
- **Config start directory**: the hook resolves config from the input JSON's
  `cwd` field, falling back to the process cwd when absent.
- **Fail-open everywhere.** Unparseable stdin, a malformed `guardrails` value,
  an uncompilable rule regex, or any unexpected exception → exit 0, no deny.
  Deliberate divergence from `pr-mode`'s loud error: this hook runs on every
  Edit/Write in every repo, and an erroring hook would break all editing.
  Emergency bypass: env `SHIPD_GUARDRAILS=off`. Rejected: erroring on
  malformed config — unacceptable blast radius for a typo.
- **Three conservative built-in rules** (change-log comments, step-narration
  comments, placeholder/elision comments — exact patterns in the delta spec):
  low false-positive patterns, each individually disable-able. Comment markers
  covered by the defaults are `#` and `//`; other languages' markers are added
  per-repo via config rules.
- **Snapshot caveat**: the hook runs from the plugin cache snapshot, so it
  goes live only after the version bump lands and `claude plugin update
  s@shipd` runs (AGENTS.md).

Risk: a false positive denies a legitimate edit and the agent loops. Guarded
by the conservative default set, per-rule `disable`, the whole-hook `false`
switch, and the env bypass; the deny reason always names the rule so the user
can act on it.

## Questions and answers

### Q1: Does the guardrail hook enforce everywhere or only in opted-in repos?
- **Question:** The plugin is installed at user scope, so the hook fires in
  every repo the user works in. Enforce the built-in rules everywhere by
  default with layered config disable/override (a), or stay dormant unless a
  config layer declares `guardrails` (b)? Recommendation: (a).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Enforce everywhere by default (a). The complaint is about agent
  behavior generally, not one repo; any `.shipd-config.json` layer, including
  `~/.shipd-config.json`, can disable the hook or individual rules.
- **Queued:** none — no workspace was discoverable from this repo, so the
  oracle had no queue to file into.
