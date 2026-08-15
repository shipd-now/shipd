## 1. Port the remaining identity files

- [x] 1.1 [req: identity-settings] In `/Users/mikkelbergmann/projects/shipd`, run
      `python3 tools/port.py apply --source
      /Users/mikkelbergmann/projects/shipd --ref <sha> --dest . --include
      .claude/ --include .claude-plugin/` using the same shipd sha the library
      port used, and confirm it exits `0`.

## 2. Set the machine-read identity fields

- [x] 2.1 [req: identity-manifests] In
      `/Users/mikkelbergmann/projects/shipd/.claude-plugin/marketplace.json`, set
      the top-level `name` to `shipd`, the single plugin entry's `name` to `s`,
      and its `source` to `./plugins/s`; replace the bare `am` entry in its
      `keywords` array with `s`.
- [x] 2.2 [req: identity-manifests] Read the `version` value from
      `/Users/mikkelbergmann/projects/shipd/plugins/s/.claude-plugin/plugin.json`
      and record it.
- [x] 2.3 [req: identity-manifests] In
      `/Users/mikkelbergmann/projects/shipd/plugins/s/.claude-plugin/plugin.json`,
      set `name` to `s`, set `version` to the value from task 2.2 with its patch
      component incremented by one, and replace the bare `am` entry in `keywords`
      with `s`.
- [x] 2.4 [req: identity-manifests] Grep both manifest files for a name or
      keyword field whose value is exactly `am` and confirm there is none.

## 3. Settings

- [x] 3.1 [req: identity-settings] In
      `/Users/mikkelbergmann/projects/shipd/.claude/settings.json`, confirm
      `statusLine.command` invokes the statusline script under the `plugins/s/`
      path, set `enabledPlugins` to enable `s@shipd`, and set
      `extraKnownMarketplaces` to declare `shipd` as a `directory` source with
      path `.`. Remove any `s@shipd` or `shipd` entry.

## 4. Install and verify

- [x] 4.1 [req: identity-plugin-loads] Register the shipd repository as a
      marketplace and install the `s@shipd` plugin, then confirm a cache snapshot
      directory exists for the version set in task 2.3.
- [x] 4.2 [req: identity-plugin-loads] Start a fresh Claude Code session in
      `/Users/mikkelbergmann/projects/shipd` and confirm the plugin's skills are
      listed under the `/s:` namespace, with none from this marketplace listed
      under `/s:`.
- [x] 4.3 [req: identity-plugin-loads] In that session, invoke a `/s:` skill that
      shells out to the engine and confirm the script under
      `/Users/mikkelbergmann/projects/shipd/plugins/s/skills/build/scripts/` runs
      and returns its normal output.
- [x] 4.4 [req: *] Confirm `s@shipd` is still installed and its `/s:` skills
      still load, so the two plugins coexist.
- [x] 4.5 [req: *] Commit the identity changes in
      `/Users/mikkelbergmann/projects/shipd` on a branch, push, and open a PR.
