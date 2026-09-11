<!-- doc-type: reference -->

# The member map and workspace discovery

[← Workspaces](../workspaces.md)

Two problems share one machine-local file. The **member map** tells a
workspace where a member repo already lives on this machine. The **pointer**
tells a checkout outside the workspace which workspace it belongs to.

## The machine-local file

The file is `.shipd-workspace.local.json` — plain JSON, no comments. It carries
three fields, two at a workspace root and one in a member checkout:

| field | lives at | states |
|---|---|---|
| `repos` | the workspace root | where each member repo sits on this machine |
| `clone_sources` | the workspace root | which directories the candidate scan probes |
| `workspace_root` | a member checkout's root | which workspace the checkout belongs to |

The file is machine-local and stays out of git, because it maps *this*
machine's checkouts. It therefore sits beside the tracked
`.shipd-config.json` manifest rather than inside it. The `workspace-map set`
and `workspace-sources add` verbs below add it to the workspace root's
`.gitignore` on first write.

## Mapping members to existing checkouts

The sync ladder materializes members under the workspace root. A second copy
of a checkout you already work in — say `~/projects/shipd` — silently diverges
from the first. Map that member instead.

`~/workspaces/myapp/.shipd-workspace.local.json`:

```json
{
  "repos": {
    "shipd": "~/projects/shipd",
    "api": "../checkouts/api"
  },
  "clone_sources": ["~/projects"]
}
```

- **Keys** are manifest member paths — the workspace-root-relative `path`
  values that the manifest's `projects[*].repos` entries declare.
- **Values** name where that member sits on this machine. The engine expands a
  leading `~`, resolves a relative value against the workspace root, and
  stores what you typed.

### The workspace-map verbs

The guided front door is **`/s:workspace map`**. It reads the sync plan and
proposes, for each unmapped member, the local checkout that the
`clone_sources` scan matched. It asks in a single round, then drives one `set`
per member you accept. It reports already-mapped members and never re-asks
them. `sync` and `clone` open one consent round of their own, which offers the
same reuse over the whole plan.

You never hand-author the file: the engine owns it. The read-only `shipd`
binary exposes no write verb, so these three forms invoke the engine script
directly:

```sh
# list every entry: stored value, then the absolute path it resolves to
python3 <plugin>/skills/build/scripts/spec_status.py workspace-map

# map a declared member to a checkout you already have
python3 <plugin>/skills/build/scripts/spec_status.py \
    workspace-map set shipd ~/projects/shipd

# unmap it again
python3 <plugin>/skills/build/scripts/spec_status.py workspace-map remove shipd
```

- **`set` validates the member path** — a path the manifest does not declare
  exits non-zero, names the declared paths, and writes nothing.
- **`set` stores the local path verbatim** — it resolves a `~` or a relative
  form on every read, so the file says what you typed.
- **`set` never repairs, and never refuses over the target** — a missing
  target, or one that is no git work tree, warns on stderr. The entry still
  lands, because pre-declaring a checkout you are about to move into place is
  legitimate.
- **`set` ensures the ignore line** — a successful write appends
  `.shipd-workspace.local.json` to the workspace root's `.gitignore`,
  idempotently, and creates that file when it is absent. The line sits outside
  the marked member-repos block, which `workspace sync --write-gitignore`
  rewrites to exactly the manifest's member paths.
- **Every other top-level key survives** — the verbs replace `repos` alone, so
  the pointer below can share the file.
- **`remove` deletes exactly its entry** — it exits non-zero when there is
  none, and it leaves the ignore line alone.
- **A malformed file fails both writers**, with the error the readers raise,
  naming the file. The verbs never repair a broken map.

### The clone-source list

The candidate scan unions two lists: the `clone_sources` key of the resolved
configuration ([getting started](getting-started.md)) and the same key in this
file, shown above. Configuration entries come first, and the engine drops
duplicates after it expands them. Record a directory here when it belongs to
this machine alone.

`/s:workspace sync` and `/s:workspace map` ask where your checkouts live when
neither list resolves, then record the answer through the engine's verbs:

```sh
# list, then start and stop probing a directory
python3 <plugin>/skills/build/scripts/spec_status.py workspace-sources
python3 <plugin>/skills/build/scripts/spec_status.py workspace-sources \
    add ~/projects
python3 <plugin>/skills/build/scripts/spec_status.py workspace-sources \
    remove ~/projects
```

- **`add` stores the path verbatim** and ensures the ignore line `set` does. A
  directory already stored under any spelling exits zero and writes nothing; a
  missing one warns on stderr, and the entry still lands.
- **`remove` deletes exactly one entry** — the stored value, or the directory
  it resolves to — and exits non-zero when nothing matches.

### What a mapped member means

A mapped member *is* that checkout for every workspace read. The report probes
it there, and board aggregation, `locate`, and epic discovery read its epics
and changes.

```sh
shipd workspace            # repo: shipd [mapped -> /Users/you/projects/shipd]
shipd workspace sync       # state: present   action: none
```

The planner treats a mapped member this way:

- **Its action is always `none`** — the materialization ladder never runs, and
  the planner emits no advisory command against a mapped path. Materializing
  into a directory you own outside the workspace is the one repair this engine
  must never attempt.
- **Origin drift still reports.** A mapped checkout whose `origin` differs
  from the manifest `url` plans `none`, with a drift note naming both URLs. An
  in-workspace member behaves the same way.
- **A missing target drifts rather than materializes** — the member records
  state `absent`, action `none`, and a drift note naming the path. Fix the
  checkout, or remove the map entry.
- **A stale key is a note, not an error.** The workspace report prints a
  `repos` key that matches no member path, and changes nothing.
- **A malformed map fails the verb reading it**, naming the file. Five shapes
  fail: invalid JSON, a non-object top level, and a non-object `repos` value.
  A mapping value that is not a non-empty string fails too, as does a
  `clone_sources` value that is not an array of non-empty strings.

## Resolving from outside the workspace

The member map solves the workspace's side: the workspace knows the checkout
is `~/projects/shipd`. This section solves the other side. A shipd verb run
*inside* `~/projects/shipd` must still reach the workspace's wiki, registry,
and initiatives rather than a repo-local fallback.

Discovery walks three rungs, and stops at the first rung that resolves:

1. **The ancestor search** — each directory up to `/` whose own
   `.shipd-config.json` declares `workspace`.
2. **The pointer** — a `workspace_root` in the checkout's own
   `.shipd-workspace.local.json`.
3. **The origin-URL scan** — the workspaces under `workspaces_root` that
   declare this checkout's `origin` as a member `url`.

A checkout materialized under the workspace root resolves on rung 1, exactly
as it always has. The rungs below it never run, and never cost a `git` probe.

### The pointer

Reach for the explicit rung when the scan is ambiguous, or when your
workspaces do not share one parent directory. The pointer reuses the
machine-local file of the section above — same filename, disjoint fields.

`~/projects/shipd/.shipd-workspace.local.json`:

```json
{
  "workspace_root": "~/workspaces/myapp"
}
```

The engine expands a leading `~` and resolves a relative value against the
file's own directory. At the repo root, the pointer governs the whole repo,
and discovery finds it from any subdirectory you run a verb in.

The pointer is decisive, and it reports when it is wrong. A target that does
not itself declare a `workspace` resolves *nothing*. Discovery then prints one
warning naming the pointer file and the target, rather than quietly falling
through to the scan. A deliberate declaration that is wrong is a thing to fix,
not a thing to work around.

### The origin-URL scan

Rung 3 runs with no pointer declared, and with `workspaces_root` (see
[getting started](getting-started.md)) naming a directory that exists. The
engine reads the checkout's `origin` with one local `git remote get-url`, then
matches it against the member `url`s of each workspace directly under that
parent. Nothing needs declaring anywhere: the manifest already carries every
member's clone URL.

The match compares URLs in a normalized form, so the manifest's spelling need
not match your remote's. Normalization strips the scheme and any `user@`
prefix, then reads a `host:path` colon as `host/path`. It drops one trailing
`.git` and any trailing slashes, then case-folds the result. All four of these
name one repository:

```
git@github.com:acme/repo.git
https://github.com/Acme/Repo
ssh://git@github.com/acme/repo/
github.com/acme/repo
```

Normalization does not resolve an **SSH host alias**. Take a remote of
`git@github-acme:acme/repo.git`, where `github-acme` is a `Host` entry in your
`~/.ssh/config`: its normalized host is `github-acme`. That host differs from
the `github.com` the manifest declares, so the scan will not match it. The
engine reads no SSH configuration, deliberately — a workspace manifest cannot
know a hostname that only your machine resolves. Use the pointer for those
checkouts.

Exactly one matching workspace resolves the chain from that workspace — the
*full* chain, so a base workspace enclosing the matched one stays a member.
Two or more matches resolve nothing and print one warning naming every match,
because a guess would write a job's knowledge into the wrong workspace:

```
warning: this checkout's origin is declared by 2 workspaces
(/Users/you/workspaces/myapp, /Users/you/workspaces/tasks-rollout);
declare `workspace_root` in /Users/you/projects/shipd/.shipd-workspace.local.json
to choose one
```

The remedy is rung 2: name the one you mean.

### What the rungs leave alone

- **A start that already resolves an ancestor changes nothing** — the lower
  rungs run only on an empty chain.
- **A bare checkout stays silent.** No pointer, no `workspaces_root`, no
  readable `origin`, or no match leaves the chain empty — no warning, no
  error. CI and headless consumers with no machine config never leave rung 1.
- **The rungs write nothing** — both of them only read. No verb creates the
  pointer file for you, and neither warning changes any verb's exit code.
- **The rungs never touch the network.** The scan's one `git` call reads a
  remote URL locally, under a short timeout. Any failure disables the rung.
