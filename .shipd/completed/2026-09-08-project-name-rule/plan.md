# project-name-rule

Status: verified

## Idea

Relax the workspace registry's kebab-case constraint on project names to an
identifier-style rule so names like `APISchema` are valid, with a case-folded
duplicate check protecting case-insensitive filesystems.

### Motivation

The kebab-case requirement on project slugs was inherited wholesale from the
automikk port and forces cosmetic renames (`APISchema` → `api-schema`) that a
real workspace hit as a hard `workspace-sync` failure. Nothing mechanical
requires kebab here — every reference is an exact string match, and the only
filesystem use (`projects/<slug>/context.md`) is equally safe under an
identifier-style rule.

### Details

- Add a `PROJECT_NAME_RE` rule — ASCII letters and digits joined by single
  `-`, `_`, or `.` separators — and apply it where project names are
  validated: registry keys and `focus` in `validate_workspace`
  (`plugins/s/skills/build/scripts/spec_common.py`), and an initiative
  brief's `Project:` value (`plugins/s/skills/build/scripts/spec_lint.py`).
- Add a case-folded duplicate check across declared project names, so
  `APISchema` and `apischema` cannot coexist and collide as
  `projects/<name>/` directories on a case-insensitive filesystem.
- Update the `shipd-workspace` capability's three governing requirements,
  the initiative skill's prose, the engine tests, and the plugin version.

Affected capability: `shipd-workspace` (modified). Impact:
`plugins/s/skills/build/scripts/spec_common.py`,
`plugins/s/skills/build/scripts/spec_lint.py`,
`plugins/s/skills/build/tests/test_spec_common.py`,
`plugins/s/skills/build/tests/test_spec_lint.py`,
`plugins/s/skills/initiative/SKILL.md`,
`plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No relaxation of any other kebab id family: change ids, epic slugs and
  stub-table entries, initiative slugs, wiki page slugs, and queue slugs all
  stay kebab-case.
- No renaming or migration of existing registries — every kebab-case name is
  already valid under the relaxed rule.
- No case-insensitive reference resolution: `focus` and `Project:` values
  still match declared names exactly, case-sensitively.

## Implementation

- **One named rule, beside the family it departs from.** Add
  `PROJECT_NAME_RE = re.compile(r"^[A-Za-z0-9]+(?:[-_.][A-Za-z0-9]+)*$")`
  directly below `KEBAB_RE` in `spec_common.py` (currently line 63), with a
  comment noting it governs project names only. Rejected: reusing a loosened
  `KEBAB_RE` — every other id family must stay strictly kebab. Rejected: a
  fully loose "anything but whitespace and `/`" rule — project names become
  the `projects/<name>/context.md` directory component
  (`spec_common.py` `project_context_path`, shipd-workspace
  project-context-convention), so `..`, `\`, and exotic characters must stay
  impossible by construction.
- **`validate_workspace` changes** (`spec_common.py`): the registry-key check
  and the `focus` check switch from `KEBAB_RE` to `PROJECT_NAME_RE`, with
  error wording "project name '%s' is not a valid project name (ASCII
  letters and digits joined by '-', '_' or '.')" and the focus message
  updated the same way. A new pass reports an error naming both names when
  two declared project names are equal under `str.casefold()`. Docstring
  updated to match.
- **Initiative brief lint** (`spec_lint.py`, the metadata loop in
  `lint_initiative`): the `Project:` value check switches from
  `sc.KEBAB_RE` to `sc.PROJECT_NAME_RE`, aligning it with `lint_video`,
  which already applies no kebab gate to a video brief's `Project:` value
  and relies on the exact-match cross-check alone. The
  declared-name cross-check `_check_brief_project` is unchanged.
- **Observed current behavior (runnable premise):** running
  `validate_workspace({"projects": {"APISchema": {"repos": ["ai/APISchema"]}}})`
  today returns `["project slug 'APISchema' is not a kebab-case slug"]`, and
  `spec_status.py` `workspace-sync` wraps such findings as the hard failure
  "workspace registry is invalid". The new rule makes that same input
  validate clean.
- **Prose and version:** `plugins/s/skills/initiative/SKILL.md` stops calling
  the `Project:` value kebab-case; the plugin version bumps to `0.6.191` in
  the same change (cache-snapshot rule in AGENTS.md).
- Risk: an existing registry could already hold a name the new rule rejects —
  impossible in practice, since every previously-valid name was kebab and
  kebab names all match `PROJECT_NAME_RE`; validation only widens.

## Questions and answers

### Q1: How loose should the relaxed project-name rule be?
- **Question:** Replace the kebab-case constraint on workspace project names
  (registry keys, `focus`, brief `Project:` values) with which rule? Options:
  (a) identifier-style — ASCII alphanumerics joined by `-`, `_`, or `.`,
  plus a case-folded duplicate-name error; (b) fully loose — any non-empty
  name minus whitespace, `/`, `\`, `..`, and leading dots; (c) keep
  kebab-case and only improve the error message. Recommendation: (a),
  because project names surface as the `projects/<name>/context.md`
  directory component.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option (a) — identifier-style names with the case-folded
  duplicate check. `APISchema`, `api_schema`, and `API.Schema` become valid;
  spaces, path separators, and traversal sequences stay impossible by
  construction, and case-collisions on case-insensitive filesystems are
  refused explicitly.
- **Queued:** q-project-name-rule-looseness
