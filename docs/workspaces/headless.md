# Headless consumers

[← Workspaces](../workspaces.md)

A workspace repo is readable by things that are not a Claude session — a CI
job, a chat bot, a cloud agent. The footprint is deliberately small:

- a **bare `git clone`** of the workspace repo — no members materialized, no
  sync run,
- **Python 3** — `spec_status.py` is stdlib-only, so nothing to install, and
- the plugin's **`plugins/s/skills/build/scripts/spec_status.py`**, run in
  place inside a plugin checkout — it imports its sibling modules from that
  directory, so copying the one file out on its own does not work.

That is the whole list — and it is why this page alone names the script
rather than the `shipd` binary every other page of the guide uses: a headless
consumer has nothing but a bare clone and a plugin checkout, with no binary on
its `PATH`, so `spec_status.py` run in place *is* the pinned contract.

Run the verbs from inside the clone, or point at it from anywhere with the
top-level `--root`:

```sh
git clone git@github.com:acme/ws-documents-linking.git /tmp/ws
python3 <plugin>/skills/build/scripts/spec_status.py --root /tmp/ws workspace-show
```

(`<plugin>` = `plugins/s` in a shipd checkout, or the installed plugin root.)

**Discovery needs nothing but the config file.** The engine finds the
workspace by walking upward for a `.shipd-config.json` that declares
`workspace` — it consults no git metadata and no `.shipd/` marker, so a
checkout with the git history stripped, or an unpacked tarball, resolves
exactly like a clone.

**Reads succeed with every member absent.** Nothing about reading a workspace
requires its member repos to exist:

- `workspace-show` exits 0 and reports the roster with each unmaterialized
  member marked `(absent) [url]`,
- `cat wiki <slug>`, `wiki-show`, and the initiative reads
  (`cat initiative <slug>`, `initiative-show`) all resolve from the tracked
  `.shipd/` content alone,
- `workspace-sync` only *prints* the materialization plan — it probes local
  disk and never touches the network, so it is safe to run in CI as an
  inspection.

**No machine-level configuration is needed.** A missing
`~/.shipd-config.json` changes nothing for a reader: `clone_sources` only
picks a cheaper rung during materialization, and `wiki_base` only adds a
fallback store after the workspace chain. Neither affects what a read verb
returns from the clone in front of it.

**Git matters only for writes.** A headless consumer that also *writes* — a
bot queueing a question with `wiki-queue-add`, say — still works without a
git binary or a configured identity: the write installs, the auto-commit is
skipped or fails soft to a single stderr warning, and the verb exits 0. Push
the result yourself if you want it shared; the engine will not.
