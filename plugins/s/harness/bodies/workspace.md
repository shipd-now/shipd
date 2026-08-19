<!-- description: Set up and inspect the shipd workspace — init, show, clone, or sync — through the engine's workspace verbs. -->
# /s:workspace — guided workspace setup and roster

A workspace is the grouping root above repositories: it declares a `workspace`
key in its `.shipd-config.json`, is found by nearest-ancestor search, and holds
the initiative briefs and the project registry. The engine owns that
declaration and the marked gitignore block — never hand-write either. Only this
command runs networked git; the engine verbs never touch the network.

<!-- include:preamble -->

Dispatch the invocation to exactly one verb: `init`, `show`,
`clone <url> [dest]`, or `sync`. Run from the workspace root so `--root` can be
omitted; `init` is the exception and takes an explicit target path.

## `show` — the roster, read-only

Run `shipd workspace`. It prints the workspace root, each declared project
(repos annotated present or absent) and each initiative with its status and
`Project:` scope; summarize it plainly. If it fails with the no-workspace
error, report that verbatim and point the user at `/s:workspace init`.

## `init` — guided creation

Run `shipd workspace` first. If it succeeds, a workspace already resolves:
report the root it prints, create nothing, and stop — nesting a second
workspace is a deliberate hand edit, not this command's job.

Otherwise ask two questions in one round: the **target root** (the repository's
parent directory, recommended, or the repository root itself, both as resolved
absolute paths) and **portable git seeding** (plain init, recommended, or
`--git`, which also runs `git init` there and ensures the marked member-repos
block in `.gitignore`).
<!-- if:question-dialogs -->
Put both questions in a single question dialog, recommended option first.
<!-- else -->
End the turn as plain text with both questions numbered, options lettered,
recommended first, and wait for a typed reply.
<!-- end -->
Drive the verb against the chosen path, `--git` only when seeding was chosen,
and report the root it prints:

```
python3 "$S/spec_status.py" workspace-init <chosen-path> [--git]
```

If it refuses — a workspace already discoverable, a missing directory — report
its error verbatim and stop; never retry against another path on your own. A
new workspace starts empty.

## `clone <url> [dest]` — bootstrap from a repository URL

No confirmation round; the invocation is the consent. Resolve the destination
(`[dest]`, else the URL's last path segment with any trailing `.git` stripped)
to an absolute path. **Refuse one topology only**: if the destination's
immediate parent itself declares a `workspace` key, report that cloning there
would nest a workspace and clone nothing — a job workspace inside an outer
workspace is legitimate, so never blanket-refuse nesting. Otherwise run
`git clone <url> [dest]`, reporting any git error verbatim and stopping, note
an enclosing workspace above the parent in one line, and run `sync` from inside
the created root.

## `sync` — materialize the members

No confirmation round either. Get the plan, one JSON record per line:

```
python3 "$S/spec_status.py" workspace-sync --json
```

Execute each `member` record by its `action`, running the record's `command:`
**exactly as printed** — the planner never executes. `none` touches nothing
(report any `drift:` note verbatim, never repair it); `worktree`,
`reference-clone`, and `clone` run their command; `unmaterializable` is
reported by its `reason:` and skipped. A failed command is reported against its
member and the run continues — partial materialization is a report, not an
abort.
<!-- if:file-references -->
Read `{refs}/workspace.md` for the record fields and the convergence rules.
<!-- else -->
This harness cannot open a companion reference file, so the plan's full record
grammar is unavailable here. Say so, act only on the `action`, `command`,
`drift`, and `reason` fields named above, and report any other field verbatim
instead of acting on it.
<!-- end -->
Then reconcile and confirm convergence:

```
python3 "$S/spec_status.py" workspace-sync --json --write-gitignore
```

Every member you executed should now be `action: none` with no `drift:` note;
report any that did not converge. Finish on the roster (`shipd workspace`),
then stop — point the user at `/s:initiative` to give the workspace its first
brief.
