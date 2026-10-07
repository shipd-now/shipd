# review-manifest-coverage
Status: verified
Theme: reliability

## Idea

### Motivation

Lens 1 (v0.6.258) grouped packaging manifests into the contracts cohort by
matching an exact-basename set. benchy-cf reviewed the diff and found the
set silently omits every ecosystem that names its manifest after the
project rather than by convention:

- C#: `*.csproj`, `*.fsproj`, `Directory.Packages.props`,
  `Directory.Build.props`, `packages.config`, `packages.lock.json`
- Swift: `Package.swift`, `Package.resolved`
- Ruby: `*.gemspec` (`Gemfile` was covered)
- Elixir: `mix.exs`, `mix.lock`
- Dart: `pubspec.yaml`, `pubspec.lock`
- Python: `uv.lock`

This is not hypothetical coverage: the benchmark's 25-PR test set includes
three C# projects and one Swift project, so four of its PRs could not have
had a manifest recognised at all.

### Details

An exact-name set cannot express a manifest named after its project, so the
match grows two more shapes: a suffix list for project-named files, and the
`requirements*.txt` family whose split files declare as much as the plain
one. The three shapes move behind one `_is_manifest` helper rather than an
ever-longer lambda.

### Non-goals

- No change to the lens prose, its guidance, or the trigger. This is the
  classification side only — the lens itself shipped correct.
- No attempt to enumerate every packaging ecosystem. The list is
  benchy-cf's evidence plus same-family completions named in the
  Implementation section, not a survey.

## Implementation

`MANIFEST_BASENAMES` gains every exact name benchy-cf listed, plus these
same-family completions I added rather than taking from their evidence, each
a dependency or packaging declaration of a kind already in the set:
`go.work`/`go.work.sum` (Go workspaces beside `go.mod`), `Podfile` and its
lock (the other iOS manifest beside `Package.swift`), and `build.sbt`
(Scala, beside the Gradle and Maven entries). `*.vbproj` and `*.nuspec`
likewise join the suffix list beside the C# project files and the gemspec.

`MANIFEST_SUFFIXES` is new, holding the project-named shapes: `.csproj`,
`.fsproj`, `.vbproj`, `.gemspec`, `.nuspec`, `.cabal`.

`_is_manifest(base)` replaces the inline set membership in the `contracts`
rule and carries all three shapes, with a docstring naming why there are
three. The `requirements*` rule is a prefix-and-suffix pair rather than a
list, since the family is open-ended (`requirements-dev.txt`,
`requirements-test.txt`).

### The over-capture risk

A suffix list and a prefix rule are the kind of broad match that can pull in
files that are not manifests, which the exact-name set could not. So the
change pins the negative case as well as the positive: a new test asserts an
api route module, a frontend component, a test module and an unrelated
top-level file all stay out of `contracts`. Verified directly against
`COHORT_RULES` over 26 paths before the test was written — 22 manifest
shapes reaching `contracts`, four controls keeping their cohorts.

### Version

`plugins/s/.claude-plugin/plugin.json` bumps 0.6.258 → 0.6.259.

## Readiness attestation

### Problem and motivation

The manifest match is an exact-name set, so it omits every manifest named
after its project — including the C# and Swift shapes that four of the
benchmark's 25 PRs carry.

Evidence: `plugins/s/skills/review/scripts/semdiff.py`'s
`MANIFEST_BASENAMES` as shipped in v0.6.258 lists 22 exact names and the
`contracts` rule tests `base.lower() in MANIFEST_BASENAMES`; benchy-cf's
review of that diff names the six missing ecosystems and reports three C#
PRs and one Swift PR in the test set.

### Scope and non-goals

In scope: the basename additions, the new suffix list, the
`requirements*.txt` family, the `_is_manifest` helper, and tests for both
the positive and negative cases. Out of scope: the lens prose and trigger,
and any ecosystem beyond the evidence plus the named same-family
completions.

### Affected capabilities and files

One capability, one requirement.

Evidence: `semantic-review`/`cohort-grouping` (base `8b7c9cca6afc`). Files:
`plugins/s/skills/review/scripts/semdiff.py`,
`plugins/s/skills/review/tests/test_semdiff_files_context.py`,
`plugins/s/.claude-plugin/plugin.json`. Runnable premises: applied and
measured in this worktree — 239 review tests and 3172 build tests green —
and classification verified directly against `COHORT_RULES` over 22
manifest shapes and four non-manifest controls.

### No open task-shaping decision

- Suffix matching versus listing every project name: suffix, since the
  project name is by definition unknowable in advance — settled above.
- Whether `requirements-dev.txt` counts: yes, a split requirements file
  declares dependencies as much as the plain one.
- How far to extend beyond benchy-cf's list: to same-family completions
  only, each named in the Implementation section so the additions are
  reviewable rather than implicit.
- Whether a broad match needs a negative test: yes, and it is the main
  thing this change adds beyond coverage.
