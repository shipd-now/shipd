# init-research-dir
Status: verified

## Idea

Make `shipd init` also create the `research/` directory, and record the
init-created set in the documentation.

### Motivation

`<content-dir>/research/` is the reserved home of the cited research reports
`/s:research` installs and epics link, but `shipd init` scaffolds only
`verified/`/`planned/`/`completed/`, so a freshly initialized repo lacks the
research home until the first report install creates it lazily.

### Details

- Add `research` to the `init` verb's created set (`LAYOUT_DIRS` in
  `spec_status.py`), with the same check-then-create, never-clobber, and
  reporting semantics.
- Update the documentation that records what init creates: the
  `spec_status.py` module and handler docstrings, the plan skill's
  missing-layout guard wording, and a note in `.shipd/README.md`'s layout
  section naming the four init-created directories.
- Update the engine and CLI tests that enumerate the created set.

Affected capabilities: `spec-status` (modified), `shipd-plan` (modified).
Impact: `plugins/s/skills/build/scripts/spec_status.py`, its tests,
`plugins/s/skills/build/tests/test_shipd_cli.py`,
`plugins/s/skills/plan/SKILL.md`, `.shipd/README.md`, plugin version bump.

### Non-goals

- No other lazily-created directories join the init set — `epics/`, `video/`,
  and the rest still appear when their engines first install something.
- No change to the binary's dispatch, usage row, or the verb's flags — the
  four-directory set is the only behavioral change.
- No seeding of files inside `research/`.

## Implementation

- **One-line behavioral change:** `LAYOUT_DIRS` in
  `plugins/s/skills/build/scripts/spec_status.py` becomes
  `("verified", "planned", "completed", "research")` — `cmd_init` already
  iterates that tuple for probing, creation, and reporting, verified by the
  shipped v0.6.161 behavior (`shipd init` on a fresh root printed exactly one
  line per `LAYOUT_DIRS` member plus the summary, exit 0). Order appends
  `research` last so existing three-directory output ordering is preserved as
  a prefix. Rejected: a separate optional-set mechanism — nothing distinguishes
  research from the lifecycle three once it is part of the init contract.
- **Documentation record, four surfaces:** the `spec_status.py` module
  docstring's `init` entry and `cmd_init`/`LAYOUT_DIRS` comments name all
  four directories; `plugins/s/skills/plan/SKILL.md`'s missing-layout guard
  lists `research/` in the minimal layout; `.shipd/README.md` gains one
  sentence directly after the on-disk layout block stating that `shipd init`
  (and `spec_status.py init`) creates `verified/`, `planned/`, `completed/`,
  and `research/` and that every other directory appears lazily on first
  install. The binary's generic usage row ("create the content directory
  layout") stays as is.
- **Tests follow the enumeration:** `TestInitVerb` in
  `test_spec_status.py` (its class docstring, fresh-create, no-clobber,
  idempotent, and blocker cases) and
  `test_init_creates_the_layout_and_reports_ready` in `test_shipd_cli.py`
  assert the four-directory set; the non-clobber case additionally seeds a
  pre-existing `research/` report file and asserts it survives byte-identical.
- **Version bump** to `0.6.162` in `plugins/s/.claude-plugin/plugin.json`
  (version-keyed plugin cache).

Risk: a consumer parsing init output line-count would see four lines instead
of three — no such consumer exists in the tree (`shipd init` shipped in the
immediately preceding change and the plan skill reads only the exit code).
