# Meta-repo and manifest prior art for portable am workspaces

## Summary

Two mature families of prior art exist for "clone one thing, get a coordinated
multi-repo workspace": manifest-driven sync tools (Google `repo`, Zephyr
`west`) where a version-controlled manifest names every member repo, its URL,
path, and revision [1][2]; and thin meta-repos (the `meta` tool, the planning
repo pattern) where the workspace root itself is a git repo holding a manifest
plus shared content, with member clones gitignored [3][5]. The proposed am
portable workspace is squarely the second family, and that family's
conventions are consistent: the manifest is committed to the workspace repo,
child directories are auto-gitignored so children stay first-class independent
repos, and a single clone verb bootstraps the whole set [3].

The strongest design signals: every manifest schema separates the remote URL
from the checkout path and a revision, with layered defaults and override
mechanisms [1]; sync is an explicit idempotent verb (`repo sync`,
`west update`, `meta git clone`/`meta git update`) rather than implicit git
behavior [1][2][3]; and git submodules — the built-in alternative — are
consistently avoided for this use case because cloning does not initialize
them, UI tooling support is poor, and they impose a dual-commit workflow
[4]. The planning-repo pattern independently converges on co-locating
cross-repo knowledge (docs, architecture decisions, a workspace-level AI
context file) in the meta-repo precisely because "AI coding assistants work
best with context" spanning the whole portfolio — direct precedent for
shipping the LLM wiki inside the workspace repo [5].

## Manifest-driven tools: schema and sync semantics

Google `repo` keeps its manifest in its own git repository (a `default.xml` at
the top level), fetched automatically during `repo sync`, so the manifest is
versioned and distributed exactly like code [1]. The schema separates
`<remote>` (URL prefixes), `<default>` (fallback remote/revision/sync
parameters), and `<project>` entries carrying `name`, an optional checkout
`path`, a `revision`, and `groups` for subsetting; project URLs are composed
as `${remote_fetch}/${name}.git` [1]. Revision resolution is layered —
project revision → remote revision → default revision [1]. `<include>` lets
manifests compose, and `$TOP_DIR/.repo/local_manifests/*.xml` lets a user
extend or override the base manifest without modifying it (`extend-project` /
`remove-project`) [1].

Zephyr `west` structures a workspace as a manifest repository (containing
`west.yml` naming all projects and revisions), a `.west/` marker directory at
the top, and the project clones beside it [2]. `west update` maintains a
`manifest-rev` branch in every project pointing at the manifest-specified
revision as of the last update — a visible, local record of "what the
manifest pinned" [2]. West names its supported topologies: star with the
central framework as manifest repo (T1), star with the *application* as
manifest repo (T2), and a forest under a dedicated content-free manifest repo
(T3) [2] — T2 is the direct analogue of a job-focused workspace whose primary
project anchors the manifest. Notably, west's workspace *topdir* is not
itself a git repository, and making it one is explicitly "not an officially
supported topology" [2] — west's clonable unit is the manifest repo inside
the workspace, not the workspace root.

## The clonable-workspace-repo model

The `meta` tool implements exactly the root-as-repo model: a thin meta
repository holds a committed `.meta` JSON manifest referencing child
repositories, and `meta git clone <url>` clones the meta repo then
automatically clones every child listed in the manifest — single-command
bootstrap of the whole system [3]. Child project directories are
automatically added to the meta repo's `.gitignore`, keeping children
first-class, independently clonable repos rather than nested git objects [3].
The tool's stated philosophy is dissolving the monorepo/polyrepo dichotomy
("why choose many repos or a monolithic repo, when you can have both") [3],
and it loops commands across children (`meta git status`, `meta exec`,
subset targeting via `--include-only`) [3].

The planning-repo pattern applies the same shape to knowledge rather than
tooling: the meta-repo holds a workspace-level AI context file (`CLAUDE.md`
"describing the ecosystem"), `docs/` with architecture decisions and
cross-project planning, automation scripts, and a `.gitignore` listing every
nested repository — while "actual code remains in the nested repositories,"
each keeping "separate history, branches, remotes" [5]. Its stated motivation
matches the am wiki's: assistants should understand "not just the repo you're
in, but how it fits the bigger picture" [5].

## Why not git submodules

Submodules are the git-native way to pin child repos, but the prior art
consistently routes around them for workspace coordination: a plain
`git clone` does not fetch submodules (a manual
`git submodule update --init --recursive` is required), most UI tools support
them poorly, and day-to-day work demands committing in two places and keeping
them synchronized [4]. They remain appropriate where their pinning is the
point — independent branching, restricted per-component access [4] — but the
initialization friction is precisely what manifest tools' explicit clone/sync
verbs eliminate [3][4].

## Pinning vs floating revisions

`repo` treats the `revision` as a branch to track by default, with layered
defaults and an `upstream` attribute for revision-locked syncing; tags and
SHA-1 pins are possible but the docs caution they "have not been extensively
tested" [1]. `west` floats or pins per project via the manifest revision and
records the resolved pin in each project's `manifest-rev` branch on every
update [2]. The `meta` tool's manifest, by contrast, references repos without
a documented revision-pinning mechanism — children simply track their own
branches [3]. The pattern: build-reproducibility tools (repo, west) pin;
developer-coordination tools (meta, planning repo) float and let each child's
own git state govern [1][2][3][5].

## Lessons for a portable am workspace

- The root-as-repo model is proven by `meta` and the planning-repo pattern:
  commit the manifest (`.shipd-config.json` roster) and shared content, and
  auto-gitignore each member repo directory on registration [3][5].
- Add clone-source URLs to the registry and expose one explicit, idempotent
  bootstrap/sync verb, mirroring `meta git clone` / `west update` /
  `repo sync` [1][2][3].
- Keep member repos floating (developer-coordination semantics) rather than
  pinned; am workspaces coordinate live development, not reproducible builds
  [3][5]. If pinning is ever wanted for a "job snapshot," west's
  manifest-rev-style recorded pin is the precedent to copy [2].
- Co-locating the wiki, initiatives, and per-project context in the workspace
  repo has direct precedent and an identical stated motivation in the
  planning-repo pattern [5].
- West's separation of "workspace topdir" from "the repo you clone" is a
  viable alternative if root-as-repo causes friction, but it adds a level of
  indirection the meta model avoids [2][3].

## Gaps & caveats

- Real-world merge-conflict behavior for *shared markdown knowledge* in a
  meta-repo (multiple machines/agents editing the wiki concurrently) was not
  covered by any fetched source; the low-conflict claim rests on general git
  experience, not cited evidence.
- The `meta` tool's revision handling is under-documented; the absence of a
  pinning mechanism is inferred from its README and may be incomplete [3].
- Other manifest tools surfaced but not fetched (tsrc, vcstool, myrepos/mr,
  Gitslave) — the report's schema conclusions rest on repo and west; a
  broader survey could refine the manifest-field recommendations.
- West's documentation does not explain *why* a git-repo workspace topdir is
  unsupported, so the strength of that caution is unclear [2].
- No fetched source covers permissioning a shared workspace repo across a
  team (who may write the wiki), which will matter if workspaces outgrow
  single-user use.

## Sources

1. repo Manifest Format (official) — https://gerrit.googlesource.com/git-repo/+/master/docs/manifest-format.md
2. West Workspaces — Zephyr Project Documentation — https://docs.zephyrproject.org/latest/develop/west/workspaces.html
3. meta — tool for turning many repos into a meta repo (mateodelnorte) — https://github.com/mateodelnorte/meta
4. Managing Repositories With Git Submodules — Aviator — https://www.aviator.co/blog/managing-repositories-with-git-submodules/
5. The Planning Repo Pattern — Jason Poley — https://medium.com/@jbpoley/the-planning-repo-pattern-160ee57adcaf
