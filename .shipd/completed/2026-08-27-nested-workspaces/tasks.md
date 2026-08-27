## 1. Engine chain resolution

- [x] 1.1 [req: workspace-root-discovery] In
      `plugins/s/skills/build/tests/test_spec_common.py`, add tests for a new
      `spec_common.workspace_chain(start)`: two nested declaring directories
      yield both roots nearest-first, a single declaring ancestor yields one,
      no declaring ancestor yields an empty list, and `find_workspace_root`
      returns the chain's first member (or `None`). Run them and observe them
      fail — `workspace_chain` does not exist yet.
- [x] 1.2 [req: workspace-root-discovery] In
      `plugins/s/skills/build/scripts/spec_common.py`, add `workspace_chain(start)`
      beside `find_workspace_root` (line 650): walk from `os.path.abspath(start)`
      parent-by-parent to the filesystem root collecting every directory whose
      own `.shipd-config.json` declares a `workspace` key, nearest first, and
      reimplement `find_workspace_root` to return the chain's first member or
      `None`. Confirm 1.1's tests pass.
- [x] 1.3 [req: workspace-chain-facilities] In
      `plugins/s/skills/build/tests/test_spec_common.py`, add tests for
      `resolve_wiki_stores(start)` (existing chain store dirs, nearest first,
      skipping members with no store), `resolve_initiative_brief(start, slug)`
      (nearest member holding the brief, else `None`), and `registry_root(start)`
      (nearest member whose `workspace` object declares `projects`, falling back
      to the chain's first member, `None` on an empty chain). Run them and
      observe them fail.
- [x] 1.4 [req: workspace-chain-facilities] In
      `plugins/s/skills/build/scripts/spec_common.py`, implement those three
      helpers on top of `workspace_chain`, each returning an empty list or
      `None` on an empty chain and never raising. Confirm 1.3's tests pass.
- [x] 1.5 [req: wiki-base-key] In
      `plugins/s/skills/build/tests/test_spec_common.py`, add a test that a
      `wiki_base` resolving to an enclosing chain member's store directory is
      treated as undeclared, alongside the existing self-referential case. Run
      it and observe it fail.
- [x] 1.6 [req: wiki-base-key] Widen the base carve-out so `wiki_base` counts as
      undeclared when it equals any chain store directory — in
      `plugins/s/skills/build/scripts/spec_common.py` (`wiki_base_dir`, line 908)
      and its consumer in `spec_status.py` (`cmd_wiki_show`, line 2445). Confirm
      1.5's test passes.

## 2. Nested workspace creation

- [x] 2.1 [req: workspace-initialization] In
      `plugins/s/skills/build/tests/test_spec_common.py`, add tests for
      `init_workspace(path, nested=True)`: it declares `workspace` beneath an
      enclosing workspace and returns both the created and enclosing roots,
      while it still refuses when the target's own config already declares
      `workspace`, and the bare call still refuses under an enclosing workspace.
      Run them and observe them fail.
- [x] 2.2 [req: workspace-initialization] In
      `plugins/s/skills/build/scripts/spec_common.py`, add a `nested=False`
      parameter to `init_workspace` (line 769): when set, skip the
      already-discoverable refusal unless the refusal names the target itself,
      and report the enclosing root. Confirm 2.1's tests pass.
- [x] 2.3 [req: workspace-init-verb] In
      `plugins/s/skills/build/tests/test_spec_status.py`, add tests that
      `workspace-init <path> --nested` exits zero under an enclosing workspace,
      printing the created root and the enclosing root, and that the bare verb
      still exits non-zero there. Run them and observe them fail.
- [x] 2.4 [req: workspace-init-verb] In
      `plugins/s/skills/build/scripts/spec_status.py`, add the `--nested` flag to
      the `workspace-init` subparser and pass it through to `init_workspace`.
      Confirm 2.3's tests pass.

## 3. Wiki reads across the chain, writes at the nearest

- [x] 3.1 [req: wiki-status-verbs, wiki-store-layout] In
      `plugins/s/skills/build/tests/test_spec_status.py`, add tests for
      chain-aware `cat wiki`: a page held only by the outer store prints from
      there, a page held by both prints the inner one, `cat wiki index` and
      `cat wiki queue` print every chain store's file nearest-first, and `cat
      wiki log` / `cat wiki schema` print the nearest store's file only. Run
      them and observe them fail.
- [x] 3.2 [req: wiki-status-verbs, wiki-store-layout] In
      `plugins/s/skills/build/scripts/spec_status.py`, make the `cat wiki` path
      (`cmd_cat`, line 1979, via `_wiki_store`, line 2021) resolve through
      `resolve_wiki_stores` for the workspace store, keeping `--personal`
      fixed-path, and pass the resolved file list to `_cat_files` so each file
      prints behind its own `--- <path>` separator. Confirm 3.1's tests pass.
- [x] 3.3 [req: wiki-status-verbs, wiki-base-key] In
      `plugins/s/skills/build/tests/test_spec_status.py`, add tests that
      `wiki-show` prints a `chain:` line naming the inherited store when one
      exists, `chain: none` when it does not, `chain: none` under `--personal`,
      and `base: none` when `wiki_base` points at a chain store; and that it
      exits zero reporting the nearest store absent when only an enclosing
      workspace holds one, exiting non-zero only when no chain member does. Run
      them and observe them fail — the verb currently exits non-zero with `no
      wiki store at …` whenever the nearest store is missing.
- [x] 3.4 [req: wiki-status-verbs, wiki-base-key] In
      `plugins/s/skills/build/scripts/spec_status.py`, add the `chain:` line to
      `cmd_wiki_show` (line 2445) directly above the existing `base:` line, and
      replace its unconditional `no wiki store at …` guard with one that raises
      only when no chain member holds a store, reporting the nearest store as
      absent otherwise. Confirm 3.3's tests pass.
- [x] 3.5 [req: wiki-status-verbs, wiki-store-layout] In
      `plugins/s/skills/build/tests/test_spec_status.py`, add a test that
      `wiki-queue-add` run from a repo under a nested workspace with no store of
      its own scaffolds that workspace's store, lands the block there, and
      leaves the enclosing store's `queue.md` byte-identical. Run it and observe
      it fail — the verb currently exits non-zero with `no wiki store at …`.
- [x] 3.6 [req: wiki-status-verbs, wiki-store-layout] In
      `plugins/s/skills/build/scripts/spec_status.py`, make `cmd_wiki_queue_add`
      (line 2536) and `wiki-queue-answer` scaffold the nearest workspace's store
      through the existing `wiki-init` seeding path when `queue.md` is absent,
      instead of raising, keeping every other guard unchanged. Confirm 3.5's
      test passes.

## 4. Registry and initiative inheritance

- [x] 4.1 [req: workspace-status-verbs] In
      `plugins/s/skills/build/tests/test_spec_status.py`, add a test that
      `workspace-show` run under a nested workspace declaring no `projects`
      lists the enclosing workspace's projects and names the enclosing root as
      the registry's provenance, and that a nested workspace declaring its own
      `projects` shows only its own with no provenance line. Run it and observe
      it fail.
- [x] 4.2 [req: workspace-status-verbs] In
      `plugins/s/skills/build/scripts/spec_status.py`, make `workspace-show` and
      `project-show` load the registry from `registry_root` and have
      `workspace-show` print the provenance line when that root differs from the
      workspace root. Confirm 4.1's test passes.
- [x] 4.3 [req: config-show-verb] In
      `plugins/s/skills/build/tests/test_spec_status.py`, add a test that
      `config-show` under nested workspaces prints the nearest root on its
      `workspace:` line plus a chain line listing both roots nearest-first, and
      prints no chain line for a single-member chain. Run it and observe it
      fail.
- [x] 4.4 [req: config-show-verb] In
      `plugins/s/skills/build/scripts/spec_status.py`, add the chain line to
      `cmd_config_show` (line 1777). Confirm 4.3's test passes.
- [x] 4.5 [req: initiative-reference-resolution] In
      `plugins/s/skills/build/tests/test_spec_lint.py`, add a test that an epic
      carrying `Initiative: <slug>` lints clean under a nested workspace when
      only the enclosing workspace holds the brief, and still errors when no
      chain member holds it. Run it and observe the first case fail.
- [x] 4.6 [req: initiative-reference-resolution] Route initiative-brief lookups
      through `resolve_initiative_brief`: `spec_lint.py` (lines 731, 1408),
      `dashboard.py` (line 947), and `spec_status.py`'s `cat initiative` (line
      1960). Leave `spec_emit.py`'s initiative write (line 142) on
      `find_workspace_root`. Confirm 4.5's test passes.
- [x] 4.7 [req: workspace-chain-facilities] In
      `plugins/s/skills/build/tests/test_spec_emit.py`, add regression tests that
      `spec_emit.py initiative` and `spec_emit.py wiki` run from a repo under a
      nested workspace install into the nearest workspace and never write into
      an enclosing one. Run them and confirm they pass against the unchanged
      emit code.

## 5. Oracle ladder and documentation

- [x] 5.1 [req: oracle-agent-contract, oracle-cited-answers] In
      `plugins/s/skills/build/tests/test_subagent_contract.py`, add tests
      asserting `plugins/s/agents/oracle.md` describes the chain rung (the
      `chain:` line, nearest-first store search, skipping members with no
      store), keeps the base rung after it, and documents the `Cited: [[slug]]
      (inherited <ws-root>)` marker. Run them and observe them fail.
- [x] 5.2 [req: oracle-agent-contract, oracle-cited-answers] Rewrite the job-wiki
      rung in `plugins/s/agents/oracle.md` (lines 59-91) as the workspace-chain
      rung — read `wiki-show`'s `chain:` line, search each listed store in order
      with the same engine reads and read-only grep, skip absent stores — keep
      the base rung as the following rung, restate that queue writes land in the
      nearest store only, and add the inherited citation marker to the citation
      rules (line 234 onward). Confirm 5.1's tests pass.
- [x] 5.3 [req: oracle-agent-contract] Update `docs/oracle.md`'s ladder
      description and diagram to carry the chain rung between the personal and
      base rungs.
- [x] 5.4 [req: workspace-chain-facilities] Update `docs/portable-workspaces.md`
      to document nesting: filing job workspaces beneath the base workspace root
      so inheritance is automatic, `workspace-init --nested`, which facilities
      inherit (wiki reads, initiative briefs, the project registry) and which do
      not (sync/member materialization, every write), and that `wiki_base` is now
      only needed for a base outside the chain.

## 6. Ship

- [x] 6.1 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.155` to `0.6.156`.
- [x] 6.2 [req: *] Run the full engine suite
      (`python3 -m pytest plugins/s/skills/build/tests/`) and confirm it passes
      with no third-party imports added.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 450 | 182.7k |
| Edit | 63 | 72.0k |
| (no tool) | 0 | 39.0k |
| Read | 125 | 37.5k |
| Agent | 25 | 22.2k |
| SendMessage | 8 | 6.1k |
| ToolSearch | 9 | 5.0k |
| AskUserQuestion | 1 | 2.3k |
| TaskStop | 1 | 61 |
| **Total** | 682 | 366.7k |
