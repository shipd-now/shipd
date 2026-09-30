## 1. Side-track

- [x] 1.1 [req: onboard-workspaces-side-track] In
      `plugins/s/skills/onboard/SKILL.md`, add a "Workspaces side-track"
      section: the `workspaces`, `workspaces next`, `workspaces back`, and
      `workspaces reset` arguments; state file `~/.shipd/onboarding/workspaces.json`
      as `{"part": <1-5>}`; sandbox `~/.shipd/onboarding/workspaces-sandbox/`;
      reuse the sandbox on re-entry; `reset` deletes both after the user asks.
- [x] 1.2 [req: onboard-workspaces-side-track] In the same section, write the
      five part directives. Build with `spec_status.py workspace-init <base>
      --git`, `workspace-init <base>/<team> --nested --git`, `workspace-project
      add`, `wiki-init`, and `workspace-show`, run from the team directories,
      for base `acme-base` and teams `myapp`, `billing`, `infra`. Parts:
      1 manifest and chain; 2 nearest-wins reads and shadowing; 3 writes land
      nearest; 4 overlap on one shared repo that two teams both declare; 5 isolation plus
      pointers to `docs/workspaces.md`. Each part ends with navigation text.
- [x] 1.3 [req: onboard-step-navigation] In the argument-handling section, route
      the `workspaces` argument to the side-track without touching `state.json`,
      and add a sentence to step 9 naming `/s:onboard workspaces`.

## 2. Docs and version

- [x] 2.1 [req: onboard-workspaces-side-track] Update the `/s:onboard` rows in
      `README.md` and `docs/cheatsheet.md` to mention `workspaces`, and the
      onboard skill's frontmatter description and trigger phrases.
- [x] 2.2 [req: onboard-workspaces-side-track] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` from 0.6.241 to 0.6.242.

## 3. Verification

- [x] 3.1 [req: onboard-workspaces-side-track] Run the lesson's verb sequence in
      a scratch `HOME` and confirm each scenario's output; run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` and confirm
      it passes.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 32 | 13.9k |
| Edit | 7 | 5.0k |
| (no tool) | 0 | 3.3k |
| Agent | 2 | 596 |
| ScheduleWakeup | 1 | 181 |
| Read | 1 | 111 |
| **Total** | 43 | 23.1k |
