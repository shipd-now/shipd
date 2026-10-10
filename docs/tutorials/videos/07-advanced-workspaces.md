<!-- doc-type: how-to -->

# Episode 7: Member maps and headless runs

## Introduction

A workspace materializes its member repos on every machine, which can leave a second copy of a checkout you already use. A CI job or chat bot also needs to read the workspace without a Claude session. This episode shows the member map for the first problem and the headless read for the second. The episode is for engineers who already run a workspace.

## At a glance

| Item | Detail |
|---|---|
| Roadmap group | Verification and governance |
| Runtime | 5 minutes |
| Prerequisites | A workspace with at least one member repo, as in episode 6 |
| Commands shown | `/s:workspace map`, `workspace-map set`, `workspace-map remove`, `shipd workspace`, `workspace-show` |

## Script

### 0:00–1:00 The duplicate checkout problem

**On screen:** A workspace folder next to `~/projects/shipd`. The sync plan proposes a second clone of the same repo.

**Narration:** The sync ladder materializes members under the workspace root. A second copy of a checkout you already work in silently diverges from the first. Map that member instead. The map is a machine-local file, `.shipd-workspace.local.json`, and it stays out of git because it describes only this machine.

### 1:00–2:15 Map a member to an existing checkout

**On screen:** The presenter types `/s:workspace map`. The skill proposes the local checkout it matched for each unmapped member.

**Narration:** The guided front door is `/s:workspace map`. It proposes a checkout for each unmapped member and asks in a single round. Then it drives one `set` per member you accept. You never hand-author the file. The engine owns it.

### 2:15–3:15 What a mapped member means

**On screen:** The terminal runs `shipd workspace`. The line for `shipd` reads `mapped` and shows the absolute path.

**Narration:** A mapped member is that checkout for every workspace read. The sync action for it is always none, so the engine never materializes into a directory you own. A missing target shows as drift, not as a clone. To undo a mapping, run `workspace-map remove` with the member path.

### 3:15–4:15 Read a workspace headless

**On screen:** A CI log. A bare `git clone` of the workspace repo runs, then `spec_status.py --root /tmp/ws workspace-show`.

**Narration:** A headless consumer needs three things. It needs a bare clone of the workspace repo, Python 3, and the plugin's `spec_status.py` script run in place. It needs no `shipd` binary on its path. The read succeeds with every member absent, and `workspace-show` marks each missing member as absent.

### 4:15–5:00 Reads need no setup, writes need Git

**On screen:** The log shows `workspace-sync` printing its plan and exiting 0.

**Narration:** Discovery needs only the config file that declares the workspace. A missing machine config changes nothing for a reader. `workspace-sync` only prints its plan and never touches the network. Git matters only for writes, and the engine never pushes for you.

## Takeaways

- `.shipd-workspace.local.json` maps a member to a checkout you already have, and it stays out of git.
- A mapped member plans no action, so the engine never clones over your checkout.
- A headless read needs a bare clone, Python 3, and `spec_status.py`, with no members present.

## Next

Episode 8 moves from workspaces to the pipeline that checks every pull request: [CI and Copilot review](08-ci-and-copilot-review.md).

## Sources

- [The member map and workspace discovery](../../workspaces/member-map.md)
- [Headless consumers](../../workspaces/headless.md)
- [Sharing a workspace with a team](../../workspaces/teams.md)
