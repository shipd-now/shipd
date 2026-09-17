## ADDED Requirements

### Requirement: Customisation guide
id: customisation-guide

The repository SHALL ship a standalone guide at `docs/customise.md`
inventorying every customisation surface the plugin offers, so a reader finds
in one page what today is spread across the content directory's `README.md`,
`docs/guardrails.md`, and the copyable config example.

The guide SHALL cover, each in its own section:

- **The configuration file** — that `.shipd-config.json` is the only file the
  engine reads, that layers merge nearest-wins-wholesale, and that
  `shipd config` reports the resolved values with the layer that supplied each.
- **The recognized keys** — a table carrying one row per member of
  `spec_common.RECOGNIZED_CONFIG_KEYS`, each row naming what the key governs,
  with the `build` sub-block's members named in a single row.
- **The delivery steps** — that `autonomous-pipeline` is the key governing
  which steps a delivery runs, the stage registry in canonical order
  (`research`, `epic`, `plan`, `gate`, `build`, `review`), the five entry
  forms named, the three shipped presets (`default`, `eco`, `basic`), and the
  inspection route: `/s:status pipeline`, and `pipeline-show --expand <preset>`
  to start from a preset the key cannot merge with overrides.
- **The file-authored surfaces** — the optional `<content-dir>/constitution.md`
  that the planning and build flows treat as binding, the guardrail rule files
  and their three sources, the `post-worktree-scripts` registered through
  `shipd worktree hooks add`, and the wiki and personal memory pages the oracle
  reads.
- **The harness** — that the harness registry decides which agent surfaces
  receive the `/s:` commands, maintained through `shipd harness` and
  `shipd install`.
- **The environment overrides** — at least `SHIPD_GUARDRAILS`,
  `SHIPD_WORKTREE_IDLE_MINUTES`, and `SHIPD_WORKTREE_STALE_DAYS`, each named
  with the surface it overrides.
- **The limits** — what a repository cannot customise today: the `/s:` command
  bodies, which the harness generates from the plugin's own templates; the
  stage registry's membership and canonical order, which a declared pipeline
  selects from and inserts custom steps around but never extends or reorders;
  and the guardrail modes, which are the two built-ins.

The guide SHALL defer each surface's grammar to its existing authority rather
than restating it, linking the content directory's `README.md` for the
pipeline, PR mode, and `guardrails` key grammar, and `docs/guardrails.md` for
the rule file format. The guide SHALL conform to the shipd documentation
standard: `<!-- doc-type: reference -->` as its first line, and a total line
count within the reference cap.

`README.md`, `docs/cheatsheet.md`, and `docs/getting-started.md` SHALL each
carry a link to the guide, and `docs/getting-started.md` SHALL stay within its
own 150-line cap.

The engine's test suite SHALL guard the key table against drift by asserting
that every `RECOGNIZED_CONFIG_KEYS` member appears in `docs/customise.md`,
failing with the names of any absent keys.

#### Scenario: The guide answers how to change the delivery steps
- **WHEN** a reader opens `docs/customise.md` looking for how to change which
  steps a delivery runs
- **THEN** it names `autonomous-pipeline` as the key, lists the six registry
  stages in canonical order, names the three shipped presets, and gives the
  command that reports the effective pipeline

#### Scenario: Every recognized key is inventoried
- **WHEN** the config-key drift guard runs
- **THEN** every member of `RECOGNIZED_CONFIG_KEYS` is present in
  `docs/customise.md`

#### Scenario: A newly recognized key that the guide omits fails the suite
- **GIVEN** a key added to `RECOGNIZED_CONFIG_KEYS` and absent from
  `docs/customise.md`
- **WHEN** the config-key drift guard runs
- **THEN** it fails naming that key

#### Scenario: The guide states what is fixed
- **WHEN** a reader reaches the guide's limits section
- **THEN** it states that the harness generates the `/s:` command bodies from
  the plugin's templates, that a declared pipeline neither extends nor reorders
  the stage registry, and that a rule picks one of the two built-in guardrail
  modes

#### Scenario: The guide defers grammar rather than restating it
- **WHEN** a reader needs the full pipeline entry grammar or the rule file
  format
- **THEN** the guide links the content directory's `README.md` and
  `docs/guardrails.md` instead of carrying a second copy

#### Scenario: The guide carries its marker and fits its cap
- **WHEN** `python3 plugins/s/skills/document/scripts/docs_lint.py
  docs/customise.md` runs
- **THEN** it exits 0 with the file marked `reference` at 250 lines or fewer

#### Scenario: The entry surfaces point at the guide
- **WHEN** `README.md`, `docs/cheatsheet.md`, and `docs/getting-started.md` are
  inspected
- **THEN** each carries a link to the guide, and `docs/getting-started.md` is
  at most 150 lines
