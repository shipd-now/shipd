## 1. Team-sharing section

- [x] 1.1 [req: portable-workspaces-doc] Append `## 8. Sharing a workspace
      with a team` to `docs/portable-workspaces.md`, covering: any number of
      engineers clone the same workspace repo and each runs the §4 load flow,
      so members are always machine-local and per-engineer (the manifest never
      records how a member landed); the wiki, queue, and initiatives are the
      shared surfaces and travel by ordinary `git pull`/`git push` of the
      workspace repo; the managed `.gitignore` members block is deterministic
      from the manifest, so identical manifests produce no block churn between
      clones.
- [x] 1.2 [req: portable-workspaces-doc] In the same §8, add a "Concurrency
      expectations" subsection stating: the engine takes no locks and never
      pushes, pulls, or fetches — every wiki write auto-commits locally,
      scoped to exactly the touched files; per-page `wiki/*.md` edits by
      different engineers merge cleanly, while concurrent `queue.md` appends
      (both land at EOF) and `index.md` catalog rewrites are the expected git
      conflict surfaces; a merge that ends up with two `## q-<slug>` blocks
      sharing a slug leaves the queue invalid — later queue writes fail until
      the duplicate is removed; recommend pulling before a session and pushing
      after it, as §3 already does for one engineer.
- [x] 1.3 [req: portable-workspaces-doc] In §3's Notes list
      (`docs/portable-workspaces.md`, after the wiki auto-commit note), add
      one line pointing readers sharing the repo across engineers at §8.

## 2. Headless-consumer section

- [x] 2.1 [req: portable-workspaces-doc] Append `## 9. Headless consumers` to
      `docs/portable-workspaces.md`, covering: a non-interactive reader (CI
      job, bot, cloud agent) needs only a bare `git clone` of the workspace
      repo, Python 3 (stdlib), and the plugin's
      `plugins/s/skills/build/scripts/spec_status.py`; run the verbs from inside the
      clone (discovery is an upward search for a `.shipd-config.json`
      declaring `workspace` — no git metadata, no `.shipd/` marker) or pass
      `--root`; `workspace-show` exits 0 with every member marked
      `(absent) [url]`, `cat wiki <slug>` and initiative reads work with no
      members materialized, and `workspace-sync` only prints a plan and never
      touches the network; no `~/.shipd-config.json` is needed for reads
      (`clone_sources`/`wiki_base` affect materialization and fallback only);
      git matters only to write auto-commits, which fail soft to a stderr
      warning with exit 0.

## 3. Consistency pass

- [x] 3.1 [req: portable-workspaces-doc] Re-read the extended
      `docs/portable-workspaces.md` end to end and reconcile wording so
      §1–§7's single-engineer phrasing (e.g. §3 "the wiki travels between
      machines") does not contradict §8/§9; keep §1–§7 section anchors
      unchanged.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 68 | 22.1k |
| Edit | 12 | 4.4k |
| Agent | 2 | 1.5k |
| ToolSearch | 1 | 933 |
| Read | 12 | 623 |
| SendMessage | 1 | 453 |
| (no tool) | 0 | 254 |
| **Total** | 96 | 30.2k |
