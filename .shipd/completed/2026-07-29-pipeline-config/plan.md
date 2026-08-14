# pipeline-config
Status: verified
Epic: autonomous-delivery

## Idea

The autonomous pipeline is designed to be configurable — skip, replace, or
extend stages per workspace or repo — but no schema, registry, or resolver
exists: the `autonomous-pipeline` config key is only prose in the epic. The
autopilot member cannot be built against an undefined contract, and users
cannot express things like "use Sourcebot for plan context" or "my CI does
the review gate".

This change delivers the contract:

- The `autonomous-pipeline` key: an ordered JSON list that *is* the
  pipeline, with four entry forms — built-in stage, explicit skip, stage
  with bound tools, replaced implementation — plus inserted `custom` steps
  positioned by list order.
- A stage registry (`research → epic → plan → gate → build → review`,
  canonical relative order) and `resolve_pipeline(root)` in `spec_common`,
  validating every entry and resolving through the existing layered config
  (nearest layer wins the whole key; no key → full default, both gates).
- A `pipeline-show` verb printing the effective pipeline with per-entry
  provenance, mirroring `config-show`.

### Non-goals

- No stage execution — running the resolved pipeline is `epic-autopilot`.
- No new merge semantics: the key rides layered nearest-wins-wholesale
  exactly as `dir` and `valid_themes` do.
- No MCP tool invocation or reachability probing — bindings and fallbacks
  are validated as data here; honoring them at run time is the autopilot's
  job.
- No config editing verbs; users author `.shipd-config.json` by hand or via
  their own tooling.

Affected capabilities: `shipd-config` (modified — three added requirements),
`spec-status` (modified — one added requirement). Impact:
`plugins/s/skills/build/scripts/spec_common.py`, `spec_status.py`, their
tests, `.shipd/README.md` and `README.md` config docs, plugin version bump.

## Implementation

- **Entry grammar (binding).** Each list entry is exactly one of:
  `{"stage": "<registry-name>"}`;
  `{"stage": "<name>", "skip": true}`;
  `{"stage": "<name>", "tools": [{"name": "<tool>", "fallback":
  "builtin"|"skip"}, ...]}`;
  `{"stage": "<name>", "replace": {"command"|"tool": "<impl>", "fallback":
  "builtin"|"skip"}}`;
  `{"custom": "<kebab-name>", "command": "<shell command>"}`.
  `tools` and `replace` may combine with neither `skip` nor each other.
  Rejected: `after`/`before` insertion syntax — the ordered list already
  encodes position.
- **Omission semantics.** A declared list is wholesale: stages absent from
  it do not run, and that omission is legitimate (the key's presence is the
  explicitness the epic demands); `"skip": true` is the visible-in-file
  variant. Absent key → the built-in default pipeline: all six stages, no
  skips, no bindings.
- **Validation in `resolve_pipeline(root)`** (spec_common, beside
  `resolve_config`): unknown `stage` name; built-in stages out of canonical
  relative order; `replace`/`tools` entries missing a `fallback` or naming
  one outside `builtin`/`skip`; `custom` without a kebab name or command;
  an entry matching no form. Errors name the offending entry by index and
  content; the function returns the ordered entries plus the provenance
  path (config file or `default`) for display.
- **Registry as data.** `PIPELINE_STAGES` tuple in `spec_common` — the
  single source the resolver, the verb, and later the autopilot import;
  no stage semantics beyond name and order live here (the artifact
  contract stays prose in the epic until the autopilot binds it in code).
- **`pipeline-show`** in `spec_status.py`: prints one line per effective
  entry (form, bindings, fallback) plus the supplying layer, `[default]`
  when no key is declared; exits non-zero listing every validation error.
  Requires no workspace and no change selection.

Risk: schema creep — future stage options landing as ad-hoc keys; guarded
by the closed entry grammar (an entry matching no form is an error, so new
options must arrive as spec'd grammar changes, never silently).
