<!-- doc-type: how-to -->

# Headless consumers

[← Workspaces](../workspaces.md)

Read a workspace from something that is not a Claude session — a CI job, a
chat bot, a cloud agent. This page names the whole footprint and what a
headless read guarantees.

## The footprint

A headless consumer needs three things:

1. A bare `git clone` of the workspace repo. Materialize no members and run
   no sync.
2. Python 3. The engine script is stdlib-only, so install nothing.
3. The plugin's `plugins/s/skills/build/scripts/spec_status.py`, run in place
   inside a plugin checkout.

Run that script in place. It imports its sibling modules from that directory,
so a copy of the one file on its own does not work.

That list is why this page names the script rather than the `shipd` binary
that every other page of the guide uses. A headless consumer carries a bare
clone and a plugin checkout, with no binary on its `PATH`. The script run in
place *is* the contract.

## Run a read

Run the verbs from inside the clone, or point at the clone from anywhere with
the top-level `--root`:

```sh
git clone git@github.com:acme/ws-documents-linking.git /tmp/ws
python3 <plugin>/skills/build/scripts/spec_status.py --root /tmp/ws workspace-show
```

`<plugin>` is `plugins/s` in a shipd checkout, or the installed plugin root.

## What a headless read guarantees

**Discovery needs nothing but the config file.** The engine finds the
workspace by walking upward for a `.shipd-config.json` that declares
`workspace`. It consults no git metadata and no `.shipd/` marker, so a
stripped git history or an unpacked tarball resolves exactly like a clone.

**Reads succeed with every member absent.** Nothing about reading a workspace
needs its member repos to exist:

- `workspace-show` exits 0 and reports the roster, marking each unmaterialized
  member `(absent) [url]`.
- `cat wiki <slug>`, `wiki-show`, and the initiative reads
  (`cat initiative <slug>`, `initiative-show`) resolve from the tracked
  `.shipd/` content alone.
- `workspace-sync` only *prints* the materialization plan. It probes local
  disk and never touches the network, so CI can run it as an inspection.

**The machine needs no configuration.** A missing `~/.shipd-config.json`
changes nothing for a reader. `clone_sources` only picks a cheaper rung during
materialization, and `wiki_base` only adds a fallback store after the
workspace chain. Neither key affects what a read verb returns from the clone
in front of it.

**Git matters only for writes.** A headless consumer that also *writes* still
works without a git binary or a configured identity. Take a bot queueing a
question with `wiki-queue-add`. The write installs, the auto-commit skips or
fails soft to one stderr warning, and the verb exits 0. Push the result
yourself to share it; the engine never pushes.
